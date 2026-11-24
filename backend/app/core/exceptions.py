"""自定义异常及全局异常处理。

定义业务中使用的异常类型，并通过 register_exception_handlers 注册到 FastAPI 应用。
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger


class BusinessException(Exception):
    """业务异常基类。

    Args:
        code: 业务错误码。
        message: 错误描述信息。
    """

    def __init__(self, code: int = 400, message: str = "业务异常") -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class AuthenticationError(BusinessException):
    """认证失败异常。"""

    def __init__(self, message: str = "认证失败，请重新登录") -> None:
        super().__init__(code=401, message=message)


class PermissionDeniedError(BusinessException):
    """权限不足异常。"""

    def __init__(self, message: str = "权限不足") -> None:
        super().__init__(code=403, message=message)


class ResourceNotFoundError(BusinessException):
    """资源未找到异常。"""

    def __init__(self, message: str = "资源不存在") -> None:
        super().__init__(code=404, message=message)


class FileProcessingError(BusinessException):
    """文件处理异常。"""

    def __init__(self, message: str = "文件处理失败") -> None:
        super().__init__(code=422, message=message)


def register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器到 FastAPI 应用。

    Args:
        app: FastAPI 应用实例。
    """

    @app.exception_handler(BusinessException)
    async def business_exception_handler(
        request: Request, exc: BusinessException
    ) -> JSONResponse:
        logger.warning(
            "业务异常 | path={} code={} message={}",
            request.url.path,
            exc.code,
            exc.message,
        )
        return JSONResponse(
            status_code=exc.code,
            content={"code": exc.code, "message": exc.message, "data": None},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception(
            "未处理异常 | path={} error={}", request.url.path, str(exc)
        )
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "message": "服务器内部错误",
                "data": None,
            },
        )
