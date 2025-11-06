"""RFQ Section Builder

Helpers to build structured phase blocks with markdown tables and metrics.

Each phase block schema:
{
  "phase_id": str,
  "title": str,
  "markdown": str,          # Combined markdown (sub-blocks merged)
  "metrics": {
      "duration_ms": int,
      "prompt_tokens": int,
      "completion_tokens": int,
      "total_tokens": int,
      "estimated": bool
  },
  "created_at": iso8601 str,
  "sub_blocks": [
      {"id": str, "title": str, "markdown": str}
  ]
}

Pruning: keep most recent <= max_blocks (default 8).
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional, Sequence
from datetime import datetime


def build_markdown_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    """Build a GitHub-flavored markdown table with alignment markers.

    Adds leading/trailing pipes so ReactMarkdown renders cleanly.
    Infers alignment: numeric/currency/right-aligned, rank & score center.
    Returns empty string if no rows.
    """
    if not rows:
        return ""

    def _infer_alignment(h: str) -> str:
        hl = h.lower()
        # Center align certain headers
        if hl in {"rank", "score (0-5)", "score"}:
            return ":---:"
        # Right align numbers/currency/metrics
        if any(token in hl for token in ["price", "unit", "total", "lead", "days", "delivery", "quality", "amount"]):
            return "---:"
        return "---"  # left

    align_markers = [_infer_alignment(h) for h in headers]
    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join(align_markers) + " |"
    body_lines = []
    for r in rows:
        body_lines.append("| " + " | ".join(_format_cell(c) for c in r) + " |")
    return f"{header_line}\n{separator_line}\n" + "\n".join(body_lines) + "\n"


def _format_cell(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.2f}" if abs(value) >= 1e-2 else f"{value:.4f}"
    return str(value)


def build_phase_block(
    phase_id: str,
    title: str,
    markdown_sections: Sequence[Dict[str, str]],
    metrics: Dict[str, Any],
    sub_blocks: Optional[Sequence[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Build a phase block combining sections and optional sub-blocks.

    markdown_sections: list of {"title": str, "body": str}
    sub_blocks: list of {"id": str, "title": str, "markdown": str}
    """
    parts: List[str] = [f"## {title}"]
    for sec in markdown_sections:
        if sec.get("title"):
            parts.append(f"### {sec['title']}")
        parts.append(sec.get("body", ""))
    if sub_blocks:
        for sb in sub_blocks:
            parts.append(f"### {sb['title']}")
            parts.append(sb.get("markdown", ""))
    combined_markdown = "\n\n".join(p.strip() for p in parts if p and p.strip()) + "\n"
    return {
        "phase_id": phase_id,
        "title": title,
        "markdown": combined_markdown,
        "metrics": metrics,
        "created_at": datetime.utcnow().isoformat(),
        "sub_blocks": list(sub_blocks) if sub_blocks else [],
    }


def prune_phase_blocks(blocks: List[Dict[str, Any]], max_blocks: int = 8) -> List[Dict[str, Any]]:
    """Prune blocks list to last max_blocks elements preserving order."""
    if len(blocks) <= max_blocks:
        return blocks
    # Keep newest (assumes append order chronological)
    return blocks[-max_blocks:]


# Specific markdown builders -------------------------------------------------

def build_comparison_markdown(report: Any) -> List[Dict[str, str]]:
    """Build markdown sections from ComparisonReport model instance."""
    sections: List[Dict[str, str]] = []

    # Rankings table
    rankings_rows = []
    for v in report.top_ranked_vendors:
        rankings_rows.append([
            v.get("rank"),
            v.get("vendor_name"),
            v.get("score"),
            f"${v.get('total_price', 0):,.2f}",
            v.get("recommendation"),
        ])
    rankings_table = build_markdown_table(
        ["Rank", "Vendor", "Score (0-5)", "Total Price", "Status"], rankings_rows
    )
    sections.append({"title": "Vendor Rankings", "body": rankings_table})

    # Normalized quotes table
    nq_rows = []
    for q in report.normalized_quotes:
        nq_rows.append([
            q.vendor_name,
            f"${q.unit_price:.2f}",
            f"${q.total_price:,.2f}",
            q.lead_time_days,
            f"{q.overall_score:.1f}",
            f"{q.price_score:.1f}",
            f"{q.delivery_score:.1f}",
            f"{q.quality_score:.1f}",
        ])
    nq_table = build_markdown_table(
        ["Vendor", "Unit $", "Total $", "Lead Days", "Score", "Price", "Delivery", "Quality"], nq_rows
    )
    sections.append({"title": "Normalized Quotes", "body": nq_table})

    # Risk summary table
    rs_rows = []
    if report.risk_summary:
        for vendor_id, risks in report.risk_summary.items():
            vendor_name = _find_vendor_name(report, vendor_id)
            rs_rows.append([vendor_name, ", ".join(risks)])
    rs_table = build_markdown_table(["Vendor", "Risks"], rs_rows) if rs_rows else "No elevated risks detected.\n"
    sections.append({"title": "Risk Summary", "body": rs_table})

    # Recommendations narrative
    if getattr(report, "recommendations", None):
        sections.append({"title": "Recommendations", "body": report.recommendations})

    return sections


