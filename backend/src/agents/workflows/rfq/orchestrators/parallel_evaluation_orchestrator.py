"""
Parallel Evaluation Orchestrator for Phase 3

Coordinates 3 parallel evaluation tracks:
1. Certification Compliance Evaluator (LLM-enhanced)
2. Delivery Risk Assessor (Hybrid)
3. Financial Analysis Evaluator (LLM-enhanced)

Uses concurrent execution pattern to evaluate all vendors across all tracks in parallel.
Merges results into unified vendor scorecard.
"""

import logging
import asyncio
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

from src.agents.workflows.rfq.models import (
    ProductRequirements,
    VendorProfile,
    QuoteResponse,
    VendorEvaluation,
    RiskLevel,
)
from src.agents.workflows.rfq.agents.llm_evaluators import (
    CertificationComplianceEvaluator,
    FinancialAnalysisEvaluator,
    DeliveryRiskAssessor,
)
from src.agents.workflows.rfq.observability import rfq_logger

logger = logging.getLogger(__name__)


@dataclass
class EvaluationTrackResult:
    """Result from a single evaluation track"""
    track_name: str
    vendor_id: str
    vendor_name: str
    score: float  # 0-100
    recommendation: str  # APPROVE, FLAG_CONCERN, REJECT
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    details: Dict[str, Any]


