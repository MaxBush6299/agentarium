"""
Phase 4: Comparison & Analysis Agent

Merges results from parallel evaluation tracks and creates comprehensive
vendor comparison reports with risk assessment and vendor recommendations.
"""

import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.agents.base import DemoBaseAgent
from src.agents.workflows.rfq.models import (
    VendorProfile,
    QuoteResponse,
    NormalizedQuote,
    ComparisonReport,
)
from src.agents.workflows.rfq.observability import rfq_logger


class ComparisonAndAnalysisAgent(DemoBaseAgent):
    """
    Merges evaluation track results and creates vendor comparison.
    
    Input: List of evaluated vendors with Track 1, 2, 3 scores + quotes
    Output: ComparisonReport with ranked vendors and analysis
    
    Scoring: Equal weighting (33% each track) produces merged score 0-100
    """
    
    def __init__(self):
        """Initialize comparison agent.

        Updated instructions encourage structured markdown output (summary + tables):
        - Provide a concise 2-3 sentence summary of vendor landscape
        - Output tables: Vendor Rankings, Normalized Quotes, Risk Summary
        - Finish with a clear recommendation line (Top Vendor, rationale)
        These instructions are advisory; current implementation builds tables procedurally.
        """
        instructions = (
            "You are a vendor comparison analyst. Produce a concise summary and structured tables. "
            "Follow this format:\n\n"
            "Summary:\n<2-3 sentences describing vendor strengths and differentiation>\n\n"
            "Vendor Rankings Table (Rank | Vendor | Score (0-5) | Total Price | Status)\n"
            "Normalized Quotes Table (Vendor | Unit $ | Total $ | Lead Days | Score | Price | Delivery | Quality)\n"
            "Risk Summary Table (Vendor | Risks) or 'No elevated risks detected.'\n\n"
            "Recommendation: <Top Vendor> - <Reason>."
        )
        super().__init__(
            name="Comparison & Analysis Agent",
            model="gpt-4o",
            tools=[],
            instructions=instructions,
        )
    
    async def merge_evaluation_tracks(
        self,
        vendors: List[VendorProfile],
        compliance_evaluations: Dict[str, Dict[str, Any]],  # vendor_id -> {confidence, risk_level, ...}
        delivery_evaluations: Dict[str, Dict[str, Any]],
        financial_evaluations: Dict[str, Dict[str, Any]],
        workflow_id: Optional[str] = None,
    ) -> Dict[str, float]:
        """
        Merge three evaluation tracks with equal weighting.
        
        Returns: Dict mapping vendor_id to merged_score (0-100)
        """
        merged_scores: Dict[str, float] = {}
        
        for vendor in vendors:
            vendor_id = vendor.vendor_id
            
            # Get confidence scores from each track (0-1), convert to 0-100
            comp_conf = compliance_evaluations.get(vendor_id, {}).get("confidence", 0.5)
            deliv_conf = delivery_evaluations.get(vendor_id, {}).get("confidence", 0.5)
            fin_conf = financial_evaluations.get(vendor_id, {}).get("confidence", 0.5)
            
            comp_score = comp_conf * 100
            deliv_score = deliv_conf * 100
            fin_score = fin_conf * 100
            
            # Merge with equal weighting (33% each)
            merged_score = (comp_score + deliv_score + fin_score) / 3.0
            merged_scores[vendor_id] = merged_score
            
            rfq_logger.info(
                f"Score merge for {vendor.vendor_name}: Comp={comp_score:.1f} + "
                f"Deliv={deliv_score:.1f} + Fin={fin_score:.1f} = Merged={merged_score:.1f}",
                workflow_id=workflow_id,
            )
        
        return merged_scores
    
    def _build_risk_summary(
        self,
        merged_scores: Dict[str, float],
        compliance_evals: Dict[str, Dict[str, Any]],
    ) -> Dict[str, List[str]]:
        """Build risk summary organized by vendor."""
        risk_summary: Dict[str, List[str]] = {}
        
        for vendor_id, score in merged_scores.items():
            risks: List[str] = []
            
            comp_risk = compliance_evals.get(vendor_id, {}).get("risk_level", "MEDIUM")
            if comp_risk in ["HIGH", "CRITICAL"]:
                risks.append(f"Compliance {comp_risk}")
            
            if score < 50:  # Low overall score (0-100 scale)
                risks.append("Low overall score")
            
            if risks:
                risk_summary[vendor_id] = risks
        
        return risk_summary
    
    def _create_normalized_quotes(
        self,
        vendors: List[VendorProfile],
        quotes: List[QuoteResponse],
        merged_scores: Dict[str, float],
    ) -> List[NormalizedQuote]:
        """Create normalized quotes for comparison."""
        normalized: List[NormalizedQuote] = []
        
        for vendor in vendors:
            quote = next((q for q in quotes if q.vendor_id == vendor.vendor_id), None)
            if not quote:
                continue
            
            # Calculate lead days from delivery_date (which is a datetime object)
            today = datetime.now()
            lead_days = (quote.delivery_date - today).days if quote.delivery_date else 0
            
            merged_score = merged_scores.get(vendor.vendor_id, 0)
            
            norm_quote = NormalizedQuote(
                quote_id=quote.quote_id or f"quote-{vendor.vendor_id}",
                vendor_id=vendor.vendor_id,
                vendor_name=vendor.vendor_name,
                unit_price=quote.unit_price,
                total_price=quote.total_price,
                price_per_unit_with_bulk=quote.unit_price * 0.95,  # Assume 5% bulk discount available
                delivery_date=quote.delivery_date,
                lead_time_days=lead_days,
                overall_score=merged_score,
                price_score=merged_score * 0.33,  # Proportional to merged
                delivery_score=merged_score * 0.33,
                quality_score=merged_score * 0.34,
                risk_flags=[],
            )
            normalized.append(norm_quote)
        
        return normalized
    
    async def analyze_vendors(
        self,
        vendors: List[VendorProfile],
        quotes: List[QuoteResponse],
        compliance_evaluations: Dict[str, Dict[str, Any]],
        delivery_evaluations: Dict[str, Dict[str, Any]],
        financial_evaluations: Dict[str, Dict[str, Any]],
        workflow_id: Optional[str] = None,
    ) -> ComparisonReport:
        """
        Perform comprehensive comparison and analysis.
        
        Returns: ComparisonReport with analysis and recommendations
        """
        rfq_logger.info(
            f"Starting comparison analysis for {len(vendors)} vendors",
            workflow_id=workflow_id,
        )
        
        # Step 1: Merge evaluation tracks
        merged_scores = await self.merge_evaluation_tracks(
            vendors=vendors,
            compliance_evaluations=compliance_evaluations,
            delivery_evaluations=delivery_evaluations,
            financial_evaluations=financial_evaluations,
            workflow_id=workflow_id,
        )
        
        # Step 2: Create normalized quotes
        normalized_quotes = self._create_normalized_quotes(
            vendors=vendors,
            quotes=quotes,
            merged_scores=merged_scores,
        )
        
        # Step 3: Sort by merged score descending to identify top vendors
        sorted_by_score = sorted(
            normalized_quotes,
            key=lambda x: merged_scores.get(x.vendor_id, 0),
            reverse=True,
        )
        
        # Step 4: Create top ranked vendors list (top 3)
        top_ranked: List[Dict[str, Any]] = []
        for idx, quote in enumerate(sorted_by_score[:3], 1):
            vendor = next(v for v in vendors if v.vendor_id == quote.vendor_id)
            score = merged_scores.get(vendor.vendor_id, 0)
            
            # Convert 0-100 to 0-5 scale for display
            score_5 = (score / 100) * 5.0
            
            top_ranked.append({
                "rank": idx,
                "vendor_id": vendor.vendor_id,
                "vendor_name": vendor.vendor_name,
                "score": round(score_5, 1),
                "total_price": quote.total_price,
                "recommendation": "RECOMMENDED" if idx == 1 else "ACCEPTABLE" if idx == 2 else "CAUTION",
            })
        
        # Step 5: Build risk summary
        risk_summary = self._build_risk_summary(merged_scores, compliance_evaluations)
        
        # Step 6: Create recommendations text
        recommendations = (
            f"Top recommendation: {sorted_by_score[0].vendor_name} "
            f"(Score: {merged_scores.get(sorted_by_score[0].vendor_id, 0):.1f}/100, "
            f"Price: ${sorted_by_score[0].total_price:,.2f})\n"
            f"Evaluated {len(vendors)} vendors across Compliance, Delivery, and Financial tracks."
        )
        
        # Create and return report
        report = ComparisonReport(
            report_id=f"report-{uuid.uuid4().hex[:8]}",
            normalized_quotes=normalized_quotes,
            vendor_evaluations=[],  # Placeholder: would need VendorEvaluation objects
            top_ranked_vendors=top_ranked,
            risk_summary=risk_summary,
            recommendations=recommendations,
        )
        
        rfq_logger.info(
            f"Comparison analysis complete. Top vendor: {sorted_by_score[0].vendor_name}",
            workflow_id=workflow_id,
        )
        
        return report
