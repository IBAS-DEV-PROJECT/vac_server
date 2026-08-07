from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

DataT = TypeVar("DataT")


class CamelModel(BaseModel):
    """응답 필드를 camelCase로 직렬화하는 공통 스키마 기반 클래스."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class SuccessResponse(CamelModel, Generic[DataT]):
    success: bool = True
    data: DataT | None = None


class ErrorDetail(CamelModel):
    code: str
    message: str


class ErrorResponse(CamelModel):
    success: bool = False
    error: ErrorDetail


def success(data: DataT | None = None) -> dict:
    return {"success": True, "data": data}
