from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


def _money(v):
    """Coerce model-emitted money values: '$1,234.56', '1,234', 'Included', '' -> float|None."""
    if v is None or isinstance(v, (int, float)):
        return v
    if isinstance(v, str):
        t = v.replace("$", "").replace(",", "").replace("AUD", "").strip()
        if t in ("", "Included", "included", "TBC", "N/A", "-"):
            return None
        try:
            return float(t)
        except ValueError:
            return None
    return None


class _MoneyTolerant(BaseModel):
    @field_validator("*", mode="before")
    @classmethod
    def _coerce_money_fields(cls, v, info):
        f = cls.model_fields.get(info.field_name)
        if f is not None and str(f.annotation) in ("float | None", "typing.Optional[float]"):
            return _money(v)
        return v


class LineItem(_MoneyTolerant):
    description: str
    quantity: str | None = None
    unit_price: float | None = None
    total: float | None = None
    source_line: str = ""


class ExtractResult(_MoneyTolerant):
    competitor_brand: str = ""
    competitor_plan: str = ""
    competitor_total: float | None = None
    competitor_items: list[LineItem] = Field(default_factory=list)
    builder_plan: str = ""
    builder_total: float | None = None
    builder_items: list[LineItem] = Field(default_factory=list)
    competitor_design: dict = Field(default_factory=dict)
    builder_design: dict = Field(default_factory=dict)


class AmbiguityFlag(_MoneyTolerant):
    id: str
    item_name: str
    competitor_wording: str = ""
    builder_detail: str = ""
    builder_value: float | None = None
    competitor_value: float | None = None
    reason: str = ""
    suggested_clarification: str = ""
    confidence: Literal["LOW", "MEDIUM"] = "LOW"

    @field_validator("confidence", mode="before")
    @classmethod
    def _clamp_confidence(cls, v):
        v = str(v or "LOW").strip().upper()
        if v == "HIGH":
            return "MEDIUM"  # an ambiguity is never HIGH-confidence by definition
        return v if v in ("LOW", "MEDIUM") else "LOW"


class AmbiguityResolution(BaseModel):
    flag_id: str
    action: Literal["comparable", "discussion", "quantity"]
    quantity: int | None = None
    note: str = ""


class InclusionRow(BaseModel):
    category: str
    builder: str
    competitor: str
    advantage: Literal["builder", "competitor", "none"] = "none"


class ValuePoint(_MoneyTolerant):
    point: str
    value: float | None = None
    source_ref: str = ""


class ReconciliationRow(_MoneyTolerant):
    description: str
    competitor_add: float | None = None
    builder_add: float | None = None
    source_ref: str = ""


class QuoteReconciliation(_MoneyTolerant):
    rows: list[ReconciliationRow] = Field(default_factory=list)
    subtotal_competitor: float | None = None
    subtotal_builder: float | None = None
    current_price_competitor: float | None = None
    current_price_builder: float | None = None
    reconciled_competitor: float | None = None
    reconciled_builder: float | None = None


class SummaryHeader(BaseModel):
    builder_plan: str = ""
    builder_contract_ref: str = ""
    builder_range: str = ""
    builder_facade: str = ""
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


class ComparisonSummary(_MoneyTolerant):
    header: SummaryHeader
    headline_snapshot: str = ""
    design_differences: list[dict] = Field(default_factory=list)
    inclusion_differences: list[InclusionRow] = Field(default_factory=list)
    builder_value_advantage: list[ValuePoint] = Field(default_factory=list)
    competitor_advantage_gaps: list[ValuePoint] = Field(default_factory=list)
    quote_reconciliation: QuoteReconciliation = Field(default_factory=QuoteReconciliation)
    flagged_items: list[dict] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    conditionals: SummaryConditionals = Field(default_factory=SummaryConditionals)
    headline_advantage: float | None = None
