"""
Phase 8: RFQ Workflow Master Orchestrator

Coordinates the complete end-to-end RFQ workflow from initial request to PO generation.

Pipeline:
1. Phase 2: Preprocessing (ProductReview + VendorQualification)
2. Phase 3: Parallel Orchestration (RFQ Submission + Quote Parsing + 3 Evaluation Tracks)
3. Phase 4: Comparison & Analysis
4. Phase 5: Negotiation Strategy
5. Phase 6: Human Gate (Approval/Reject/Edit)
6. Phase 7: Purchase Order Generation

This orchestrator chains all individual phases into one cohesive workflow.
"""

import asyncio
from typing import Optional, Tuple, Any, Dict, AsyncGenerator
from datetime import datetime

from src.agents.workflows.rfq.models import (
    RFQRequest,
    ProductRequirements,
    VendorProfile,
    QuoteResponse,
    ComparisonReport,
    NegotiationRecommendation,
    ApprovalGateResponse,
    ApprovalDecision,
    PurchaseOrder,
)
from src.agents.workflows.rfq.orchestrators.preprocessing_orchestrator import (
    PreprocessingOrchestrator,
)
from src.agents.workflows.rfq.orchestrators.parallel_evaluation_orchestrator import (
    ParallelEvaluationOrchestrator,
)
from src.agents.workflows.rfq.agents.rfq_submission_agent import RFQSubmissionExecutor
from src.agents.workflows.rfq.agents.quote_parsing_agent import QuoteParsingExecutor
from src.agents.workflows.rfq.agents.comparison_analysis_agent import (
    ComparisonAndAnalysisAgent,
)
from src.agents.workflows.rfq.agents.negotiation_strategy_agent import (
    NegotiationStrategyAgent,
)
from src.agents.workflows.rfq.agents.human_gate_agent import HumanGateAgent
from src.agents.workflows.rfq.agents.purchase_order_agent import PurchaseOrderAgent
from src.agents.workflows.rfq.observability import rfq_logger


