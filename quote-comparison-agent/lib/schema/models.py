from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class LineItem(BaseModel):
    description: str
    quantity: str | None = None
    unit_price: float | None = None
    total: float | None = None
    source_line: str = ""


class ExtractResult(BaseModel):
    competitor_brand: str = ""
    competitor_plan: str = ""
    competitor_total: float | None = None
    competitor_items: list[LineItem] = Field(default_factory=list)
    henley_plan: str = ""
    henley_total: float | None = None
    henley_items: list[LineItem] = Field(default_factory=list)
    competitor_design: dict = Field(default_factory=dict)
    henley_design: dict = Field(default_factory=dict)


class AmbiguityFlag(BaseModel):
    id: str
    item_name: str
    competitor_wording: str
    henley_detail: str
    henley_value: float | None = None
    competitor_value: float | None = None
    reason: str
    suggested_clarification: str
    confidence: Literal["LOW", "MEDIUM"] = "LOW"


class AmbiguityResolution(BaseModel):
    flag_id: str
    action: Literal["comparable", "discussion", "quantity"]
    quantity: int | None = None
    note: str = ""


class InclusionRow(BaseModel):
    category: str
    henley: str
    competitor: str
    advantage: Literal["henley", "competitor", "none"] = "none"


class ValuePoint(BaseModel):
    point: str
    value: float | None = None
    source_ref: str = ""


class ReconciliationRow(BaseModel):
    description: str
    competitor_add: float | None = None
    henley_add: float | None = None
    source_ref: str = ""


class QuoteReconciliation(BaseModel):
    rows: list[ReconciliationRow] = Field(default_factory=list)
    subtotal_competitor: float | None = None
    subtotal_henley: float | None = None
    current_price_competitor: float | None = None
    current_price_henley: float | None = None
    reconciled_competitor: float | None = None
    reconciled_henley: float | None = None


class SummaryHeader(BaseModel):
    henley_plan: str = ""
    henley_contract_ref: str = ""
    henley_range: str = ""
    henley_facade: str = ""
    competitor_builder: str = ""
    competitor_plan: str = ""
    competitor_facade: str = ""
    region: str = ""
    sales_rep: str = ""
    run_date: str = ""


class SummaryConditionals(BaseModel):
    facade_comparison: str | None = None
    brand_comparison: list[dict] | None = None
    promotional_adjustments: list[str] | None = None
    energy_compliance_note: str | None = None
    site_costs_note: str | None = None


class ComparisonSummary(BaseModel):
    header: SummaryHeader
    headline_snapshot: str = ""
    design_differences: list[dict] = Field(default_factory=list)
    inclusion_differences: list[InclusionRow] = Field(default_factory=list)
    henley_value_advantage: list[ValuePoint] = Field(default_factory=list)
    competitor_advantage_gaps: list[ValuePoint] = Field(default_factory=list)
    quote_reconciliation: QuoteReconciliation = Field(default_factory=QuoteReconciliation)
    flagged_items: list[dict] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    conditionals: SummaryConditionals = Field(default_factory=SummaryConditionals)
    headline_advantage: float | None = None
