"""
RFQ Workflow Configuration

Configuration management for the parallel RFQ workflow including agent settings,
merge strategies, evaluation parameters, and thresholds.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class MergeStrategy(str, Enum):
    """Strategy for merging parallel evaluation results."""
    CONSOLIDATE = "consolidate"  # Combine all results into unified analysis
    WEIGHTED_SCORE = "weighted_score"  # Weighted combination of scores
    CONSENSUS = "consensus"  # Consensus-based approach


class NegotiationStrategy(str, Enum):
    """Negotiation strategy types."""
    AGGRESSIVE = "aggressive"  # Push hard for best terms
    MODERATE = "moderate"  # Balanced approach
    CONSERVATIVE = "conservative"  # Accept reasonable terms
    AUTOMATED = "automated"  # Let LLM handle negotiation


@dataclass
class EvaluationWeights:
    """Weights for vendor evaluation scoring."""
    price_weight: float = 0.35  # Price is 35% of score
    delivery_weight: float = 0.25  # Delivery is 25%
    quality_weight: float = 0.25  # Quality/certifications is 25%
    vendor_rating_weight: float = 0.15  # Vendor history is 15%
    
    def validate(self) -> bool:
        """Ensure weights sum to 1.0."""
        total = (
            self.price_weight
            + self.delivery_weight
            + self.quality_weight
            + self.vendor_rating_weight
        )
        return abs(total - 1.0) < 0.01


@dataclass
class TimeoutConfig:
    """Timeout settings for various workflow stages."""
    vendor_response_timeout_seconds: int = 120  # Wait up to 2 minutes for vendor response
    human_approval_timeout_hours: int = 24  # Wait up to 24 hours for approval
    negotiation_timeout_seconds: int = 60  # Give negotiation 1 minute
    po_delivery_timeout_hours: int = 2  # PO must be delivered within 2 hours


@dataclass
class ApprovalThresholds:
    """Thresholds for automatic vs. manual approval."""
    min_price_variance_for_manual_review: float = 0.15  # Flag if price > 15% above average
    min_vendor_rating_for_auto_approval: float = 4.5  # Auto-approve if vendor rating >= 4.5
    risk_level_requiring_approval: str = "medium"  # Require approval if risk is medium+
    max_vendors_to_present: int = 3  # Show top 3 vendors for approval


@dataclass
class ParallelAgentConfig:
    """Configuration for individual parallel evaluation agents."""
    agent_id: str
    agent_name: str
    agent_type: str  # "review", "delivery", "financial"
    description: str
    enabled: bool = True
    timeout_seconds: int = 60
    retry_count: int = 3


@dataclass
class RFQWorkflowConfig:
    """
    Master configuration for RFQ parallel workflow.
    
    Centralizes all settings for the multi-agent orchestration.
    """
    
    # ========================================================================
    # Workflow Identity
    # ========================================================================
    workflow_name: str = "parallel_rfq_workflow"
    workflow_version: str = "1.0.0"
    
    # ========================================================================
    # Parallel Evaluation Agents
    # ========================================================================
    parallel_agents: List[ParallelAgentConfig] = field(default_factory=lambda: [
        ParallelAgentConfig(
            agent_id="review_agent",
            agent_name="VendorReviewAgent",
            agent_type="review",
            description="Evaluates vendor reviews, certifications, and compliance",
            timeout_seconds=60,
        ),
        ParallelAgentConfig(
            agent_id="delivery_agent",
            agent_name="DeliveryAgent",
            agent_type="delivery",
            description="Evaluates delivery feasibility and logistics",
            timeout_seconds=60,
        ),
        ParallelAgentConfig(
            agent_id="financial_agent",
            agent_name="FinancialTermsAgent",
            agent_type="financial",
            description="Evaluates pricing and payment terms",
            timeout_seconds=60,
        ),
    ])
    
    # ========================================================================
    # Merge and Aggregation Settings
    # ========================================================================
    merge_strategy: MergeStrategy = MergeStrategy.WEIGHTED_SCORE
    evaluation_weights: EvaluationWeights = field(default_factory=EvaluationWeights)
    
    # ========================================================================
    # Negotiation Settings
    # ========================================================================
    negotiation_enabled: bool = True
    negotiation_strategy: NegotiationStrategy = NegotiationStrategy.MODERATE
    
    # Negotiation parameters
    acceptable_price_variance: float = 0.10  # Accept prices within ±10% of best
    max_negotiation_rounds: int = 3  # Max 3 rounds of back-and-forth
    negotiation_leverage_factors: List[str] = field(default_factory=lambda: [
        "bulk_volume_commitment",
        "long_term_contract",
        "multi_vendor_split",
        "seasonal_demand",
        "payment_acceleration",
        "extended_terms",
    ])
    
    # ========================================================================
    # Approval Gate Settings
    # ========================================================================
    approval_gate_enabled: bool = True
    approval_thresholds: ApprovalThresholds = field(default_factory=ApprovalThresholds)
    
    # Approval decision options
    approval_decision_options: List[str] = field(default_factory=lambda: [
        "approved",
        "rejected",
        "renegotiate",
        "more_info",
        "abort",
    ])
    
    # ========================================================================
    # Timeouts
    # ========================================================================
    timeouts: TimeoutConfig = field(default_factory=TimeoutConfig)
    
    # ========================================================================
    # Fallback and Recovery
    # ========================================================================
    enable_fallback_vendors: bool = True
    fallback_vendor_count: int = 2  # Keep 2 backup vendors available
    
    # Retry logic
    max_retries_on_failure: int = 2
    retry_backoff_multiplier: float = 1.5  # Exponential backoff: 1s, 1.5s, 2.25s
    
    # ========================================================================
    # Logging and Observability
    # ========================================================================
    enable_detailed_logging: bool = True
    enable_trace_collection: bool = True
    log_level: str = "INFO"
    
    # Event tracking
    track_all_events: bool = True
    track_vendor_communications: bool = True
    track_approval_decisions: bool = True
    
    # ========================================================================
    # Persistence Settings
    # ========================================================================
    persist_intermediate_states: bool = True
    state_checkpoint_stages: List[str] = field(default_factory=lambda: [
        "product_requirements",
        "vendor_qualification",
        "rfq_submissions",
        "quote_responses",
        "evaluation_complete",
        "comparison_complete",
        "approval_gate",
        "po_generated",
    ])
    
    # ========================================================================
    # Data Processing Settings
    # ========================================================================
    quote_parsing_strict_mode: bool = False  # Allow partial quote data if False
    normalize_prices_to_currency: str = "USD"  # Convert all prices to this currency
    
    # Bulk discount handling
    apply_bulk_discounts: bool = True
    discount_tiers: Dict[int, float] = field(default_factory=lambda: {
        100: 0.05,    # 5% discount for 100+ units
        500: 0.10,    # 10% discount for 500+ units
        1000: 0.15,   # 15% discount for 1000+ units
    })
    
    # ========================================================================
    # Risk Management
    # ========================================================================
    risk_flags_to_monitor: List[str] = field(default_factory=lambda: [
        "single_source_risk",
        "certification_missing",
        "delivery_tight",
        "price_unusual",
        "vendor_rating_low",
        "compliance_concerns",
        "payment_term_risky",
        "geographic_risk",
    ])
    
    critical_risk_flags: List[str] = field(default_factory=lambda: [
        "certification_missing",
        "compliance_failed",
        "vendor_blacklisted",
    ])
    
    # ========================================================================
    # Vendor Filtering
    # ========================================================================
    min_vendor_rating_for_consideration: float = 2.5  # 2.5+ stars minimum
    require_all_certifications: bool = True  # All required certs must be present
    max_lead_time_variance: float = 0.20  # Accept lead times up to 20% over required
    
    # ========================================================================
    # Database/Integration Settings
    # ========================================================================
    use_sql_vendor_lookup: bool = True
    sql_vendor_database: str = "procurement_db"
    sql_vendor_table: str = "vendors"
    
    # ========================================================================
    # Demo/Simulation Settings
    # ========================================================================
    simulation_mode: bool = True  # Use simulated vendor responses
    simulation_response_delay_seconds: float = 0.5  # Simulate network delay
    
    # Simulated quote generation
    simulation_price_variance: float = 0.15  # Vary quote prices by ±15%
    simulation_delivery_variance_days: int = 3  # Vary delivery ±3 days
    
    # ========================================================================
    # Feature Flags
    # ========================================================================
    features_enabled: Dict[str, bool] = field(default_factory=lambda: {
        "parallel_evaluation": True,
        "human_approval_gate": True,
        "negotiation_strategy": True,
        "po_generation": True,
        "vendor_notifications": False,  # Don't actually email vendors
        "auto_po_distribution": False,  # Don't auto-send POs
    })
    
    def get_agent_config(self, agent_type: str) -> Optional[ParallelAgentConfig]:
        """Get configuration for a specific agent type."""
        for agent in self.parallel_agents:
            if agent.agent_type == agent_type:
                return agent
        return None
    
    def get_enabled_agents(self) -> List[ParallelAgentConfig]:
        """Get list of enabled parallel agents."""
        return [agent for agent in self.parallel_agents if agent.enabled]
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled."""
        return self.features_enabled.get(feature_name, False)