def _find_vendor_name(report: Any, vendor_id: str) -> str:
    for q in report.normalized_quotes:
        if q.vendor_id == vendor_id:
            return q.vendor_name
    return vendor_id


def build_negotiation_sub_blocks(recommendation: Any, quantity: int) -> List[Dict[str, str]]:
    blocks: List[Dict[str, str]] = []
    # Strategy
    if recommendation.negotiation_strategy:
        blocks.append({
            "id": "strategy",
            "title": "Strategy",
            "markdown": recommendation.negotiation_strategy.strip()
        })
    # Expected Outcome
    if recommendation.expected_outcome:
        blocks.append({
            "id": "expected_outcome",
            "title": "Expected Outcome",
            "markdown": recommendation.expected_outcome.strip()
        })
    # Pricing
    if recommendation.suggested_unit_price:
        total = recommendation.suggested_unit_price * quantity
        blocks.append({
            "id": "pricing",
            "title": "Pricing Recommendation",
            "markdown": f"Suggested Unit Price: ${recommendation.suggested_unit_price:.2f}\nTotal (@ {quantity:,} units): ${total:,.2f}"
        })
    # Leverage Points
    if recommendation.leverage_points:
        leverage_md = "\n".join(f"- {p}" for p in recommendation.leverage_points)
        blocks.append({"id": "leverage", "title": "Leverage Points", "markdown": leverage_md})
    # Fallback Options
    if recommendation.fallback_options:
        fallback_md = "\n".join(f"- {p}" for p in recommendation.fallback_options)
        blocks.append({"id": "fallbacks", "title": "Fallback Options", "markdown": fallback_md})
    return blocks


def build_purchase_order_markdown(po: Any) -> List[Dict[str, str]]:
    """Build structured markdown sections for a PurchaseOrder.

    Sections:
    - Summary (key details)
    - Line Item(s)
    - Commercial Terms
    - Delivery & Acceptance
    """
    sections: List[Dict[str, str]] = []

    # Summary key-value table
    summary_rows = [
        ["PO Number", po.po_number],
        ["PO Date", po.po_date.strftime("%Y-%m-%d")],
        ["Vendor", f"{po.vendor_name} (ID: {po.vendor_id})"],
        ["Vendor Contact", po.vendor_contact],
        ["Buyer", f"{po.buyer_name} <{po.buyer_email}>"],
        ["Product", f"{po.product_name} (ID: {po.product_id})"],
        ["Quantity", f"{po.quantity:,} {po.unit}"],
        ["Unit Price", f"${po.unit_price:,.2f}"],
        ["Total Amount", f"${po.total_amount:,.2f}"],
    ]
    sections.append({
        "title": "Summary",
        "body": build_markdown_table(["Field", "Value"], summary_rows)
    })

    # Line items (for now single consolidated item)
    line_rows = [[
        1,
        po.product_id,
        po.product_name,
        f"{po.quantity:,}",
        po.unit,
        f"${po.unit_price:,.2f}",
        f"${po.total_amount:,.2f}",
        po.delivery_date.strftime("%Y-%m-%d"),
    ]]
    sections.append({
        "title": "Line Items",
        "body": build_markdown_table([
            "Item", "Product ID", "Description", "Qty", "Unit", "Unit $", "Line Total", "Planned Delivery"
        ], line_rows)
    })

    # Commercial terms
    commercial_rows = [
        ["Payment Terms", po.payment_terms],
        ["Currency", "USD"],
        ["Pricing Basis", "Firm Fixed"],
        ["Invoicing", "Upon delivery"],
    ]
    sections.append({
        "title": "Commercial Terms",
        "body": build_markdown_table(["Term", "Detail"], commercial_rows)
    })

    # Delivery & acceptance
    delivery_rows = [
        ["Requested Delivery Date", po.delivery_date.strftime("%Y-%m-%d")],
        ["Delivery Location", "TBD - Default Warehouse"],
        ["Packaging", "Standard commercial packaging"],
        ["Acceptance Criteria", "No visible defects; meets specification; quantity correct"],
    ]
    sections.append({
        "title": "Delivery & Acceptance",
        "body": build_markdown_table(["Aspect", "Detail"], delivery_rows)
    })

    return sections
