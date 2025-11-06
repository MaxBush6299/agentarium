"""
RFQ Workflow Builder using agent_framework Workflow pattern.

Builds the complete 7-phase RFQ workflow graph:
Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 (Human Gate) → Phase 7

Usage:
    workflow = build_rfq_workflow(orchestrator_components)
    
    # Initial run
    async for event in workflow.run_stream(RFQStartMessage(...)):
        # Stream events to frontend
        
    # After human approval at Phase 6
    await workflow.send_responses_streaming({request_id: approval_decision})
"""

from typing import Dict, Any

from agent_framework import WorkflowBuilder, Workflow

from src.agents.workflows.rfq.orchestrators.rfq_workflow_executors import (
    PreprocessingExecutor,
    ParallelEvaluationExecutor,
    ComparisonExecutor,
    NegotiationExecutor,
    ApprovalGateExecutor,
    POGenerationExecutor,
    RFQStartMessage,
)
from src.agents.workflows.rfq.orchestrators.preprocessing_orchestrator import PreprocessingOrchestrator
from src.agents.workflows.rfq.orchestrators.parallel_evaluation_orchestrator import ParallelEvaluationOrchestrator
from src.agents.workflows.rfq.agents.comparison_analysis_agent import ComparisonAndAnalysisAgent
from src.agents.workflows.rfq.agents.negotiation_strategy_agent import NegotiationStrategyAgent
from src.agents.workflows.rfq.agents.purchase_order_agent import PurchaseOrderAgent
from src.agents.workflows.rfq.agents.human_gate_agent import HumanGateAgent
from src.agents.workflows.rfq.observability import rfq_logger


def build_rfq_workflow(
    preprocessing_orchestrator: PreprocessingOrchestrator,
    parallel_evaluation_orchestrator: ParallelEvaluationOrchestrator,
    rfq_submission_executor,
    quote_parsing_executor,
    comparison_agent: ComparisonAndAnalysisAgent,
    negotiation_agent: NegotiationStrategyAgent,
    human_gate_agent: HumanGateAgent,
    po_agent: PurchaseOrderAgent,
) -> Workflow:
    """
    Build the complete RFQ workflow graph using WorkflowBuilder.
    
    Creates 6 executors and connects them in sequence:
    
    START → PreprocessingExecutor → ParallelEvaluationExecutor → 
    ComparisonExecutor → NegotiationExecutor → ApprovalGateExecutor → 
    POGenerationExecutor → END
    
    The ApprovalGateExecutor uses ctx.request_info() to pause the workflow
    at Phase 6, waiting for human approval before proceeding to Phase 7.
    
    Args:
        preprocessing_orchestrator: Phase 2 preprocessing orchestrator
        parallel_evaluation_orchestrator: Phase 3 evaluation orchestrator
        rfq_submission_executor: Submits RFQs to vendors
        quote_parsing_executor: Parses vendor quotes
        comparison_agent: Phase 4 comparison agent
        negotiation_agent: Phase 5 negotiation agent
        human_gate_agent: Phase 6 human gate agent
        po_agent: Phase 7 purchase order agent
        
    Returns:
        Workflow instance ready to execute with run_stream()
    """
    rfq_logger.info("Building RFQ workflow graph")
    
    # Create executor instances
    preprocessing_exec = PreprocessingExecutor(preprocessing_orchestrator)
    parallel_eval_exec = ParallelEvaluationExecutor(
        parallel_evaluation_orchestrator,
        rfq_submission_executor,
        quote_parsing_executor
    )
    comparison_exec = ComparisonExecutor(comparison_agent)
    negotiation_exec = NegotiationExecutor(negotiation_agent)
    approval_gate_exec = ApprovalGateExecutor(human_gate_agent)
    po_generation_exec = POGenerationExecutor(po_agent)
    
    # Build workflow graph
    builder = WorkflowBuilder()
    
    # Set START node
    builder.set_start_executor(preprocessing_exec)
    
    # Connect Phase 2 → Phase 3
    builder.add_edge(preprocessing_exec, parallel_eval_exec)
    
    # Connect Phase 3 → Phase 4
    builder.add_edge(parallel_eval_exec, comparison_exec)
    
    # Connect Phase 4 → Phase 5
    builder.add_edge(comparison_exec, negotiation_exec)
    
    # Connect Phase 5 → Phase 6 (Human Gate)
    builder.add_edge(negotiation_exec, approval_gate_exec)
    
    # Connect Phase 6 → Phase 7
    builder.add_edge(approval_gate_exec, po_generation_exec)
    
    # Build and return workflow
    workflow = builder.build()
    
    rfq_logger.info("RFQ workflow graph built successfully")
    
    return workflow


def create_rfq_start_message(
    rfq_request,
    workflow_id: str,
    buyer_name: str = "Procurement Manager",
    buyer_email: str = "procurement@company.com",
    wait_for_human: bool = True
) -> RFQStartMessage:
    """
    Helper to create the initial workflow message.
    
    Args:
        rfq_request: RFQRequest from user
        workflow_id: Unique workflow ID
        buyer_name: Name of buyer/decision maker
        buyer_email: Email of buyer
        wait_for_human: If False, skip approval gate (testing)
        
    Returns:
        RFQStartMessage to start workflow
    """
    return RFQStartMessage(
        rfq_request=rfq_request,
        workflow_id=workflow_id,
        buyer_name=buyer_name,
        buyer_email=buyer_email,
        wait_for_human=wait_for_human
    )
