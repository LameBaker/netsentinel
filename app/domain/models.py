from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Node(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=128)
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(ge=1, le=65535)
    region: str = Field(min_length=2, max_length=32)
    enabled: bool = True


class RegisteredNode(Node):
    node_id: str = Field(min_length=1, max_length=64)


class ProbeResult(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    node_id: str = Field(min_length=1, max_length=128)
    status: Literal['up', 'down']
    latency_ms: float = Field(ge=0)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    error: str | None = Field(default=None, max_length=512)


class ProbeRunRequest(BaseModel):
    node_id: str | None = Field(default=None, min_length=1, max_length=64)


class ProbeRunResponse(BaseModel):
    results: list[ProbeResult]


class ProbeResultsSummary(BaseModel):
    total_checks: int = Field(ge=0)
    up_checks: int = Field(ge=0)
    down_checks: int = Field(ge=0)
    availability_pct: float = Field(ge=0, le=100)
    avg_latency_ms: float | None = Field(default=None, ge=0)
    last_checked_at: datetime | None = None
