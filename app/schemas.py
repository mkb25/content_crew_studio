from __future__ import annotations

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=240)
    style: str = Field(..., min_length=2, max_length=180)
    audience: str = Field(default="general readers", max_length=140)
    length: str = Field(default="medium", pattern="^(short|medium|long)$")


class GenerateResponse(BaseModel):
    topic: str
    style: str
    audience: str
    model: str
    output: str

