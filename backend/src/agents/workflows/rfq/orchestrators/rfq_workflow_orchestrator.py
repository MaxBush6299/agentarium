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
from time import perf_counter
from typing import Optional, Tuple, Any, Dict, AsyncGenerator
from datetime import datetime, timedelta

from src.agents.workflows.rfq.models import (
    RFQRequest,
    ProductRequirements,
    VendorProfile,
    QuoteResponse,
    ComparisonReport,
    NegotiationRecommendation,
    ApprovalGateResponse,
    ApprovalDecision,
    ApprovalRequest,
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
from src.agents.workflows.rfq.rfq_section_builder import (
    build_phase_block,
    prune_phase_blocks,
    build_comparison_markdown,
    build_negotiation_sub_blocks,
)
from src.persistence.threads import get_thread_repository


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
    
    def __init__(self, thread_id: Optional[str] = None, agent_id: str = "rfq-procurement"):
        """Initialize the master orchestrator with all sub-components.

        Args:
            thread_id: Optional thread identifier for persistence
            agent_id: Partition key for thread repository operations
        """
        self.preprocessing_orchestrator = PreprocessingOrchestrator()
        self.parallel_evaluation_orchestrator = ParallelEvaluationOrchestrator()
        self.rfq_submission_executor = RFQSubmissionExecutor()
        self.quote_parsing_executor = QuoteParsingExecutor()
        self.comparison_agent = ComparisonAndAnalysisAgent()
        self.negotiation_agent = NegotiationStrategyAgent()
        self.human_gate_agent = HumanGateAgent()
        self.po_agent = PurchaseOrderAgent()
        
        # Store thread ID for workflow state persistence
        self._thread_id = thread_id
        self._agent_id = agent_id
        
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
        Emits structured phase blocks with metrics for collapsible UI sections.
        
        Args:
            rfq_request: Initial RFQ request from user
            workflow_id: Unique workflow identifier
            buyer_name: Name of the buyer/procurement manager
            buyer_email: Email of the buyer
            wait_for_human: If False, will auto-approve for testing
            
        Yields:
            dict phase blocks `{type:'agent_section', phase, title, markdown, metrics, data}`
        """
        rfq_logger.info(
            f"Starting streaming RFQ workflow",
            extra={"workflow_id": workflow_id, "request_id": rfq_request.request_id},
        )

        agent_pk = self._agent_id  # Partition key for thread operations
        thread_repo = get_thread_repository()
        thread = None
        if self._thread_id:
            try:
                thread = await thread_repo.get(self._thread_id, agent_pk)
            except Exception as e:
                rfq_logger.warning(f"Thread fetch failed: {e}")

        def persist_phase_block(block: Dict[str, Any]):
            """Append phase block to thread metadata and prune (async wrapper)."""
            async def _update():
                nonlocal thread
                if not self._thread_id:
                    return
                try:
                    if not thread:
                        thread_local = await thread_repo.get(self._thread_id, agent_pk)
                    else:
                        thread_local = thread
                    if not thread_local:
                        return
                    if thread_local.metadata is None:
                        thread_local.metadata = {}
                    blocks = thread_local.metadata.get("rfq_phases", [])
                    blocks.append(block)
                    blocks = prune_phase_blocks(blocks, max_blocks=8)
                    thread_local.metadata["rfq_phases"] = blocks
                    await thread_repo.update(thread_local)
                    thread = thread_local
                except Exception as ex:
                    rfq_logger.warning(f"Persist phase block failed: {ex}")
            return _update()

        async def emit_phase(
            phase_key: str,
            title: str,
            markdown_sections: Any,
            data: Dict[str, Any],
            sub_blocks: Optional[Any] = None,
        ):
            start = perf_counter()
            # Token usage currently unavailable for procedural phases → zeros
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            metrics = {
                "duration_ms": 0,  # placeholder until end
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "estimated": False,
            }
            block = build_phase_block(
                phase_id=phase_key,
                title=title,
                markdown_sections=markdown_sections,
                metrics=metrics,
                sub_blocks=sub_blocks,
            )
            # Update duration
            block["metrics"]["duration_ms"] = int((perf_counter() - start) * 1000)
            await persist_phase_block(block)
            yield {
                "type": "agent_section",
                "phase": phase_key,
                "title": block["title"],
                "markdown": block["markdown"],
                "metrics": block["metrics"],
                "sub_blocks": block.get("sub_blocks", []),
                "isPhaseMessage": True,
                "data": data,
            }

        # ===================================================================
        # PHASE 2: PREPROCESSING
        # ===================================================================
        
        rfq_logger.info("Phase 2: Starting preprocessing", extra={"workflow_id": workflow_id})
        
        requirements, vendors = await self.preprocessing_orchestrator.preprocess(
            rfq_request=rfq_request,
            workflow_id=workflow_id,
        )
        # Build markdown sections (summary + vendor list table)
        req_lines = [
            f"Product: {requirements.product_name}",
            f"Category: {requirements.category}",
            f"Quantity: {requirements.quantity:,} {requirements.unit}",
            f"Required Certifications: {', '.join(requirements.required_certifications)}",
        ]
        if rfq_request.budget_amount:
            req_lines.append(f"Budget: ${rfq_request.budget_amount:,.2f}")
        if requirements.desired_delivery_date:
            req_lines.append(f"Delivery Date: {requirements.desired_delivery_date.strftime('%Y-%m-%d')}")
        summary_body = "\n".join(f"- {l}" for l in req_lines)
        vendor_rows = []
        for v in vendors:
            vendor_rows.append([
                v.vendor_name,
                v.overall_rating,
                ", ".join(v.certifications) if v.certifications else "None",
                v.estimated_lead_time_days,
                v.country,
            ])
        from src.agents.workflows.rfq.rfq_section_builder import build_markdown_table
        vendor_table = build_markdown_table(
            ["Vendor", "Rating", "Certifications", "Lead Days", "Country"], vendor_rows
        )
        sections_phase2 = [
            {"title": "Requirements", "body": summary_body},
            {"title": "Qualified Vendors", "body": vendor_table},
        ]
        async for ev in emit_phase(
            phase_key="phase2_complete",
            title="Phase 2: Vendor Qualification Complete",
            markdown_sections=sections_phase2,
            data={
                "requirements": requirements.model_dump(),
                "vendors": [v.model_dump() for v in vendors],
            },
        ):
            yield ev
        
        # ===================================================================
        # PHASE 3: PARALLEL ORCHESTRATION
        # ===================================================================
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
        # Build summary sections
        eval_summary = f"Evaluated {len(parsed_quotes)} vendor quotes across 3 evaluation tracks."\
            if parsed_quotes else "No quotes parsed."
        track_rows = []
        for t in track_results:
            track_rows.append([
                t.vendor_name,
                t.track_name,
                t.score,
                t.risk_level,
                t.recommendation,
            ])
        track_table = build_markdown_table(
            ["Vendor", "Track", "Score", "Risk", "Recommendation"], track_rows
        )
        sections_phase3 = [
            {"title": "Evaluation Summary", "body": eval_summary},
            {"title": "Track Results", "body": track_table},
        ]
        async for ev in emit_phase(
            phase_key="phase3_complete",
            title="Phase 3: Parallel Evaluation Complete",
            markdown_sections=sections_phase3,
            data={
                "quotes": [q.model_dump() for q in parsed_quotes],
                "evaluations": [e.model_dump() for e in vendor_evaluations],
                "track_results": [
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
                ],
            },
        ):
            yield ev
        
        # ===================================================================
        # PHASE 4: COMPARISON & ANALYSIS
        # ===================================================================
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
        
        sections_phase4 = build_comparison_markdown(comparison_report)
        async for ev in emit_phase(
            phase_key="phase4_complete",
            title="Phase 4: Comparison Analysis Complete",
            markdown_sections=sections_phase4,
            data={"comparison_report": comparison_report.model_dump()},
        ):
            yield ev
        
        # ===================================================================
        # PHASE 5: NEGOTIATION STRATEGY
        # ===================================================================
        rfq_logger.info("Phase 5: Starting negotiation strategy", extra={"workflow_id": workflow_id})
        
        negotiation_recommendation = await self.negotiation_agent.generate_recommendation(
            comparison_report=comparison_report,
            quantity=requirements.quantity,
            workflow_id=workflow_id,
        )
        sub_blocks_phase5 = build_negotiation_sub_blocks(
            recommendation=negotiation_recommendation,
            quantity=requirements.quantity,
        )
        sections_phase5 = [
            {"title": "Target Vendor", "body": negotiation_recommendation.vendor_name},
        ]
        async for ev in emit_phase(
            phase_key="phase5_complete",
            title="Phase 5: Negotiation Strategy",
            markdown_sections=sections_phase5,
            data={"negotiation_recommendation": negotiation_recommendation.model_dump()},
            sub_blocks=sub_blocks_phase5,
        ):
            yield ev
        
        # ===================================================================
        # PHASE 6: HUMAN GATE (APPROVAL)
        # ===================================================================
        rfq_logger.info("Phase 6: Requesting human approval", extra={"workflow_id": workflow_id})
        
        human_gate_response = await self.human_gate_agent.request_human_input(
            recommendation=negotiation_recommendation
        )
        
        # Create approval request for human decision
        approval_request = ApprovalRequest(
            request_id=workflow_id,
            comparison_report=comparison_report,
            negotiation_recommendations=[negotiation_recommendation] if negotiation_recommendation else None,
            # Derive recommended vendor from top_ranked_vendors (first entry is best)
            recommended_vendor_id=(
                comparison_report.top_ranked_vendors[0].get("vendor_id")
                if comparison_report and comparison_report.top_ranked_vendors
                else None
            ),
            recommended_vendor_name=(
                comparison_report.top_ranked_vendors[0].get("vendor_name")
                if comparison_report and comparison_report.top_ranked_vendors
                else None
            ),
            decision_required_by=datetime.utcnow() + timedelta(hours=24),
        )
        
        # Save workflow state to thread for resumption (reuse existing thread_repo)
        if hasattr(self, '_thread_id') and self._thread_id:
            thread = await thread_repo.get(self._thread_id, "rfq-procurement")
            if thread:
                thread.workflow_state = {
                    "approval_request": approval_request.model_dump(),
                    "phase": "phase6_approval",
                    "comparison_report": comparison_report.model_dump() if comparison_report else None,
                    "negotiation_recommendation": negotiation_recommendation.model_dump() if negotiation_recommendation else None,
                    "requirements": requirements.model_dump(),
                    "buyer_name": buyer_name,
                    "buyer_email": buyer_email,
                    "workflow_id": workflow_id
                }
                await thread_repo.update(thread)
        
        if not wait_for_human:
            approval = ApprovalGateResponse(
                request_id=workflow_id,
                decision=ApprovalDecision.APPROVED,
                decision_maker=buyer_name,
            )
            sections_phase6 = [
                {"title": "Approval", "body": f"Auto-Approved by {buyer_name}. Decision: Proceed."},
            ]
            async for ev in emit_phase(
                phase_key="phase6_complete",
                title="Phase 6: Approval",
                markdown_sections=sections_phase6,
                data={"approval": approval.model_dump()},
            ):
                yield ev
        else:
            # Fetch the top vendor's normalized quote for display if available
            top_vendor_id = (
                comparison_report.top_ranked_vendors[0].get("vendor_id")
                if comparison_report and comparison_report.top_ranked_vendors
                else None
            )
            recommended_vendor = None
            if comparison_report and top_vendor_id:
                recommended_vendor = next(
                    (q for q in comparison_report.normalized_quotes if q.vendor_id == top_vendor_id),
                    None,
                )
            total_cost = (
                (negotiation_recommendation.suggested_unit_price or 0) * requirements.quantity
                if negotiation_recommendation
                else 0
            )
            sections_phase6_wait = [
                {
                    "title": "Approval Required",
                    "body": f"Recommended Vendor: {recommended_vendor.vendor_name if recommended_vendor else 'N/A'}\nTotal Cost: ${total_cost:,.2f}",
                }
            ]
            async for ev in emit_phase(
                phase_key="phase6_awaiting",
                title="Phase 6: Approval Required",
                markdown_sections=sections_phase6_wait,
                data={
                    "approval_request": approval_request.model_dump(),
                    "status": "awaiting_approval",
                    "human_gate_actions": True,
                },
            ):
                yield ev
            return
        
        # ===================================================================
        # PHASE 7: PURCHASE ORDER GENERATION
        # ===================================================================
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
        
        sections_phase7 = [
            {"title": "Purchase Order", "body": f"PO Number: {issued_po.po_number}\nStatus: {issued_po.status.upper()}"},
            {
                "title": "Order Details",
                "body": (
                    f"Product: {issued_po.product_name}\n"
                    f"Quantity: {issued_po.quantity:,} {issued_po.unit}\n"
                    f"Unit Price: ${issued_po.unit_price:.2f}\n"
                    f"Total Amount: ${issued_po.total_amount:,.2f}"
                ),
            },
            {
                "title": "Delivery & Payment",
                "body": (
                    f"Delivery Date: {issued_po.delivery_date.strftime('%Y-%m-%d')}\n"
                    f"Payment Terms: {issued_po.payment_terms}"
                ),
            },
        ]
        async for ev in emit_phase(
            phase_key="phase7_complete",
            title="Phase 7: Purchase Order Issued",
            markdown_sections=sections_phase7,
            data={
                "purchase_order": issued_po.model_dump(),
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
            },
        ):
            yield ev
        
        rfq_logger.info(
            f"RFQ Workflow complete: PO {issued_po.po_number} issued successfully",
            extra={"workflow_id": workflow_id},
        )
