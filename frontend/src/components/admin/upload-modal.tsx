'use client';

import { useCallback, useRef, useState, type DragEvent } from 'react';
import { UploadCloud, File as FileIcon, X, CheckCircle2 } from 'lucide-react';

import { Modal } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import { cn, formatFileSize } from '@/lib/utils';

export interface UploadModalProps {
  open: boolean;
  onClose: () => void;
  /** 上传单个文件到指定知识库 */
  onUpload: (
    file: File,
    onProgress: (percent: number) => void
  ) => Promise<void>;
  /** 全部上传完成回调 */
  onUploaded?: () => void;
  /** 允许的文件类型 */
  accept?: string[];
  /** 最大文件大小（字节），默认 50MB */
  maxSize?: number;
}

interface UploadItem {
  file: File;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress: number;
  error?: string;
}

const DEFAULT_ACCEPT = ['.pdf', '.docx', '.txt'];

const ACCEPT_MIME: Record<string, string> = {
  pdf: 'application/pdf',
  docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  txt: 'text/plain',
};

/**
 * 文档上传弹窗。
 * 支持拖拽上传、多文件选择、上传进度展示与文件类型限制。
 */
export function UploadModal({
  open,
  onClose,
  onUpload,
  onUploaded,
  accept = DEFAULT_ACCEPT,
  maxSize = 50 * 1024 * 1024,
}: UploadModalProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [items, setItems] = useState<UploadItem[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);

  const validateFile = useCallback(
    (file: File): string | null => {
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!accept.map((a) => a.toLowerCase()).includes(ext)) {
        return `不支持的文件类型 ${ext}，仅支持 ${accept.join(' / ')}`;
      }
      if (file.size > maxSize) {
        return `文件大小超过 ${formatFileSize(maxSize)}`;
      }
      return null;
    },
    [accept, maxSize]
  );

  const addFiles = useCallback(
    (fileList: FileList | File[]) => {
      const next: UploadItem[] = [];
      Array.from(fileList).forEach((file) => {
        const error = validateFile(file);
        next.push({
          file,
          status: error ? 'error' : 'pending',
          progress: 0,
          error: error ?? undefined,
        });
      });
      setItems((prev) => [...prev, ...next]);
    },
    [validateFile]
  );

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files?.length) {
      addFiles(e.dataTransfer.files);
    }
  };

  const removeItem = (index: number) => {
    setItems((prev) => prev.filter((_, i) => i !== index));
  };

  const startUpload = async () => {
    const pending = items.filter((it) => it.status === 'pending');
    if (pending.length === 0) return;
    setUploading(true);

    for (const item of pending) {
      const index = items.indexOf(item);
      setItems((prev) =>
        prev.map((it, i) =>
          i === index ? { ...it, status: 'uploading', progress: 0 } : it
        )
      );
      try {
        await onUpload(item.file, (percent) => {
          setItems((prev) =>
            prev.map((it, i) =>
              i === index ? { ...it, progress: percent } : it
            )
          );
        });
        setItems((prev) =>
          prev.map((it, i) =>
            i === index
              ? { ...it, status: 'success', progress: 100 }
              : it
          )
        );
      } catch (err) {
        setItems((prev) =>
          prev.map((it, i) =>
            i === index
              ? {
                  ...it,
                  status: 'error',
                  error:
                    err instanceof Error ? err.message : '上传失败',
                }
              : it
          )
        );
      }
    }

    setUploading(false);
    onUploaded?.();
  };

  const handleClose = () => {
    if (uploading) return;
    setItems([]);
    onClose();
  };

  const hasUploading = items.some((it) => it.status === 'uploading');
  const acceptStr = accept.join(',');
  const acceptMime = accept
    .map((a) => ACCEPT_MIME[a.replace('.', '')])
    .filter(Boolean)
    .join(',');

  return (
    <Modal
      open={open}
      onClose={handleClose}
      title="上传文档"
      size="lg"
      footer={
        <>
          <Button variant="ghost" onClick={handleClose} disabled={uploading}>
            {items.some((it) => it.status === 'success') ? '关闭' : '取消'}
          </Button>
          <Button
            onClick={startUpload}
            loading={uploading}
            disabled={uploading || !items.some((it) => it.status === 'pending')}
            leftIcon={<UploadCloud className="h-4 w-4" />}
          >
            开始上传
          </Button>
        </>
      }
    >
      {/* 拖拽上传区 */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={cn(
          'flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed px-6 py-10 text-center transition-colors',
          dragOver
            ? 'border-primary-400 bg-primary-50'
            : 'border-gray-200 hover:border-primary-300 hover:bg-primary-50/40'
        )}
      >
        <span className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-primary-50 text-primary-600">
          <UploadCloud className="h-6 w-6" />
        </span>
        <p className="text-sm font-medium text-gray-700">
          点击或拖拽文件到此处上传
        </p>
        <p className="mt-1 text-xs text-gray-400">
          支持 {accept.join(' / ')}，单个文件最大 {formatFileSize(maxSize)}
        </p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={acceptMime || acceptStr}
          className="hidden"
          onChange={(e) => {
            if (e.target.files?.length) addFiles(e.target.files);
            e.target.value = '';
          }}
        />
      </div>

      {/* 文件列表 */}
      {items.length > 0 && (
        <ul className="mt-4 space-y-2">
          {items.map((item, index) => (
            <li
              key={`${item.file.name}-${index}`}
              className="flex items-center gap-3 rounded-md border border-gray-100 p-3"
            >
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-gray-100 text-gray-500">
                <FileIcon className="h-4 w-4" />
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <p className="truncate text-sm font-medium text-gray-900">
                    {item.file.name}
                  </p>
                  <span className="shrink-0 text-xs text-gray-400">
                    {formatFileSize(item.file.size)}
                  </span>
                </div>
                {item.status === 'uploading' && (
                  <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-gray-100">
                    <div
                      className="h-full rounded-full bg-primary-500 transition-all"
                      style={{ width: `${item.progress}%` }}
                    />
                  </div>
                )}
                {item.status === 'success' && (
                  <p className="mt-1 flex items-center gap-1 text-xs text-success-600">
                    <CheckCircle2 className="h-3 w-3" />
                    上传成功
                  </p>
                )}
                {item.status === 'error' && (
                  <p className="mt-1 text-xs text-error-600">
                    {item.error || '上传失败'}
                  </p>
                )}
              </div>
              {!hasUploading && (
                <button
                  type="button"
                  onClick={() => removeItem(index)}
                  className="shrink-0 rounded p-1 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600"
                  aria-label="移除"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </Modal>
  );
}

export default UploadModal;
