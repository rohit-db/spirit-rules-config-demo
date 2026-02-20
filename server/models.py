from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from uuid import UUID


class RuleHeaderCreate(BaseModel):
    start_date: date
    end_date: date
    cost_category: str
    rate_category: Optional[str] = None
    category: Optional[str] = None
    account_group: Optional[str] = None
    groupby_costcenter: bool = False
    groupby_account: bool = False
    fixed_variable_pct_split: Optional[float] = None
    fixed_variable_type: Optional[str] = None


class RuleHeaderUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    cost_category: Optional[str] = None
    rate_category: Optional[str] = None
    category: Optional[str] = None
    account_group: Optional[str] = None
    groupby_costcenter: Optional[bool] = None
    groupby_account: Optional[bool] = None
    fixed_variable_pct_split: Optional[float] = None
    fixed_variable_type: Optional[str] = None


class RuleHeaderResponse(BaseModel):
    id: UUID
    start_date: date
    end_date: date
    cost_category: str
    rate_category: Optional[str]
    category: Optional[str]
    account_group: Optional[str]
    groupby_costcenter: bool
    groupby_account: bool
    fixed_variable_pct_split: Optional[float]
    fixed_variable_type: Optional[str]
    status: str
    version: int
    cloned_from_id: Optional[UUID]
    created_by: str
    created_at: datetime
    updated_at: datetime


class StatusUpdate(BaseModel):
    status: str  # "draft", "in_review", "approved", "archived"


class RuleLineCreate(BaseModel):
    account_number: str
    account_name: Optional[str] = None
    stat_type: str
    proration_rate: float
    effective_date: Optional[date] = None
    notes: Optional[str] = None
    sort_order: int = 0


class RuleLineUpdate(BaseModel):
    account_number: Optional[str] = None
    account_name: Optional[str] = None
    stat_type: Optional[str] = None
    proration_rate: Optional[float] = None
    effective_date: Optional[date] = None
    notes: Optional[str] = None
    sort_order: Optional[int] = None


class RuleLineResponse(BaseModel):
    id: UUID
    header_id: UUID
    account_number: str
    account_name: Optional[str]
    stat_type: str
    proration_rate: float
    effective_date: Optional[date]
    notes: Optional[str]
    sort_order: int
    created_at: datetime
    updated_at: datetime