class ParallelEvaluationOrchestrator:
    """
    Orchestrates parallel evaluation across 3 tracks.
    
    Each track runs independently and concurrently:
    - Track 1: CertificationComplianceEvaluator
    - Track 2: DeliveryRiskAssessor
    - Track 3: FinancialAnalysisEvaluator
    
    All three evaluate all vendors in parallel for maximum efficiency.
    Results are merged into unified vendor scorecard.
    """
    
    def __init__(self):
        """Initialize orchestrator."""
        self.logger = rfq_logger
    
    async def evaluate_all_vendors(
        self,
        requirements: ProductRequirements,
        vendors: List[VendorProfile],
        quotes: List[QuoteResponse],
        workflow_id: str,
    ) -> Tuple[List[VendorEvaluation], List[EvaluationTrackResult]]:
        """
        Run all 3 evaluation tracks in parallel for all vendors.
        
        Args:
            requirements: ProductRequirements
            vendors: List of vendors to evaluate
            quotes: List of quotes from vendors
            workflow_id: Workflow ID for tracing
            
        Returns:
            Tuple of (List[VendorEvaluation], List[EvaluationTrackResult])
        """
        self.logger.info(
            f"Starting parallel evaluation of {len(vendors)} vendors across 3 tracks",
            workflow_id=workflow_id,
            stage="parallel_evaluation",
        )
        
        try:
            # Create evaluator instances
            compliance_evaluator = CertificationComplianceEvaluator(requirements)
            financial_evaluator = FinancialAnalysisEvaluator(
                requirements.product_name,
                requirements.quantity,
            )
            delivery_assessor = DeliveryRiskAssessor(requirements)
            
            self.logger.info(
                f"Evaluators created, starting parallel evaluation tracks",
                workflow_id=workflow_id,
                stage="parallel_evaluation",
            )
            
            # ================================================================
            # Track 1: Compliance Evaluation (for each vendor)
            # ================================================================
            compliance_tasks = [
                self._evaluate_compliance(
                    compliance_evaluator, vendor, workflow_id
                )
                for vendor in vendors
            ]
            
            # ================================================================
            # Track 2: Delivery Assessment (for each vendor)
            # ================================================================
            delivery_tasks = [
                self._assess_delivery(delivery_assessor, vendor, workflow_id)
                for vendor in vendors
            ]
            
            # ================================================================
            # Track 3: Financial Analysis (all vendors together)
            # ================================================================
            financial_tasks = [
                self._analyze_financial(
                    financial_evaluator, vendor, quotes, workflow_id
                )
                for vendor in vendors
            ]
            
            # Execute all tasks in parallel
            all_tasks = compliance_tasks + delivery_tasks + financial_tasks
            results = await asyncio.gather(*all_tasks, return_exceptions=False)
            
            # Separate results by track
            num_vendors = len(vendors)
            compliance_results = results[:num_vendors]
            delivery_results = results[num_vendors : num_vendors * 2]
            financial_results = results[num_vendors * 2 :]
            
            self.logger.info(
                f"✅ Parallel evaluation complete: {len(compliance_results)} compliance, "
                f"{len(delivery_results)} delivery, {len(financial_results)} financial",
                workflow_id=workflow_id,
                stage="parallel_evaluation",
            )
            
            # Merge results into vendor evaluations
            vendor_evaluations = self._merge_track_results(
                vendors,
                compliance_results,
                delivery_results,
                financial_results,
                workflow_id,
            )
            
            # Flatten all track results for detailed reporting
            all_track_results = compliance_results + delivery_results + financial_results
            
            return vendor_evaluations, all_track_results
            
        except Exception as e:
            self.logger.error(
                f"Parallel evaluation failed: {e}",
                workflow_id=workflow_id,
                stage="parallel_evaluation",
            )
            raise
    
    async def _evaluate_compliance(
        self,
        evaluator: CertificationComplianceEvaluator,
        vendor: VendorProfile,
        workflow_id: str,
    ) -> EvaluationTrackResult:
        """Evaluate vendor compliance (Track 1)."""
        try:
            result = await evaluator.evaluate_vendor_compliance(vendor, workflow_id)
            
            return EvaluationTrackResult(
                track_name="Compliance",
                vendor_id=vendor.vendor_id,
                vendor_name=vendor.vendor_name,
                score=result.get("confidence", 0.5) * 100,
                recommendation=result.get("recommendation", "FLAG_CONCERN"),
                risk_level=result.get("risk_level", "MEDIUM"),
                details=result,
            )
        except Exception as e:
            self.logger.error(
                f"Compliance evaluation failed for {vendor.vendor_name}: {e}",
                workflow_id=workflow_id,
            )
            return EvaluationTrackResult(
                track_name="Compliance",
                vendor_id=vendor.vendor_id,
                vendor_name=vendor.vendor_name,
                score=50.0,
                recommendation="FLAG_CONCERN",
                risk_level="HIGH",
                details={"error": str(e)},
            )
    
    async def _assess_delivery(
        self,
        evaluator: DeliveryRiskAssessor,
        vendor: VendorProfile,
        workflow_id: str,
    ) -> EvaluationTrackResult:
        """Assess vendor delivery capability (Track 2)."""
        try:
            result = await evaluator.assess_delivery_risk(vendor, workflow_id)
            
            return EvaluationTrackResult(
                track_name="Delivery",
                vendor_id=vendor.vendor_id,
                vendor_name=vendor.vendor_name,
                score=result.get("confidence", 0.5) * 100,
                recommendation=result.get("recommendation", "MONITOR"),
                risk_level=result.get("geopolitical_risk", "MEDIUM"),
                details=result,
            )
        except Exception as e:
            self.logger.error(
                f"Delivery assessment failed for {vendor.vendor_name}: {e}",
                workflow_id=workflow_id,
            )
            return EvaluationTrackResult(
                track_name="Delivery",
                vendor_id=vendor.vendor_id,
                vendor_name=vendor.vendor_name,
                score=50.0,
                recommendation="MONITOR",
                risk_level="MEDIUM",
                details={"error": str(e)},
            )
    
    async def _analyze_financial(
        self,
        evaluator: FinancialAnalysisEvaluator,
        vendor: VendorProfile,
        quotes: List[QuoteResponse],
        workflow_id: str,
    ) -> EvaluationTrackResult:
        """Analyze vendor financial terms (Track 3)."""
        try:
            # Get quotes for this vendor only
            vendor_quotes = [q for q in quotes if q.vendor_id == vendor.vendor_id]
            if not vendor_quotes:
                vendor_quotes = quotes  # Fallback to all quotes
            
            result = await evaluator.analyze_quotes(
                [vendor], vendor_quotes, workflow_id
            )
            
            return EvaluationTrackResult(
                track_name="Financial",
                vendor_id=vendor.vendor_id,
                vendor_name=vendor.vendor_name,
                score=result.get("confidence", 0.5) * 100,
                recommendation=result.get("recommendation", "REVIEW"),
                risk_level="LOW",  # Financial doesn't have risk levels
                details=result,
            )
        except Exception as e:
            self.logger.error(
                f"Financial analysis failed for {vendor.vendor_name}: {e}",
                workflow_id=workflow_id,
            )
            return EvaluationTrackResult(
                track_name="Financial",
                vendor_id=vendor.vendor_id,
                vendor_name=vendor.vendor_name,
                score=50.0,
                recommendation="REVIEW",
                risk_level="LOW",
                details={"error": str(e)},
            )
    
    def _merge_track_results(
        self,
        vendors: List[VendorProfile],
        compliance_results: List[EvaluationTrackResult],
        delivery_results: List[EvaluationTrackResult],
        financial_results: List[EvaluationTrackResult],
        workflow_id: str,
    ) -> List[VendorEvaluation]:
        """
        Merge results from all 3 tracks into unified vendor evaluations.
        
        Scoring: Equal weighting across tracks
        - Compliance: 33%
        - Delivery: 33%
        - Financial: 34%
        """
        vendor_evaluations = []
        
        for i, vendor in enumerate(vendors):
            compliance = compliance_results[i] if i < len(compliance_results) else None
            delivery = delivery_results[i] if i < len(delivery_results) else None
            financial = financial_results[i] if i < len(financial_results) else None
            
            # Calculate composite score (0-100)
            scores = []
            if compliance:
                scores.append(compliance.score)
            if delivery:
                scores.append(delivery.score)
            if financial:
                scores.append(financial.score)
            
            composite_score = sum(scores) / len(scores) if scores else 50.0
            
            # Determine overall recommendation
            recommendations = []
            if compliance:
                recommendations.append(compliance.recommendation)
            if delivery:
                recommendations.append(delivery.recommendation)
            if financial:
                recommendations.append(financial.recommendation)
            
            # If any track says REJECT, reject overall
            if "REJECT" in recommendations:
                overall_recommendation = "REJECT"
            # If any track says FLAG_CONCERN, flag overall
            elif "FLAG_CONCERN" in recommendations:
                overall_recommendation = "FLAG_CONCERN"
            # Otherwise approve
            else:
                overall_recommendation = "APPROVE"
            
            # Determine risk level
            risk_levels = []
            if compliance:
                risk_levels.append(compliance.risk_level)
            if delivery:
                risk_levels.append(delivery.risk_level)
            
            if "CRITICAL" in risk_levels:
                overall_risk = RiskLevel.CRITICAL
            elif "HIGH" in risk_levels:
                overall_risk = RiskLevel.HIGH
            elif "MEDIUM" in risk_levels:
                overall_risk = RiskLevel.MEDIUM
            else:
                overall_risk = RiskLevel.LOW
            
            # Create vendor evaluation
            evaluation = VendorEvaluation(
                vendor_id=vendor.vendor_id,
                vendor_name=vendor.vendor_name,
                review_score=round(composite_score / 20, 1),  # Convert 0-100 to 0-5 scale
                certifications_verified=(
                    compliance and compliance.recommendation == "APPROVE"
                ),
                compliance_status="compliant" if (
                    compliance and compliance.recommendation in ["APPROVE", "MONITOR"]
                ) else "non-compliant",
                delivery_feasible=delivery and delivery.recommendation != "REJECT",
                delivery_lead_assessment="on_time" if (
                    delivery and delivery.score >= 75
                ) else "tight",
                geographic_risk=delivery.risk_level if delivery else RiskLevel.MEDIUM,
                delivery_confidence=(delivery.score / 100.0) if delivery else 0.5,
                price_competitiveness=(financial.score / 100.0) if financial else 0.5,
                risk_level=overall_risk,
                evaluator_notes=(
                    f"Compliance: {compliance.score:.1f}%, "
                    f"Delivery: {delivery.score:.1f}%, "
                    f"Financial: {financial.score:.1f}%. "
                    f"Recommendation: {overall_recommendation}"
                    if compliance and delivery and financial
                    else "Partial evaluation (some tracks failed)"
                ),
            )
            
            vendor_evaluations.append(evaluation)
            
            self.logger.info(
                f"✅ Vendor evaluation merged: {vendor.vendor_name} "
                f"Review={evaluation.review_score}, Compliance={evaluation.compliance_status}",
                workflow_id=workflow_id,
                stage="parallel_evaluation",
            )
        
        return vendor_evaluations
