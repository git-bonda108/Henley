"""Rich demo fixtures — canonical downlights ambiguity case."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from lib.schema.models import (
    AmbiguityFlag,
    ComparisonSummary,
    ExtractResult,
    InclusionRow,
    LineItem,
    QuoteReconciliation,
    ReconciliationRow,
    SummaryConditionals,
    SummaryHeader,
    ValuePoint,
)


def demo_extract(wizard: dict) -> ExtractResult:
    return ExtractResult(
        competitor_brand=wizard.get("competitor_brand") or "Carlisle Homes",
        competitor_plan="Brighton 28",
        competitor_total=412_890.0,
        competitor_items=[
            LineItem(description="Base house Brighton 28", total=389_500.0, source_line="L.12"),
            LineItem(description="Downlights included", quantity=None, total=0.0, source_line="L.27"),
            LineItem(description="Stone benchtop — kitchen", total=4_200.0, source_line="L.31"),
            LineItem(description="Driveway — standard", quantity=None, total=0.0, source_line="L.44"),
        ],
        builder_plan="Allegra 355-D38",
        builder_total=438_544.0,
        builder_items=[
            LineItem(description="Allegra 355-D38 base", total=401_200.0, source_line="L.8"),
            LineItem(description="Electrical pack — 37 downlights + 2 two-way switches", total=1_606.0, source_line="L.19"),
            LineItem(description="Stone benchtop — 40mm Caesarstone", total=5_890.0, source_line="L.22"),
            LineItem(description="Concrete driveway 32m²", total=8_400.0, source_line="L.35"),
        ],
        competitor_design={"bedrooms": 4, "bathrooms": 2, "storeys": 2, "size_sqm": 241},
        builder_design={"bedrooms": 4, "bathrooms": 2, "storeys": 2, "size_sqm": 355},
    )


def demo_ambiguities() -> list[AmbiguityFlag]:
    return [
        AmbiguityFlag(
            id=str(uuid.uuid4()),
            item_name="Internal Electrical Pack — Downlights",
            competitor_wording='"Downlights included"',
            builder_detail="14× downlights + 2× two-way switches (base). Full pack: 49+ downlights",
            builder_value=1606.0,
            competitor_value=0.0,
            reason="Direct comparison of $0 vs $1,606 would overstate Builder's cost if the competitor includes only ~5 downlights.",
            suggested_clarification="Confirm competitor downlight quantity with customer or sales file.",
            confidence="LOW",
        ),
        AmbiguityFlag(
            id=str(uuid.uuid4()),
            item_name="Driveway",
            competitor_wording='"Driveway — standard"',
            builder_detail="Concrete driveway 32m² — $8,400",
            builder_value=8400.0,
            competitor_value=0.0,
            reason="Competitor scope and area not specified.",
            suggested_clarification="Confirm driveway material and area on competitor quote.",
            confidence="MEDIUM",
        ),
    ]


def demo_summary(wizard: dict, resolved: list) -> ComparisonSummary:
    now = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")
    return ComparisonSummary(
        header=SummaryHeader(
            builder_plan="Allegra 355-D38",
            builder_contract_ref=wizard.get("customer_ref") or "—",
            builder_range="Allegra",
            builder_facade="Hamptons",
            competitor_builder=wizard.get("competitor_brand") or "Carlisle Homes",
            competitor_plan="Brighton 28",
            competitor_facade="Contemporary",
            region=wizard.get("region") or "VIC",
            sales_rep=wizard.get("sales_rep") or "—",
            run_date=now,
        ),
        headline_snapshot=(
            "Our Allegra 355-D38 includes a confirmed electrical pack valued at $1,606 and a 32m² concrete driveway at $8,400. "
            "The competitor quote lists downlights and driveway as included without quantity or scope — these were flagged for human review. "
            "Where confirmed, our inclusions provide measurable value in electrical, benchtop, and site works."
        ),
        design_differences=[
            {"point": "Builder footprint 355m² vs competitor 241m² — not directly comparable without normalisation.", "costImpact": None, "source": "Design URLs"},
            {"point": "Builder Hamptons façade vs competitor Contemporary — aesthetic difference only.", "costImpact": None, "source": "Design URLs"},
        ],
        inclusion_differences=[
            InclusionRow(category="Stone benchtop (kitchen)", builder="Yes — 40mm Caesarstone", competitor="Yes — unspecified thickness", advantage="builder"),
            InclusionRow(category="Downlights (quantity confirmed)", builder="Yes — 37 + pack option", competitor="TBC — quantity unresolved", advantage="builder"),
            InclusionRow(category="Concrete driveway (area confirmed)", builder="Yes — 32m²", competitor="TBC — scope unresolved", advantage="builder"),
            InclusionRow(category="7-star energy compliance", builder="Yes", competitor="Unconfirmed — requires manual validation", advantage="none"),
        ],
        builder_value_advantage=[
            ValuePoint(point="Electrical pack — 37 downlights + switches", value=1606.0, source_ref="Builder L.19"),
            ValuePoint(point="Caesarstone 40mm benchtop upgrade", value=1690.0, source_ref="Builder L.22 vs Carlisle L.31"),
        ],
        competitor_advantage_gaps=[
            ValuePoint(point="Smaller footprint may suit customer budget if size acceptable", value=None, source_ref="Design URLs"),
        ],
        quote_reconciliation=QuoteReconciliation(
            rows=[
                ReconciliationRow(description="Base house", competitor_add=None, builder_add=None, source_ref="Quotes"),
                ReconciliationRow(description="Electrical — downlights (confirmed Builder only)", builder_add=1606.0, source_ref="Builder L.19"),
                ReconciliationRow(description="Driveway (Builder confirmed)", builder_add=8400.0, source_ref="Builder L.35"),
            ],
            subtotal_competitor=412_890.0,
            subtotal_builder=438_544.0,
            current_price_competitor=412_890.0,
            current_price_builder=438_544.0,
            reconciled_competitor=None,
            reconciled_builder=None,
        ),
        flagged_items=[
            {
                "itemName": "Downlights",
                "competitorStatement": '"Downlights included" — quantity NOT SPECIFIED',
                "builderDetail": "37 downlights + switches — $1,606",
                "confidence": "LOW",
                "reason": "Cannot compare $0 vs $1,606 without competitor quantity.",
                "suggestedClarification": "Ask customer for competitor electrical schedule.",
            }
        ],
        open_questions=[
            "What quantity of downlights does the Carlisle quote actually include?",
            "Is the competitor driveway concrete, asphalt, or cross-over only?",
            "Does the customer require 355m² or would a smaller Builder plan be appropriate?",
        ],
        conditionals=SummaryConditionals(
            promotional_adjustments=["Sumitomo discount"] if "Sumitomo discount" in wizard.get("promotions", []) else None,
            energy_compliance_note="Builder includes 7-star compliance as standard on Allegra range — confirm competitor baseline.",
        ),
        headline_advantage=25_654.0,
    )
