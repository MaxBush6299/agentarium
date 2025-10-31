"""
Phase 6 Orchestrator: Integrates HumanGateAgent into the RFQ workflow.
Pipes negotiation recommendations through the human gate for approval before finalization.
"""
import asyncio
from src.agents.workflows.rfq.agents.negotiation_strategy_agent import NegotiationStrategyAgent
from src.agents.workflows.rfq.agents.human_gate_agent import HumanGateAgent

class Phase6NegotiationOrchestrator:
    def __init__(self):
        self.negotiation_agent = NegotiationStrategyAgent()
        self.human_gate_agent = HumanGateAgent()

    async def run(self, comparison_report, quantity, workflow_id):
        # Step 1: Generate negotiation recommendation
        recommendation = await self.negotiation_agent.generate_recommendation(
            comparison_report=comparison_report,
            quantity=quantity,
            workflow_id=workflow_id,
        )
        # Step 2: Pass through human gate
        final_recommendation = await self.human_gate_agent.request_human_input(recommendation)
        if final_recommendation is None:
            print("Workflow stopped by human gate.")
            return None
        print("Final recommendation approved and ready for next phase.")
        return final_recommendation
