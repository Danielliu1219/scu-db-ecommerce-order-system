from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

T = TypeVar("T")


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)


class NonemptyPatch(Input):
    @model_validator(mode="after")
    def nonempty(self):
        if not self.model_fields_set or any(
            getattr(self, key) is None for key in self.model_fields_set
        ):
            raise ValueError("Provide at least one non-null field")
        return self


class Response(BaseModel, Generic[T]):
    data: T


class Page(BaseModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total: int


class Pagination(Input):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class Changed(BaseModel):
    changed: bool


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | list[dict[str, str]] | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody
