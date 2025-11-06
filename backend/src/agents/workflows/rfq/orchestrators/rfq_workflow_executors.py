"""
RFQ Workflow Executors using agent_framework Workflow pattern.

Each executor represents a phase in the RFQ procurement workflow:
- Phase 2: PreprocessingExecutor - Vendor qualification and requirements extraction
- Phase 3: ParallelEvaluationExecutor - Parallel evaluation tracks
- Phase 4: ComparisonExecutor - Vendor comparison and analysis
- Phase 5: NegotiationExecutor - Negotiation strategy generation
- Phase 6: ApprovalGateExecutor - Human approval gate (uses ctx.request_info)
- Phase 7: POGenerationExecutor - Purchase order generation and issuance

Each executor follows the pattern:
    @handler: Process incoming message, perform work, emit output message
    @response_handler: (Phase 6 only) Handle human responses and resume workflow
"""

from typing import Any, Dict, List
from datetime import datetime, timedelta

from agent_framework import (
    Executor,
    WorkflowContext,
    handler,
    response_handler,
)
from pydantic import BaseModel

from src.agents.workflows.rfq.models import (
    RFQRequest,
    ApprovalRequest,
    ApprovalGateResponse,
    ApprovalDecision,
)
from src.agents.workflows.rfq.orchestrators.preprocessing_orchestrator import PreprocessingOrchestrator
from src.agents.workflows.rfq.orchestrators.parallel_evaluation_orchestrator import ParallelEvaluationOrchestrator
from src.agents.workflows.rfq.agents.comparison_analysis_agent import ComparisonAndAnalysisAgent
from src.agents.workflows.rfq.agents.negotiation_strategy_agent import NegotiationStrategyAgent
from src.agents.workflows.rfq.agents.purchase_order_agent import PurchaseOrderAgent
from src.agents.workflows.rfq.agents.human_gate_agent import HumanGateAgent
from src.agents.workflows.rfq.observability import rfq_logger


# =============================================================================
# Message Types for Workflow Graph
# =============================================================================

class RFQStartMessage(BaseModel):
    """Initial message to start RFQ workflow."""
    rfq_request: RFQRequest
    workflow_id: str
    buyer_name: str = "Procurement Manager"
    buyer_email: str = "procurement@company.com"
    wait_for_human: bool = True


class Phase2CompleteMessage(BaseModel):
    """Output from preprocessing phase."""
    requirements: Dict[str, Any]
    vendors: List[Dict[str, Any]]
    workflow_id: str
    rfq_request: RFQRequest


class Phase3CompleteMessage(BaseModel):
    """Output from parallel evaluation phase."""
    quotes: List[Dict[str, Any]]
    evaluations: List[Dict[str, Any]]
    track_results: List[Dict[str, Any]]
    requirements: Dict[str, Any]
    vendors: List[Dict[str, Any]]
    workflow_id: str
    rfq_request: RFQRequest


class Phase4CompleteMessage(BaseModel):
    """Output from comparison phase."""
    comparison_report: Dict[str, Any]
    requirements: Dict[str, Any]
    vendors: List[Dict[str, Any]]
    workflow_id: str
    rfq_request: RFQRequest


class Phase5CompleteMessage(BaseModel):
    """Output from negotiation phase."""
    negotiation_recommendation: Dict[str, Any]
    comparison_report: Dict[str, Any]
    requirements: Dict[str, Any]
    vendors: List[Dict[str, Any]]
    workflow_id: str
    rfq_request: RFQRequest
    buyer_name: str
    buyer_email: str


class ApprovalResponseMessage(BaseModel):
    """Human approval response."""
    decision: str  # "approve" or "reject"
    decision_maker: str
    workflow_id: str


class Phase6CompleteMessage(BaseModel):
    """Output from approval gate."""
    approval: Dict[str, Any]
    negotiation_recommendation: Dict[str, Any]
    requirements: Dict[str, Any]
    vendors: List[Dict[str, Any]]
    workflow_id: str
    buyer_name: str
    buyer_email: str


class WorkflowCompleteMessage(BaseModel):
    """Final workflow output."""
    purchase_order: Dict[str, Any]
    workflow_id: str


# =============================================================================
# Phase 2: Preprocessing Executor
# =============================================================================

class PreprocessingExecutor(Executor):
    """Phase 2: Vendor qualification and requirements extraction."""
    
    def __init__(self, preprocessing_orchestrator: PreprocessingOrchestrator, executor_id: str = "preprocessing"):
        super().__init__(id=executor_id)
        self.preprocessing_orchestrator = preprocessing_orchestrator
    
    @handler
    async def preprocess_rfq(
        self,
        message: RFQStartMessage,
        ctx: WorkflowContext[Phase2CompleteMessage]
    ) -> None:
        """Execute preprocessing phase: extract requirements and qualify vendors."""
        rfq_logger.info(
            f"Phase 2: Starting preprocessing",
            extra={"workflow_id": message.workflow_id}
        )
        
        requirements, vendors = await self.preprocessing_orchestrator.preprocess(
            rfq_request=message.rfq_request,
            workflow_id=message.workflow_id,
        )
        
        # Send message to next executor
        await ctx.send_message(Phase2CompleteMessage(
            requirements=requirements.model_dump(),
            vendors=[v.model_dump() for v in vendors],
            workflow_id=message.workflow_id,
            rfq_request=message.rfq_request
        ))
    
    def _build_phase2_message(self, requirements, vendors, rfq_request) -> str:
        """Build detailed Phase 2 message."""
        message = f"""## Phase 2: Vendor Qualification Complete

**Product Requirements:**
- Product: {requirements.product_name}
- Category: {requirements.category}
- Quantity: {requirements.quantity:,} {requirements.unit}
- Required Certifications: {', '.join(requirements.required_certifications)}"""
        
        if rfq_request.budget_amount:
            message += f"\n- Budget: ${rfq_request.budget_amount:,.2f}"
        
        if requirements.desired_delivery_date:
            message += f"\n- Delivery Date: {requirements.desired_delivery_date.strftime('%Y-%m-%d')}"
        
        message += f"\n\n**Qualified Vendors ({len(vendors)}):**\n"
        
        for i, vendor in enumerate(vendors, 1):
            message += f"\n**{i}. {vendor.vendor_name}** (ID: {vendor.vendor_id})\n"
            message += f"   - Rating: {vendor.overall_rating}/5.0\n"
            message += f"   - Certifications: {', '.join(vendor.certifications) if vendor.certifications else 'None'}\n"
            message += f"   - Lead Time: {vendor.estimated_lead_time_days} days\n"
            message += f"   - Location: {vendor.country}\n"
            if vendor.previous_orders > 0:
                message += f"   - Previous Orders: {vendor.previous_orders}\n"
        
        return message


# =============================================================================
# Phase 3: Parallel Evaluation Executor
# =============================================================================

class ParallelEvaluationExecutor(Executor):
    """Phase 3: Submit RFQs, parse quotes, run parallel evaluation tracks."""
    
    def __init__(
        self,
        parallel_evaluation_orchestrator: ParallelEvaluationOrchestrator,
        rfq_submission_executor,
        quote_parsing_executor,
        executor_id: str = "parallel_evaluation"
    ):
        super().__init__(id=executor_id)
        self.parallel_evaluation_orchestrator = parallel_evaluation_orchestrator
        self.rfq_submission_executor = rfq_submission_executor
        self.quote_parsing_executor = quote_parsing_executor
    
    @handler
    async def evaluate_vendors(
        self,
        message: Phase2CompleteMessage,
        ctx: WorkflowContext[Phase3CompleteMessage]
    ) -> None:
        """Execute parallel evaluation phase."""
        rfq_logger.info(
            f"Phase 3: Starting parallel evaluation",
            extra={"workflow_id": message.workflow_id}
        )
        
        # Convert dict back to model instances
        from src.agents.workflows.rfq.models import ProductRequirements, VendorProfile
        requirements = ProductRequirements(**message.requirements)
        vendors = [VendorProfile(**v) for v in message.vendors]
        
        # 3.1: Submit RFQ to all vendors
        submissions = await self.rfq_submission_executor.submit_to_all_vendors(
            requirements=requirements,
            vendors=vendors,
            workflow_id=message.workflow_id,
        )
        
        # 3.2: Parse all quotes
        parsed_quotes = await self.quote_parsing_executor.execute(
            requirements=requirements,
            vendors=vendors,
            submissions=submissions,
            workflow_id=message.workflow_id,
        )
        
        # 3.3: Run 3 evaluation tracks in parallel
        vendor_evaluations, track_results = await self.parallel_evaluation_orchestrator.evaluate_all_vendors(
            requirements=requirements,
            vendors=vendors,
            quotes=parsed_quotes,
            workflow_id=message.workflow_id,
        )
        
        # Send message to next executor
        await ctx.send_message(Phase3CompleteMessage(
            quotes=[q.model_dump() for q in parsed_quotes],
            evaluations=[e.model_dump() for e in vendor_evaluations],
            track_results=[{
                "track_name": t.track_name,
                "vendor_id": t.vendor_id,
                "vendor_name": t.vendor_name,
                "score": t.score,
                "recommendation": t.recommendation,
                "risk_level": t.risk_level,
                "details": t.details,
            } for t in track_results],
            requirements=message.requirements,
            vendors=message.vendors,
            workflow_id=message.workflow_id,
            rfq_request=message.rfq_request
        ))
    
    def _build_phase3_message(self, parsed_quotes, track_results) -> str:
        """Build detailed Phase 3 message."""
        message = f"""## Phase 3: Parallel Evaluation Complete

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
            message += f"### {vendor_data['vendor_name']}\n"
            if quote:
                message += f"**Quote:** ${quote.unit_price:.2f}/unit (Total: ${quote.total_price:,.2f})\n\n"
            
            for track in vendor_data["tracks"]:
                risk_emoji = "🟢" if track.risk_level == "low" else "🟡" if track.risk_level == "medium" else "🔴"
                message += f"**{track.track_name}** {risk_emoji}\n"
                message += f"- Score: {track.score}/100\n"
                message += f"- Risk Level: {track.risk_level.upper()}\n"
                message += f"- Recommendation: {track.recommendation}\n"
                if track.details:
                    message += f"- Details: {track.details}\n"
                message += "\n"
        
        return message


# =============================================================================
# Phase 4: Comparison Executor
# =============================================================================

class ComparisonExecutor(Executor):
    """Phase 4: Vendor comparison and analysis."""
    
    def __init__(self, comparison_agent: ComparisonAndAnalysisAgent, executor_id: str = "comparison"):
        super().__init__(id=executor_id)
        self.comparison_agent = comparison_agent
    
    @handler
    async def compare_vendors(
        self,
        message: Phase3CompleteMessage,
        ctx: WorkflowContext[Phase4CompleteMessage]
    ) -> None:
        """Execute comparison phase."""
        rfq_logger.info(
            f"Phase 4: Starting comparison analysis",
            extra={"workflow_id": message.workflow_id}
        )
        
        # Convert back to model instances
        from src.agents.workflows.rfq.models import VendorProfile, QuoteResponse
        vendors = [VendorProfile(**v) for v in message.vendors]
        quotes = [QuoteResponse(**q) for q in message.quotes]
        
        # Merge evaluation tracks
        compliance_evals = {t["vendor_id"]: {"confidence": t["score"] / 100} for t in message.track_results if t["track_name"] == "Certification Compliance"}
        delivery_evals = {t["vendor_id"]: {"confidence": t["score"] / 100} for t in message.track_results if t["track_name"] == "Delivery Risk"}
        financial_evals = {t["vendor_id"]: {"confidence": t["score"] / 100} for t in message.track_results if t["track_name"] == "Financial Analysis"}
        
        merged_scores = await self.comparison_agent.merge_evaluation_tracks(
            vendors=vendors,
            compliance_evaluations=compliance_evals,
            delivery_evaluations=delivery_evals,
            financial_evaluations=financial_evals,
            workflow_id=message.workflow_id,
        )
        
        # Generate comparison report
        comparison_report = await self.comparison_agent.analyze_vendors(
            vendors=vendors,
            quotes=quotes,
            compliance_evaluations=compliance_evals,
            delivery_evaluations=delivery_evals,
            financial_evaluations=financial_evals,
            workflow_id=message.workflow_id,
        )
        
        # Send message to next executor
        await ctx.send_message(Phase4CompleteMessage(
            comparison_report=comparison_report.model_dump(),
            requirements=message.requirements,
            vendors=message.vendors,
            workflow_id=message.workflow_id,
            rfq_request=message.rfq_request
        ))
    
    def _build_phase4_message(self, comparison_report) -> str:
        """Build detailed Phase 4 message."""
        message = f"""## Phase 4: Comparison Analysis Complete

**Vendor Rankings:**

"""
        
        for i, ranked_vendor in enumerate(comparison_report.top_ranked_vendors, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"**{i}.**"
            vendor_name = ranked_vendor.get('vendor_name', 'Unknown')
            score = ranked_vendor.get('score', 0)
            total_price = ranked_vendor.get('total_price', 0)
            recommendation = ranked_vendor.get('recommendation', '')
            
            message += f"{medal} **{vendor_name}**\n"
            message += f"   - Score: {score:.1f}/5.0\n"
            message += f"   - Total Price: ${total_price:,.2f}\n"
            message += f"   - Status: {recommendation}\n"
            message += "\n"
        
        if hasattr(comparison_report, 'recommendations') and comparison_report.recommendations:
            message += f"**Analysis:**\n{comparison_report.recommendations}\n"
        
        return message


# =============================================================================
# Phase 5: Negotiation Executor
# =============================================================================

class NegotiationExecutor(Executor):
    """Phase 5: Negotiation strategy generation."""
    
    def __init__(self, negotiation_agent: NegotiationStrategyAgent, executor_id: str = "negotiation"):
        super().__init__(id=executor_id)
        self.negotiation_agent = negotiation_agent
    
    @handler
    async def generate_negotiation_strategy(
        self,
        message: Phase4CompleteMessage,
        ctx: WorkflowContext[Phase5CompleteMessage]
    ) -> None:
        """Execute negotiation strategy phase."""
        rfq_logger.info(
            f"Phase 5: Starting negotiation strategy",
            extra={"workflow_id": message.workflow_id}
        )
        
        # Convert back to model instances
        from src.agents.workflows.rfq.models import ComparisonReport, ProductRequirements
        comparison_report = ComparisonReport(**message.comparison_report)
        requirements = ProductRequirements(**message.requirements)
        
        negotiation_recommendation = await self.negotiation_agent.generate_recommendation(
            comparison_report=comparison_report,
            quantity=requirements.quantity,
            workflow_id=message.workflow_id,
        )
        
        # Send message to next executor
        await ctx.send_message(Phase5CompleteMessage(
            negotiation_recommendation=negotiation_recommendation.model_dump(),
            comparison_report=message.comparison_report,
            requirements=message.requirements,
            vendors=message.vendors,
            workflow_id=message.workflow_id,
            rfq_request=message.rfq_request,
            buyer_name="Procurement Manager",
            buyer_email="procurement@company.com"
        ))
    
    def _build_phase5_message(self, negotiation_recommendation, requirements) -> str:
        """Build detailed Phase 5 message."""
        message = f"""## Phase 5: Negotiation Strategy

**Target Vendor:** {negotiation_recommendation.vendor_name}

**Negotiation Strategy:**

{negotiation_recommendation.negotiation_strategy}

**Expected Outcome:**