class RFQWorkflowOrchestrator:
    """
    Master orchestrator for complete RFQ workflow.
    
    This orchestrator chains all phases together:
    - Phase 2: Preprocessing (sequential)
    - Phase 3: Parallel evaluation (concurrent)
    - Phase 4: Comparison (LLM analysis)
    - Phase 5: Negotiation strategy (LLM expert)
    - Phase 6: Human gate (async approval)
    - Phase 7: PO generation (final output)
    
    The orchestrator maintains state throughout the workflow and provides
    observability at each phase transition.
    """
    
    def __init__(self):
        """Initialize the master orchestrator with all sub-components."""
        self.preprocessing_orchestrator = PreprocessingOrchestrator()
        self.parallel_evaluation_orchestrator = ParallelEvaluationOrchestrator()
        self.rfq_submission_executor = RFQSubmissionExecutor()
        self.quote_parsing_executor = QuoteParsingExecutor()
        self.comparison_agent = ComparisonAndAnalysisAgent()
        self.negotiation_agent = NegotiationStrategyAgent()
        self.human_gate_agent = HumanGateAgent()
        self.po_agent = PurchaseOrderAgent()
        
        rfq_logger.info("RFQ Workflow Master Orchestrator initialized")
    
    async def execute_full_workflow(
        self,
        rfq_request: RFQRequest,
        workflow_id: str,
        buyer_name: str = "Procurement Manager",
        buyer_email: str = "procurement@company.com",
        wait_for_human: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute the complete RFQ workflow from request to PO.
        
        Args:
            rfq_request: Initial RFQ request from user
            workflow_id: Unique workflow identifier
            buyer_name: Name of the buyer/procurement manager
            buyer_email: Email of the buyer
            wait_for_human: If False, will auto-approve for testing
            
        Returns:
            dict with all intermediate results and final PO
        """
        rfq_logger.info(
            f"Starting full RFQ workflow",
            extra={"workflow_id": workflow_id, "request_id": rfq_request.request_id},
        )
        
        results: Dict[str, Any] = {
            "workflow_id": workflow_id,
            "request_id": rfq_request.request_id,
            "started_at": datetime.now().isoformat(),
        }
        
        # =======================================================================
        # PHASE 2: PREPROCESSING
        # =======================================================================
        rfq_logger.info("Phase 2: Starting preprocessing", extra={"workflow_id": workflow_id})
        
        requirements, vendors = await self.preprocessing_orchestrator.preprocess(
            rfq_request=rfq_request,
            workflow_id=workflow_id,
        )
        
        results["phase2_requirements"] = requirements
        results["phase2_vendors"] = vendors
        
        rfq_logger.info(
            f"Phase 2 complete: {len(vendors)} vendors qualified",
            extra={"workflow_id": workflow_id},
        )
        
        # =======================================================================
        # PHASE 3: PARALLEL ORCHESTRATION
        # =======================================================================
        rfq_logger.info("Phase 3: Starting parallel evaluation", extra={"workflow_id": workflow_id})
        
        # 3.1: Submit RFQ to all vendors in parallel
        submissions = await self.rfq_submission_executor.submit_to_all_vendors(
            requirements=requirements,
            vendors=vendors,
            workflow_id=workflow_id,
        )
        
        results["phase3_submissions"] = submissions
        
        # 3.2: Parse all quotes in parallel
        parsed_quotes = await self.quote_parsing_executor.execute(
            requirements=requirements,
            vendors=vendors,
            submissions=submissions,
            workflow_id=workflow_id,
        )
        
        # Store raw quotes (QuoteResponse objects as dicts) for backward compatibility
        results["phase3_raw_quotes"] = [q.model_dump() for q in parsed_quotes]
        results["phase3_parsed_quotes"] = [q.model_dump() for q in parsed_quotes]
        
        # 3.3: Run 3 evaluation tracks in parallel
        vendor_evaluations, track_results = await self.parallel_evaluation_orchestrator.evaluate_all_vendors(
            requirements=requirements,
            vendors=vendors,
            quotes=parsed_quotes,
            workflow_id=workflow_id,
        )
        
        results["phase3_evaluations"] = [e.model_dump() for e in vendor_evaluations]
        results["phase3_vendor_evaluations"] = [e.model_dump() for e in vendor_evaluations]
        results["phase3_track_results"] = [
            {
                "track_name": t.track_name,
                "vendor_id": t.vendor_id,
                "vendor_name": t.vendor_name,
                "score": t.score,
                "recommendation": t.recommendation,
                "risk_level": t.risk_level,
                "details": t.details,
            }
            for t in track_results
        ]
        
        rfq_logger.info(
            f"Phase 3 complete: {len(parsed_quotes)} quotes evaluated",
            extra={"workflow_id": workflow_id},
        )
        
        # =======================================================================
        # PHASE 4: COMPARISON & ANALYSIS
        # =======================================================================
        rfq_logger.info("Phase 4: Starting comparison analysis", extra={"workflow_id": workflow_id})
        
        # Merge evaluation tracks
        compliance_evals = {t.vendor_id: {"confidence": t.score / 100} for t in track_results if t.track_name == "Certification Compliance"}
        delivery_evals = {t.vendor_id: {"confidence": t.score / 100} for t in track_results if t.track_name == "Delivery Risk"}
        financial_evals = {t.vendor_id: {"confidence": t.score / 100} for t in track_results if t.track_name == "Financial Analysis"}
        
        merged_scores = await self.comparison_agent.merge_evaluation_tracks(
            vendors=vendors,
            compliance_evaluations=compliance_evals,
            delivery_evaluations=delivery_evals,
            financial_evaluations=financial_evals,
            workflow_id=workflow_id,
        )
        
        # Generate comparison report
        comparison_report = await self.comparison_agent.analyze_vendors(
            vendors=vendors,
            quotes=parsed_quotes,
            compliance_evaluations=compliance_evals,
            delivery_evaluations=delivery_evals,
            financial_evaluations=financial_evals,
            workflow_id=workflow_id,
        )
        
        results["phase4_comparison_report"] = comparison_report.model_dump()
        
        rfq_logger.info(
            f"Phase 4 complete: Top vendor is {comparison_report.top_ranked_vendors[0]['vendor_name']}",
            extra={"workflow_id": workflow_id},
        )
        
        # =======================================================================
        # PHASE 5: NEGOTIATION STRATEGY
        # =======================================================================
        rfq_logger.info("Phase 5: Starting negotiation strategy", extra={"workflow_id": workflow_id})
        
        negotiation_recommendation = await self.negotiation_agent.generate_recommendation(
            comparison_report=comparison_report,
            quantity=requirements.quantity,
            workflow_id=workflow_id,
        )
        
        results["phase5_negotiation_recommendation"] = negotiation_recommendation.model_dump()
        
        rfq_logger.info(
            f"Phase 5 complete: Target vendor {negotiation_recommendation.vendor_name}, "
            f"potential savings: ${negotiation_recommendation.estimated_cost_savings or 0:.2f}",
            extra={"workflow_id": workflow_id},
        )
        
        # =======================================================================
        # PHASE 6: HUMAN GATE (APPROVAL)
        # =======================================================================
        rfq_logger.info("Phase 6: Requesting human approval", extra={"workflow_id": workflow_id})
        
        # Request human input
        human_gate_response = await self.human_gate_agent.request_human_input(
            recommendation=negotiation_recommendation
        )
        
        results["phase6_human_gate_request"] = human_gate_response
        
        # In production, we would wait for frontend to POST approval
        # For testing, we can auto-approve or wait
        if not wait_for_human:
            # Auto-approve for testing
            approval = ApprovalGateResponse(
                request_id=workflow_id,
                decision=ApprovalDecision.APPROVED,
                decision_maker=buyer_name,
            )
            
            approved_recommendation = await self.human_gate_agent.handle_human_action(
                action="approve",
                data=None,
            )
        else:
            # In production, this would wait for the POST /api/human-gate/action call
            rfq_logger.info(
                "Waiting for human approval via frontend...",
                extra={"workflow_id": workflow_id},
            )
            
            # For now, return early with status "awaiting_approval"
            results["status"] = "awaiting_approval"
            results["message"] = "Workflow paused for human approval"
            return results
        
        results["phase6_approval"] = approval.model_dump()
        
        rfq_logger.info(
            f"Phase 6 complete: Decision = {approval.decision}",
            extra={"workflow_id": workflow_id},
        )
        
        if approval.decision != "approved":
            results["status"] = "rejected"
            results["message"] = f"Workflow terminated: {approval.decision}"
            return results
        
        # =======================================================================
        # PHASE 7: PURCHASE ORDER GENERATION
        # =======================================================================
        rfq_logger.info("Phase 7: Generating purchase order", extra={"workflow_id": workflow_id})
        
        # Find the target vendor profile
        target_vendor = next(
            (v for v in vendors if v.vendor_id == negotiation_recommendation.vendor_id),
            vendors[0],  # Fallback to first vendor
        )
        
        purchase_order = await self.po_agent.generate_purchase_order(
            recommendation=negotiation_recommendation,
            approval=approval,
            requirements=requirements,
            vendor=target_vendor,
            workflow_id=workflow_id,
            buyer_name=buyer_name,
            buyer_email=buyer_email,
        )
        
        results["phase7_purchase_order"] = purchase_order.model_dump()
        
        rfq_logger.info(
            f"Phase 7 complete: PO {purchase_order.po_number} generated for {target_vendor.vendor_name}",
            extra={"workflow_id": workflow_id},
        )
        
        # Issue the PO
        issued_po = await self.po_agent.issue_purchase_order(
            purchase_order=purchase_order,
        )
        
        results["final_purchase_order"] = issued_po.model_dump()
        results["status"] = "completed"
        results["completed_at"] = datetime.now().isoformat()
        
        rfq_logger.info(
            f"RFQ Workflow complete: PO {issued_po.po_number} issued successfully",
            extra={"workflow_id": workflow_id},
        )
        
        return results

    async def execute_full_workflow_streaming(
        self,
        rfq_request: RFQRequest,
        workflow_id: str,
        buyer_name: str = "Procurement Manager",
        buyer_email: str = "procurement@company.com",
        wait_for_human: bool = True,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute the complete RFQ workflow with detailed phase-by-phase streaming.
        
        Yields detailed messages after each phase completion with full results.
        
        Args:
            rfq_request: Initial RFQ request from user
            workflow_id: Unique workflow identifier
            buyer_name: Name of the buyer/procurement manager
            buyer_email: Email of the buyer
            wait_for_human: If False, will auto-approve for testing
            
        Yields:
            dict with phase results and formatted message
        """
        rfq_logger.info(
            f"Starting streaming RFQ workflow",
            extra={"workflow_id": workflow_id, "request_id": rfq_request.request_id},
        )

    async def execute_full_workflow_streaming(
        self,
        rfq_request: RFQRequest,
        workflow_id: str,
        buyer_name: str = "Procurement Manager",
        buyer_email: str = "procurement@company.com",
        wait_for_human: bool = True,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute the complete RFQ workflow with detailed phase-by-phase streaming.
        
        Yields detailed messages after each phase completion with full results.
        
        Args:
            rfq_request: Initial RFQ request from user
            workflow_id: Unique workflow identifier
            buyer_name: Name of the buyer/procurement manager
            buyer_email: Email of the buyer
            wait_for_human: If False, will auto-approve for testing
            
        Yields:
            dict with phase results and formatted message
        """
        rfq_logger.info(
            f"Starting streaming RFQ workflow",
            extra={"workflow_id": workflow_id, "request_id": rfq_request.request_id},
        )
        
        # =======================================================================
        # PHASE 2: PREPROCESSING
        # =======================================================================
        rfq_logger.info("Phase 2: Starting preprocessing", extra={"workflow_id": workflow_id})
        
        requirements, vendors = await self.preprocessing_orchestrator.preprocess(
            rfq_request=rfq_request,
            workflow_id=workflow_id,
        )
        
        # Build detailed Phase 2 message
        phase2_message = f"""## Phase 2: Vendor Qualification Complete

**Product Requirements:**
- Product: {requirements.product_name}
- Category: {requirements.category}
- Quantity: {requirements.quantity:,} {requirements.unit}
- Required Certifications: {', '.join(requirements.required_certifications)}"""
        
        # Add budget if available from original request
        if rfq_request.budget_amount:
            phase2_message += f"\n- Budget: ${rfq_request.budget_amount:,.2f}"
        
        # Add delivery date if available
        if requirements.desired_delivery_date:
            phase2_message += f"\n- Delivery Date: {requirements.desired_delivery_date.strftime('%Y-%m-%d')}"
        
        phase2_message += f"\n\n**Qualified Vendors ({len(vendors)}):**\n"
        
        for i, vendor in enumerate(vendors, 1):
            phase2_message += f"\n**{i}. {vendor.vendor_name}** (ID: {vendor.vendor_id})\n"
            phase2_message += f"   - Rating: {vendor.overall_rating}/5.0\n"
            phase2_message += f"   - Certifications: {', '.join(vendor.certifications) if vendor.certifications else 'None'}\n"
            phase2_message += f"   - Lead Time: {vendor.estimated_lead_time_days} days\n"
            phase2_message += f"   - Location: {vendor.country}\n"
            if vendor.previous_orders > 0:
                phase2_message += f"   - Previous Orders: {vendor.previous_orders}\n"
        
        yield {
            "phase": "phase2_complete",
            "message": phase2_message,
            "data": {
                "requirements": requirements.model_dump(),
                "vendors": [v.model_dump() for v in vendors]
            }
        }
        
        # =======================================================================
        # PHASE 3: PARALLEL ORCHESTRATION
        # =======================================================================
        rfq_logger.info("Phase 3: Starting parallel evaluation", extra={"workflow_id": workflow_id})
        
        # 3.1: Submit RFQ to all vendors
        submissions = await self.rfq_submission_executor.submit_to_all_vendors(
            requirements=requirements,
            vendors=vendors,
            workflow_id=workflow_id,
        )
        
        # 3.2: Parse all quotes
        parsed_quotes = await self.quote_parsing_executor.execute(
            requirements=requirements,
            vendors=vendors,
            submissions=submissions,
            workflow_id=workflow_id,
        )
        
        # 3.3: Run 3 evaluation tracks in parallel
        vendor_evaluations, track_results = await self.parallel_evaluation_orchestrator.evaluate_all_vendors(
            requirements=requirements,
            vendors=vendors,
            quotes=parsed_quotes,
            workflow_id=workflow_id,
        )
        
        # Build detailed Phase 3 message
        phase3_message = f"""## Phase 3: Parallel Evaluation Complete

**Evaluation Summary:**
Evaluated {len(parsed_quotes)} vendor quotes across 3 evaluation tracks:

"""
        
        # Group track results by vendor
        vendor_track_map = {}
        for track in track_results:
            if track.vendor_id not in vendor_track_map:
                vendor_track_map[track.vendor_id] = {
                    "vendor_name": track.vendor_name,
                    "tracks": []
                }
            vendor_track_map[track.vendor_id]["tracks"].append(track)
        
        for vendor_id, vendor_data in vendor_track_map.items():
            quote = next((q for q in parsed_quotes if q.vendor_id == vendor_id), None)
            phase3_message += f"### {vendor_data['vendor_name']}\n"
            if quote:
                phase3_message += f"**Quote:** ${quote.unit_price:.2f}/unit (Total: ${quote.total_price:,.2f})\n\n"
            
            for track in vendor_data["tracks"]:
                risk_emoji = "🟢" if track.risk_level == "low" else "🟡" if track.risk_level == "medium" else "🔴"
                phase3_message += f"**{track.track_name}** {risk_emoji}\n"
                phase3_message += f"- Score: {track.score}/100\n"
                phase3_message += f"- Risk Level: {track.risk_level.upper()}\n"
                phase3_message += f"- Recommendation: {track.recommendation}\n"
                if track.details:
                    phase3_message += f"- Details: {track.details}\n"
                phase3_message += "\n"
        
        yield {
            "phase": "phase3_complete",
            "message": phase3_message,
            "data": {
                "quotes": [q.model_dump() for q in parsed_quotes],
                "evaluations": [e.model_dump() for e in vendor_evaluations],
                "track_results": [{
                    "track_name": t.track_name,
                    "vendor_id": t.vendor_id,
                    "vendor_name": t.vendor_name,
                    "score": t.score,
                    "recommendation": t.recommendation,
                    "risk_level": t.risk_level,
                    "details": t.details,
                } for t in track_results]
            }
        }
        
        # =======================================================================
        # PHASE 4: COMPARISON & ANALYSIS
        # =======================================================================
        rfq_logger.info("Phase 4: Starting comparison analysis", extra={"workflow_id": workflow_id})
        
        # Merge evaluation tracks
        compliance_evals = {t.vendor_id: {"confidence": t.score / 100} for t in track_results if t.track_name == "Certification Compliance"}
        delivery_evals = {t.vendor_id: {"confidence": t.score / 100} for t in track_results if t.track_name == "Delivery Risk"}
        financial_evals = {t.vendor_id: {"confidence": t.score / 100} for t in track_results if t.track_name == "Financial Analysis"}
        
        merged_scores = await self.comparison_agent.merge_evaluation_tracks(
            vendors=vendors,
            compliance_evaluations=compliance_evals,
            delivery_evaluations=delivery_evals,
            financial_evaluations=financial_evals,
            workflow_id=workflow_id,
        )
        
        # Generate comparison report
        comparison_report = await self.comparison_agent.analyze_vendors(
            vendors=vendors,
            quotes=parsed_quotes,
            compliance_evaluations=compliance_evals,
            delivery_evaluations=delivery_evals,
            financial_evaluations=financial_evals,
            workflow_id=workflow_id,
        )
        
        # Build detailed Phase 4 message
        phase4_message = f"""## Phase 4: Comparison Analysis Complete

**Vendor Rankings:**

"""
        
        for i, ranked_vendor in enumerate(comparison_report.top_ranked_vendors, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"**{i}.**"
            vendor_name = ranked_vendor.get('vendor_name', 'Unknown')
            score = ranked_vendor.get('score', 0)
            total_price = ranked_vendor.get('total_price', 0)
            recommendation = ranked_vendor.get('recommendation', '')
            
            phase4_message += f"{medal} **{vendor_name}**\n"
            phase4_message += f"   - Score: {score:.1f}/5.0\n"
            phase4_message += f"   - Total Price: ${total_price:,.2f}\n"
            phase4_message += f"   - Status: {recommendation}\n"
            phase4_message += "\n"
        
        # Add recommendations if available
        if hasattr(comparison_report, 'recommendations') and comparison_report.recommendations:
            phase4_message += f"**Analysis:**\n{comparison_report.recommendations}\n"
        
        yield {
            "phase": "phase4_complete",
            "message": phase4_message,
            "data": {
                "comparison_report": comparison_report.model_dump()
            }
        }
        
        # =======================================================================
        # PHASE 5: NEGOTIATION STRATEGY
        # =======================================================================
        rfq_logger.info("Phase 5: Starting negotiation strategy", extra={"workflow_id": workflow_id})
        
        negotiation_recommendation = await self.negotiation_agent.generate_recommendation(
            comparison_report=comparison_report,
            quantity=requirements.quantity,
            workflow_id=workflow_id,
        )
        
        # Build detailed Phase 5 message with FULL negotiation strategy
        phase5_message = f"""## Phase 5: Negotiation Strategy

**Target Vendor:** {negotiation_recommendation.vendor_name}

**Negotiation Strategy:**

{negotiation_recommendation.negotiation_strategy}

**Expected Outcome:**

{negotiation_recommendation.expected_outcome}
"""
        
        # Add suggested pricing if available
        if negotiation_recommendation.suggested_unit_price:
            phase5_message += f"\n**Pricing Recommendation:**\n"
            phase5_message += f"- Suggested Unit Price: ${negotiation_recommendation.suggested_unit_price:.2f}\n"
            phase5_message += f"- Total for {requirements.quantity:,} units: ${negotiation_recommendation.suggested_unit_price * requirements.quantity:,.2f}\n"
        
        # Add leverage points
        if negotiation_recommendation.leverage_points:
            phase5_message += f"\n**Leverage Points:**\n"
            for i, point in enumerate(negotiation_recommendation.leverage_points, 1):
                phase5_message += f"{i}. {point}\n"
        
        # Add fallback options
        if negotiation_recommendation.fallback_options:
            phase5_message += f"\n**Fallback Options:**\n"
            for i, option in enumerate(negotiation_recommendation.fallback_options, 1):
                phase5_message += f"{i}. {option}\n"
        
        yield {
            "phase": "phase5_complete",
            "message": phase5_message,
            "data": {
                "negotiation_recommendation": negotiation_recommendation.model_dump()
            }
        }
        
        # =======================================================================
        # PHASE 6: HUMAN GATE (APPROVAL)
        # =======================================================================
        rfq_logger.info("Phase 6: Requesting human approval", extra={"workflow_id": workflow_id})
        
        human_gate_response = await self.human_gate_agent.request_human_input(
            recommendation=negotiation_recommendation
        )
        
        if not wait_for_human:
            # Auto-approve for testing
            approval = ApprovalGateResponse(
                request_id=workflow_id,
                decision=ApprovalDecision.APPROVED,
                decision_maker=buyer_name,
            )
            
            phase6_message = f"""## Phase 6: Approval

✅ **Auto-Approved** (demonstration mode)

**Approved By:** {buyer_name}
**Decision:** Proceed with purchase order"""
            
            if negotiation_recommendation.suggested_unit_price:
                phase6_message += f"\n**Approved Amount:** ${negotiation_recommendation.suggested_unit_price * requirements.quantity:,.2f}"
            
            phase6_message += "\n"
        else:
            phase6_message = f"""## Phase 6: Awaiting Human Approval

⏳ **Approval Required**

Please review the negotiation recommendation and approve or reject the purchase.
"""
            
            yield {
                "phase": "phase6_awaiting",
                "message": phase6_message,
                "data": {
                    "human_gate_request": human_gate_response,
                    "status": "awaiting_approval"
                }
            }
            return
        
        yield {
            "phase": "phase6_complete",
            "message": phase6_message,
            "data": {
                "approval": approval.model_dump()
            }
        }
        
        # =======================================================================
        # PHASE 7: PURCHASE ORDER GENERATION
        # =======================================================================
        rfq_logger.info("Phase 7: Generating purchase order", extra={"workflow_id": workflow_id})
        
        target_vendor = next(
            (v for v in vendors if v.vendor_id == negotiation_recommendation.vendor_id),
            vendors[0],
        )
        
        purchase_order = await self.po_agent.generate_purchase_order(
            recommendation=negotiation_recommendation,
            approval=approval,
            requirements=requirements,
            vendor=target_vendor,
            workflow_id=workflow_id,
            buyer_name=buyer_name,
            buyer_email=buyer_email,
        )
        
        issued_po = await self.po_agent.issue_purchase_order(
            purchase_order=purchase_order,
        )
        
        # Build detailed Phase 7 message
        phase7_message = f"""## Phase 7: Purchase Order Issued

✅ **Purchase Order Created Successfully**

**PO Number:** {issued_po.po_number}
**Status:** {issued_po.status.upper()}

**Vendor Information:**
- Name: {issued_po.vendor_name}
- Contact: {issued_po.vendor_contact}

**Order Details:**
- Product: {issued_po.product_name}
- Quantity: {issued_po.quantity:,} {issued_po.unit}
- Unit Price: ${issued_po.unit_price:.2f}
- **Total Amount: ${issued_po.total_amount:,.2f}**

**Delivery:**
- Expected Date: {issued_po.delivery_date.strftime('%Y-%m-%d')}

**Payment:**
- Terms: {issued_po.payment_terms}

**Buyer:**
- Name: {issued_po.buyer_name}
- Email: {issued_po.buyer_email}

---

🎉 **RFQ Procurement Workflow Complete!**
"""
        
        yield {
            "phase": "phase7_complete",
            "message": phase7_message,
            "data": {
                "purchase_order": issued_po.model_dump(),
                "status": "completed",
                "completed_at": datetime.now().isoformat()
            }
        }
        
        rfq_logger.info(
            f"RFQ Workflow complete: PO {issued_po.po_number} issued successfully",
            extra={"workflow_id": workflow_id},
        )
