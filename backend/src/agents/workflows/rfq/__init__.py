"""
RFQ Parallel Workflow Package

Comprehensive parallel orchestration workflow for Request for Quotation (RFQ) processing.

Modules:
- models: Data models for RFQ workflow
- config: Configuration management
- observability: Logging and event tracking
"""

from src.agents.workflows.rfq.models import (
    # Enumerations
    VendorStatus,
    RFQStatus,
    ApprovalDecision,
    RiskLevel,
    # Core Models
    RFQRequest,
    ProductRequirements,
    VendorProfile,
    RFQSubmission,
    QuoteResponse,
    VendorEvaluation,
    NormalizedQuote,
    ComparisonReport,
    NegotiationRecommendation,
    ApprovalRequest,
    ApprovalGateResponse,
    PurchaseOrder,
)

from src.agents.workflows.rfq.config import (
    RFQWorkflowConfig,
    ConfigurationPresets,
    MergeStrategy,
    NegotiationStrategy,
    EvaluationWeights,
    TimeoutConfig,
    ApprovalThresholds,
    ParallelAgentConfig,
    # Configuration presets
    DEFAULT_CONFIG,
    DEVELOPMENT_CONFIG,
    TESTING_CONFIG,
    PRODUCTION_CONFIG,
    DEMO_CONFIG,
)

from src.agents.workflows.rfq.observability import (
    # Event types and severity
    RFQEventType,
    EventSeverity,
    # Models
    RFQEvent,
    WorkflowTraceMetadata,
    # Components
    RFQLogger,
    EventCollector,
    # Global instances
    rfq_logger,
    event_collector,
)

__all__ = [
    # Models
    "RFQRequest",
    "ProductRequirements",
    "VendorProfile",
    "RFQSubmission",
    "QuoteResponse",
    "VendorEvaluation",
    "NormalizedQuote",
    "ComparisonReport",
    "NegotiationRecommendation",
    "ApprovalRequest",
    "ApprovalGateResponse",
    "PurchaseOrder",
    # Enumerations
    "VendorStatus",
    "RFQStatus",
    "ApprovalDecision",
    "RiskLevel",
    # Configuration
    "RFQWorkflowConfig",
    "ConfigurationPresets",
    "MergeStrategy",
    "NegotiationStrategy",
    "EvaluationWeights",
    "TimeoutConfig",
    "ApprovalThresholds",
    "ParallelAgentConfig",
    "DEFAULT_CONFIG",
    "DEVELOPMENT_CONFIG",
    "TESTING_CONFIG",
    "PRODUCTION_CONFIG",
    "DEMO_CONFIG",
    # Observability
    "RFQEventType",
    "EventSeverity",
    "RFQEvent",
    "WorkflowTraceMetadata",
    "RFQLogger",
    "EventCollector",
    "rfq_logger",
    "event_collector",
]
