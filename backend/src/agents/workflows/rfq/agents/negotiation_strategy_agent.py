"""
Phase 5: Negotiation Strategy Agent

Analyzes comparison reports to identify negotiation opportunities.
Uses LLM to generate expert negotiation strategies and counter-offers.
AI agent operates as a senior purchasing manager and expert contract negotiator.
"""

import uuid
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from src.agents.base import DemoBaseAgent
from src.agents.workflows.rfq.models import (
    ComparisonReport,
    NormalizedQuote,
    NegotiationRecommendation,
)
from src.agents.workflows.rfq.observability import rfq_logger


class NegotiationStrategyAgent(DemoBaseAgent):
    """
    Expert contract negotiator using LLM to generate strategies.
    
    Operates as a senior purchasing manager with deep expertise in:
    - Vendor negotiation and relationship management
    - Contract law and terms optimization
    - Supply chain risk assessment
    - Cost and timeline optimization
    
    Input: ComparisonReport with top vendors and their quotes
    Output: NegotiationRecommendation with AI-generated strategy
    
    The agent analyzes vendor positioning, market conditions, and leverage
    points to generate comprehensive, expert-level negotiation strategies.
    """
    
    def __init__(self):
        """Initialize negotiation strategy agent."""
        instructions = """You are a senior purchasing manager and expert contract negotiator for a large multinational business.
Your role is to analyze vendor quotes and competitive bids to extract maximum value while maintaining strong supplier relationships.

Your expertise includes:
- Identifying pricing anomalies and market positioning
- Recognizing vendor leverage points and willingness to negotiate
- Crafting negotiation strategies that maximize savings while preserving relationships
- Understanding total cost of ownership beyond unit price
- Risk assessment and vendor stability evaluation
- Market knowledge and competitive benchmarking

When analyzing vendor quotes, you:
1. Identify the target vendor's strategic position in the market
2. Recognize their pricing leverage (premium vs. competitive)
3. Assess their delivery capabilities and supply chain risk
4. Determine optimal negotiation tactics based on vendor profile
5. Suggest specific counter-offers backed by market data
6. Recommend fallback strategies and walk-away thresholds
7. Provide talking points for the negotiation team
8. Quantify the financial impact of potential negotiations

Your recommendations should be specific, actionable, and backed by clear reasoning.
Focus on win-win outcomes that strengthen long-term supplier relationships while protecting company interests."""
        
        super().__init__(
            name="Negotiation Strategy Agent",
            model="gpt-4o",
            tools=[],
            instructions=instructions,
        )
    
    async def generate_recommendation(
        self,
        comparison_report: ComparisonReport,
        quantity: int = 100,
        workflow_id: Optional[str] = None,
    ) -> NegotiationRecommendation:
        """
        Generate AI-powered negotiation recommendation using LLM expertise.
        
        Args:
            comparison_report: ComparisonReport from Phase 4
            quantity: Order quantity for price calculations
            workflow_id: Workflow identifier for logging
        
        Returns: NegotiationRecommendation with AI-generated strategy
        """
        rfq_logger.info(
            f"Starting LLM-based negotiation analysis for comparison report {comparison_report.report_id}",
            workflow_id=workflow_id,
        )
        
        if not comparison_report.normalized_quotes or not comparison_report.top_ranked_vendors:
            rfq_logger.error(
                "Cannot generate recommendations: missing quotes or top vendors",
                workflow_id=workflow_id,
            )
            raise ValueError("Comparison report missing normalized_quotes or top_ranked_vendors")
        
        # Get top vendor (highest ranked)
        top_vendor = comparison_report.top_ranked_vendors[0]
        top_vendor_id = top_vendor["vendor_id"]
        
        # Find the normalized quote for the top vendor
        top_quote = next(
            (q for q in comparison_report.normalized_quotes if q.vendor_id == top_vendor_id),
            None,
        )
        
        if not top_quote:
            rfq_logger.error(
                f"Top vendor {top_vendor_id} not found in normalized_quotes",
                workflow_id=workflow_id,
            )
            raise ValueError(f"Quote not found for top vendor {top_vendor_id}")
        
        # Build comprehensive context for LLM analysis
        analysis_context = self._build_analysis_context(
            top_vendor=top_vendor,
            top_quote=top_quote,
            all_quotes=comparison_report.normalized_quotes,
            all_vendors=comparison_report.top_ranked_vendors,
            quantity=quantity,
        )
        
        # Use LLM to generate expert negotiation strategy
        strategy_prompt = self._build_strategy_prompt(analysis_context)
        
        try:
            # Get LLM response with negotiation strategy
            response = await self.run(strategy_prompt)
            strategy_analysis = self._parse_llm_response(response.text if hasattr(response, 'text') else str(response))
        except Exception as e:
            rfq_logger.error(
                f"LLM strategy generation failed: {str(e)}, using fallback strategy",
                workflow_id=workflow_id,
            )
            strategy_analysis = self._generate_fallback_strategy(analysis_context)
        
        # Extract specific recommendations from strategy analysis
        target_price = strategy_analysis.get("suggested_unit_price", top_quote.unit_price * 0.95)
        cost_savings = (top_quote.unit_price - target_price) * quantity
        
        # Extract fallback options - handle both string list and dict list formats
        fallback_opts = strategy_analysis.get("fallback_options", [])
        if fallback_opts and isinstance(fallback_opts[0], dict):
            # If LLM returned dicts with 'option' key, extract the strings
            fallback_opts = [opt.get("option", str(opt)) for opt in fallback_opts]
        
        # Create comprehensive recommendation
        recommendation = NegotiationRecommendation(
            recommendation_id=f"nego-{uuid.uuid4().hex[:8]}",
            vendor_id=top_vendor_id,
            vendor_name=top_vendor["vendor_name"],
            leverage_points=strategy_analysis.get("leverage_points", []),
            suggested_unit_price=target_price,
            suggested_payment_terms=strategy_analysis.get("payment_terms", "Net 45"),
            suggested_delivery_date=strategy_analysis.get("delivery_date", top_quote.delivery_date),
            negotiation_strategy=strategy_analysis.get(
                "strategy",
                "Expert contract negotiation recommended"
            ),
            expected_outcome=strategy_analysis.get(
                "expected_outcome",
                f"Target: ${target_price:.2f}/unit, Potential savings: ${cost_savings:,.2f}"
            ),
            fallback_options=fallback_opts,
            estimated_cost_savings=max(0, cost_savings),
            notes=strategy_analysis.get(
                "notes",
                f"Analysis based on {len(comparison_report.normalized_quotes)} competing vendors. "
                f"Top vendor achieves score of {top_vendor['score']:.1f}/5.0"
            ),
        )
        
        rfq_logger.info(
            f"AI-generated negotiation recommendation: {recommendation.recommendation_id} "
            f"for {recommendation.vendor_name}, potential savings ${recommendation.estimated_cost_savings:,.2f}",
            workflow_id=workflow_id,
        )
        
        return recommendation
    
    def _build_analysis_context(
        self,
        top_vendor: Dict[str, Any],
        top_quote: NormalizedQuote,
        all_quotes: List[NormalizedQuote],
        all_vendors: List[Dict[str, Any]],
        quantity: int,
    ) -> Dict[str, Any]:
        """Build comprehensive context for LLM analysis."""
        
        # Calculate market benchmarks
        unit_prices = [q.unit_price for q in all_quotes]
        avg_price = sum(unit_prices) / len(unit_prices) if unit_prices else top_quote.unit_price
        min_price = min(unit_prices) if unit_prices else top_quote.unit_price
        max_price = max(unit_prices) if unit_prices else top_quote.unit_price
        
        lead_times = [q.lead_time_days for q in all_quotes]
        avg_lead_time = sum(lead_times) / len(lead_times) if lead_times else top_quote.lead_time_days
        
        return {
            "top_vendor": {
                "name": top_vendor["vendor_name"],
                "score": top_vendor["score"],
                "recommendation": top_vendor["recommendation"],
            },
            "top_quote": {
                "unit_price": top_quote.unit_price,
                "total_price": top_quote.total_price,
                "delivery_date": top_quote.delivery_date.isoformat() if top_quote.delivery_date else None,
                "lead_time_days": top_quote.lead_time_days,
                "price_with_bulk": top_quote.price_per_unit_with_bulk,
            },
            "market_benchmarks": {
                "average_unit_price": avg_price,
                "minimum_unit_price": min_price,
                "maximum_unit_price": max_price,
                "price_range": max_price - min_price,
                "average_lead_time": avg_lead_time,
                "num_vendors": len(all_quotes),
            },
            "pricing_analysis": {
                "price_vs_average": ((top_quote.unit_price - avg_price) / avg_price) * 100,
                "price_vs_best": ((top_quote.unit_price - min_price) / min_price) * 100,
                "current_total_cost": top_quote.unit_price * quantity,
                "cost_at_average": avg_price * quantity,
                "cost_at_minimum": min_price * quantity,
            },
            "delivery_analysis": {
                "vendor_lead_time": top_quote.lead_time_days,
                "market_average_lead_time": avg_lead_time,
                "best_available_lead_time": min(lead_times) if lead_times else None,
            },
            "alternative_vendors": [
                {
                    "name": v["vendor_name"],
                    "score": v["score"],
                    "recommendation": v["recommendation"],
                }
                for v in all_vendors[1:]
            ],
            "quantity": quantity,
        }
    
    def _build_strategy_prompt(self, context: Dict[str, Any]) -> str:
        """Build detailed prompt for LLM negotiation strategy generation."""
        
        return f"""
Analyze this vendor negotiation scenario and provide a comprehensive expert strategy:

TARGET VENDOR: {context['top_vendor']['name']}
- Quality Score: {context['top_vendor']['score']:.1f}/5.0
- Recommendation: {context['top_vendor']['recommendation']}

PRICING ANALYSIS:
- Vendor's Unit Price: ${context['top_quote']['unit_price']:.2f}
- Market Average: ${context['market_benchmarks']['average_unit_price']:.2f}
- Best Available Price: ${context['market_benchmarks']['minimum_unit_price']:.2f}
- Vendor vs Average: {context['pricing_analysis']['price_vs_average']:+.1f}%
- Vendor vs Best: {context['pricing_analysis']['price_vs_best']:+.1f}%
- Total Cost for {context['quantity']} units: ${context['top_quote']['total_price']:,.2f}

DELIVERY ANALYSIS:
- Vendor's Lead Time: {context['top_quote']['lead_time_days']} days
- Market Average: {context['delivery_analysis']['market_average_lead_time']:.0f} days
- Best Available: {context['delivery_analysis']['best_available_lead_time']} days
- Delivery Date: {context['top_quote']['delivery_date']}

ALTERNATIVE OPTIONS:
{chr(10).join([f"- {v['name']}: Score {v['score']:.1f}/5.0, {v['recommendation']}" for v in context['alternative_vendors']])}

As a senior purchasing manager and expert contract negotiator, provide:

1. VENDOR POSITIONING: Where does this vendor sit in the market? Are they premium, competitive, or distressed?

2. LEVERAGE POINTS: What negotiation leverage do we have? Consider:
   - Competitive alternatives available
   - Pricing vs market benchmarks
   - Delivery timeline flexibility
   - Volume commitment opportunities
   - Long-term partnership potential

3. NEGOTIATION STRATEGY: What's our recommended approach?
   - Should we negotiate aggressively, moderately, or conservatively?
   - What's our opening position and walk-away threshold?
   - How can we frame negotiations to maintain the relationship?

4. SPECIFIC COUNTER-OFFERS:
   - Target unit price (with justification)
   - Suggested payment terms (e.g., Net 45, Net 60)
   - Delivery date acceleration request (if applicable)
   - Volume commitment or multi-order opportunities

5. TALKING POINTS: What should our negotiation team emphasize?
   - Market data points
   - Competitive positioning
   - Value of long-term partnership

6. FALLBACK STRATEGY: If the vendor won't negotiate:
   - Should we escalate further or accept their quote?
   - Should we pivot to alternative vendors?
   - What's the financial impact?

7. RISK ASSESSMENT: Any red flags or opportunities?

Respond with actionable, specific recommendations backed by the data above.
Format your response as JSON with keys: leverage_points (list), suggested_unit_price (float), 
payment_terms (str), delivery_acceleration_days (int), strategy (str), expected_outcome (str), 
talking_points (list), fallback_options (list), notes (str)
"""
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured recommendation data."""
        try:
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Fallback: extract key information from text
        return {
            "leverage_points": ["Competitive market conditions", "Alternative vendors available"],
            "suggested_unit_price": None,
            "payment_terms": "Net 45",
            "strategy": response[:500] if response else "Expert negotiation recommended",
            "expected_outcome": "Negotiations expected to yield cost savings and favorable terms",
            "fallback_options": ["Consider alternative vendors if negotiation fails"],
            "notes": "Strategy generated from LLM analysis of market conditions",
        }
    
    def _generate_fallback_strategy(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback strategy if LLM fails."""
        
        price_delta = context["pricing_analysis"]["price_vs_average"]
        lead_time_delta = context["delivery_analysis"]["vendor_lead_time"] - context["delivery_analysis"]["market_average_lead_time"]
        
        leverage_points = []
        if price_delta > 5:
            leverage_points.append(f"Vendor pricing is {price_delta:.1f}% above market - negotiate down")
        
        if lead_time_delta > 3:
            leverage_points.append(f"Longer delivery ({lead_time_delta:.0f} days) - request acceleration or discount")
        
        leverage_points.append("Competitive alternatives available from other qualified vendors")
        
        return {
            "leverage_points": leverage_points,
            "suggested_unit_price": context["market_benchmarks"]["average_unit_price"] * 0.97,
            "payment_terms": "Net 45",
            "delivery_date": None,
            "strategy": "Request 3-5% price reduction based on competitive market analysis and volume commitment potential",
            "expected_outcome": f"Target savings of ${(context['top_quote']['unit_price'] - context['market_benchmarks']['average_unit_price']) * context['quantity']:,.0f} on this order",
            "fallback_options": [
                f"{v['name']} (Score: {v['score']:.1f}/5.0)"
                for v in context["alternative_vendors"]
            ],
            "notes": "Fallback strategy based on market benchmarking",
        }