# ============================================================================
# Configuration Presets
# ============================================================================

class ConfigurationPresets:
    """Pre-defined configuration profiles for different scenarios."""
    
    @staticmethod
    def development() -> RFQWorkflowConfig:
        """Development configuration with detailed logging and simulation."""
        config = RFQWorkflowConfig()
        config.simulation_mode = True
        config.enable_detailed_logging = True
        config.log_level = "DEBUG"
        config.timeouts.vendor_response_timeout_seconds = 5  # Quick timeouts for dev
        config.timeouts.human_approval_timeout_hours = 1  # 1 hour for dev
        return config
    
    @staticmethod
    def testing() -> RFQWorkflowConfig:
        """Testing configuration with mocked vendor responses."""
        config = RFQWorkflowConfig()
        config.simulation_mode = True
        config.enable_detailed_logging = True
        config.max_retries_on_failure = 3
        config.features_enabled["vendor_notifications"] = False
        config.features_enabled["auto_po_distribution"] = False
        return config
    
    @staticmethod
    def production() -> RFQWorkflowConfig:
        """Production configuration with real vendor integration."""
        config = RFQWorkflowConfig()
        config.simulation_mode = False
        config.enable_detailed_logging = False
        config.log_level = "WARNING"
        config.timeouts.vendor_response_timeout_seconds = 300  # 5 minute timeout
        config.max_retries_on_failure = 2
        config.negotiation_strategy = NegotiationStrategy.MODERATE
        return config
    
    @staticmethod
    def demo() -> RFQWorkflowConfig:
        """Demo configuration optimized for presentation."""
        config = RFQWorkflowConfig()
        config.simulation_mode = True
        config.simulation_response_delay_seconds = 1.0  # Visible delays for demo
        config.enable_detailed_logging = True
        config.timeouts.vendor_response_timeout_seconds = 10
        config.timeouts.human_approval_timeout_hours = 1
        config.features_enabled["parallel_evaluation"] = True
        config.features_enabled["human_approval_gate"] = True
        config.features_enabled["negotiation_strategy"] = True
        return config


# ============================================================================
# Default Instance
# ============================================================================

# Export default configuration instances
DEFAULT_CONFIG = RFQWorkflowConfig()
DEVELOPMENT_CONFIG = ConfigurationPresets.development()
TESTING_CONFIG = ConfigurationPresets.testing()
PRODUCTION_CONFIG = ConfigurationPresets.production()
DEMO_CONFIG = ConfigurationPresets.demo()
