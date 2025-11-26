from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class OperatorBase(BaseModel):
    """Base properties for an Operator."""
    name: str
    is_active: bool = True
    max_load: int = Field(ge=1)


class OperatorCreate(OperatorBase):
    """Schema for creating an Operator."""
    pass


class OperatorResponse(OperatorBase):
    """Schema for Operator response."""
    id: int
    model_config = ConfigDict(from_attributes=True)


class SourceCreate(BaseModel):
    """Schema for creating a Source."""
    name: str


class LinkConfig(BaseModel):
    """Schema for configuring operator weights for a source."""
    operator_id: int
    weight: int = Field(ge=1)


class SourceConfigUpdate(BaseModel):
    """Schema for updating source distribution rules."""
    operators: List[LinkConfig]


class SourceResponse(BaseModel):
    """Schema for Source response."""
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class LeadIdentify(BaseModel):
    """Input data to identify a lead."""
    identifier: str


class CaseCreate(BaseModel):
    """Input data to register a new case."""
    lead_identifier: str
    source_id: int
    message: Optional[str] = None


class CaseResponse(BaseModel):
    """Schema for Case response."""
    id: int
    lead_identifier: str
    source_id: int
    operator_id: Optional[int]
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)