{negotiation_recommendation.expected_outcome}
"""
        
        if negotiation_recommendation.suggested_unit_price:
            message += f"\n**Pricing Recommendation:**\n"
            message += f"- Suggested Unit Price: ${negotiation_recommendation.suggested_unit_price:.2f}\n"
            message += f"- Total for {requirements.quantity:,} units: ${negotiation_recommendation.suggested_unit_price * requirements.quantity:,.2f}\n"
        
        if negotiation_recommendation.leverage_points:
            message += f"\n**Leverage Points:**\n"
            for i, point in enumerate(negotiation_recommendation.leverage_points, 1):
                message += f"{i}. {point}\n"
        
        if negotiation_recommendation.fallback_options:
            message += f"\n**Fallback Options:**\n"
            for i, option in enumerate(negotiation_recommendation.fallback_options, 1):
                message += f"{i}. {option}\n"
        
        return message


# =============================================================================
# Phase 6: Approval Gate Executor (HUMAN-IN-THE-LOOP)
# =============================================================================

class ApprovalGateExecutor(Executor):
    """
    Phase 6: Human approval gate using ctx.request_info().
    
    This is the critical executor that PAUSES the workflow and waits for
    human approval before proceeding to Phase 7 (PO generation).
    """
    
    def __init__(self, human_gate_agent: HumanGateAgent, executor_id: str = "approval_gate"):
        super().__init__(id=executor_id)
        self.human_gate_agent = human_gate_agent
        self._pending_approval_data = {}  # Store Phase5 data for response_handler
    
    @handler
    async def request_approval(
        self,
        message: Phase5CompleteMessage,
        ctx: WorkflowContext[Phase6CompleteMessage]
    ) -> None:
        """
        Request human approval and PAUSE workflow until response received.
        
        This uses ctx.request_info() which is the KEY to pausing the workflow.
        The workflow will become IDLE and wait for send_responses_streaming().
        """
        rfq_logger.info(
            f"Phase 6: Requesting human approval",
            extra={"workflow_id": message.workflow_id}
        )
        
        # Convert back to model instances
        from src.agents.workflows.rfq.models import (
            ComparisonReport,
            NegotiationRecommendation,
            ProductRequirements
        )
        comparison_report = ComparisonReport(**message.comparison_report)
        negotiation_recommendation = NegotiationRecommendation(**message.negotiation_recommendation)
        requirements = ProductRequirements(**message.requirements)
        
        # Extract recommended vendor
        recommended_vendor_id = None
        recommended_vendor_name = None
        if comparison_report and comparison_report.top_ranked_vendors:
            top_vendor = comparison_report.top_ranked_vendors[0]
            recommended_vendor_id = top_vendor.get('vendor_id')
            recommended_vendor_name = top_vendor.get('vendor_name')
        
        # Create approval request
        approval_request = ApprovalRequest(
            request_id=message.workflow_id,
            comparison_report=comparison_report,
            negotiation_recommendations=[negotiation_recommendation] if negotiation_recommendation else None,
            recommended_vendor_id=recommended_vendor_id,
            recommended_vendor_name=recommended_vendor_name,
            decision_required_by=datetime.utcnow() + timedelta(hours=24),
        )
        
        total_cost = (negotiation_recommendation.suggested_unit_price or 0) * requirements.quantity if negotiation_recommendation else 0
        
        # Store data for response_handler
        self._pending_approval_data[message.workflow_id] = {
            "negotiation_recommendation": message.negotiation_recommendation,
            "requirements": message.requirements,
            "vendors": message.vendors,
            "buyer_name": message.buyer_name,
            "buyer_email": message.buyer_email,
        }
        
        # 🚨 THIS IS THE KEY: ctx.request_info() PAUSES THE WORKFLOW
        # Workflow becomes IDLE and waits for send_responses_streaming()
        await ctx.request_info(
            request_data=approval_request.model_dump(),
            response_type=str  # Expected response type
        )
    
    @response_handler
    async def handle_approval_response(
        self,
        original_request: dict,
        response: str,
        ctx: WorkflowContext[Phase6CompleteMessage]
    ) -> None:
        """
        Handle the human approval response and resume workflow.
        
        This method is called automatically when send_responses_streaming()
        provides the approval decision.
        
        Args:
            original_request: The dict passed to ctx.request_info(request_data=...)
            response: The str response from send_responses_streaming()
            ctx: Workflow context for sending messages
        """
        # Extract workflow_id from original request
        workflow_id = original_request.get("request_id", "")
        
        rfq_logger.info(
            f"Phase 6: Received approval response: {response}",
            extra={"workflow_id": workflow_id}
        )
        
        # Retrieve stored data from handler
        stored_data = self._pending_approval_data.get(workflow_id, {})
        
        # Create approval response
        approval = ApprovalGateResponse(
            request_id=workflow_id,
            decision=ApprovalDecision.APPROVED if response == "approve" else ApprovalDecision.REJECTED,
            decision_maker=stored_data.get("buyer_name", "Procurement Manager"),
        )
        
        # Send message to next executor with stored Phase5 data
        await ctx.send_message(Phase6CompleteMessage(
            approval=approval.model_dump(),
            negotiation_recommendation=stored_data.get("negotiation_recommendation", {}),
            requirements=stored_data.get("requirements", {}),
            vendors=stored_data.get("vendors", []),
            workflow_id=workflow_id,
            buyer_name=stored_data.get("buyer_name", "Procurement Manager"),
            buyer_email=stored_data.get("buyer_email", "procurement@company.com")
        ))

        # Emit a lightweight phase6_complete event dict for external listeners (frontend)
        # NOTE: WorkflowContext in current agent_framework may not expose an emit method.
        # If event broadcasting is needed, integrate via higher-level orchestrator or API layer.
        
        # Clean up stored data
        self._pending_approval_data.pop(workflow_id, None)


# =============================================================================
# Phase 7: Purchase Order Generation Executor
# =============================================================================

class POGenerationExecutor(Executor):
    """Phase 7: Purchase order generation and issuance."""
    
    def __init__(self, po_agent: PurchaseOrderAgent, executor_id: str = "po_generation"):
        super().__init__(id=executor_id)
        self.po_agent = po_agent
    
    @handler
    async def generate_purchase_order(
        self,
        message: Phase6CompleteMessage,
        ctx: WorkflowContext[WorkflowCompleteMessage]
    ) -> None:
        """Execute PO generation phase."""
        rfq_logger.info(
            f"Phase 7: Generating purchase order",
            extra={"workflow_id": message.workflow_id}
        )
        
        # Convert back to model instances
        from src.agents.workflows.rfq.models import (
            ApprovalGateResponse,
            NegotiationRecommendation,
            ProductRequirements,
            VendorProfile
        )
        approval = ApprovalGateResponse(**message.approval)
        negotiation_recommendation = NegotiationRecommendation(**message.negotiation_recommendation)
        requirements = ProductRequirements(**message.requirements)
        vendors = [VendorProfile(**v) for v in message.vendors]
        
        # Find target vendor
        target_vendor = next(
            (v for v in vendors if v.vendor_id == negotiation_recommendation.vendor_id),
            vendors[0],
        )
        
        # Generate purchase order
        purchase_order = await self.po_agent.generate_purchase_order(
            recommendation=negotiation_recommendation,
            approval=approval,
            requirements=requirements,
            vendor=target_vendor,
            workflow_id=message.workflow_id,
            buyer_name=message.buyer_name,
            buyer_email=message.buyer_email,
        )
        
        # Issue purchase order
        issued_po = await self.po_agent.issue_purchase_order(
            purchase_order=purchase_order,
        )
        
        # Send final message
        await ctx.send_message(WorkflowCompleteMessage(
            purchase_order=issued_po.model_dump(),
            workflow_id=message.workflow_id
        ))
        
        rfq_logger.info(
            f"RFQ Workflow complete: PO {issued_po.po_number} issued successfully",
            extra={"workflow_id": message.workflow_id},
        )

        # Emit phase7_complete event for real-time UI without waiting for model message consumption
        # See note above regarding ctx.emit availability.
