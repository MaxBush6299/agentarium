# RFQ Parallel Workflow Package

Comprehensive parallel orchestration workflow for Request for Quotation (RFQ) processing using the Microsoft Agent Framework.

## Directory Structure

```
rfq/
├── __init__.py          # Package exports
├── models.py            # Data models (Pydantic)
├── config.py            # Configuration management
└── observability.py     # Logging and event tracking
```

## Package Overview

### 📦 models.py (750+ lines)
Defines all data models for the RFQ workflow using Pydantic.

**Enumerations (4)**
- `VendorStatus` - Vendor qualification states
- `RFQStatus` - RFQ submission tracking
- `ApprovalDecision` - Human approval decisions
- `RiskLevel` - Risk severity levels

**Data Models (12)**
- `RFQRequest` - Initial workflow input
- `ProductRequirements` - Product specifications and constraints
- `VendorProfile` - Vendor information
- `RFQSubmission` - RFQ tracking
- `QuoteResponse` - Vendor quote response
- `VendorEvaluation` - Multi-track evaluation results
- `NormalizedQuote` - Standardized comparison data
- `ComparisonReport` - Comprehensive analysis
- `NegotiationRecommendation` - Negotiation strategy
- `ApprovalRequest` - Human decision request
- `ApprovalGateResponse` - Human decision response
- `PurchaseOrder` - Generated PO

### ⚙️ config.py (350+ lines)
Centralized configuration management for the RFQ workflow.

**Configuration Classes (5)**
- `EvaluationWeights` - Scoring weights (price, delivery, quality, rating)
- `TimeoutConfig` - Timeout settings for all stages
- `ApprovalThresholds` - Auto-approval criteria
- `ParallelAgentConfig` - Individual agent settings
- `RFQWorkflowConfig` - Master configuration (80+ parameters)

**Configuration Presets (4)**
- `DEVELOPMENT_CONFIG` - For local development
- `TESTING_CONFIG` - For unit/integration tests
- `PRODUCTION_CONFIG` - For production deployment
- `DEMO_CONFIG` - Optimized for demonstrations

**Key Configuration Areas**
- Parallel agents (3: Review, Delivery, Financial)
- Merge strategies (weighted, consolidate, consensus)
- Negotiation settings (rounds, variance, leverage)
- Approval thresholds (price, rating, risk)
- Timeouts (vendor, approval, negotiation, PO delivery)
- Feature flags (enable/disable components)
- Simulation settings (for demo/testing)

### 📊 observability.py (450+ lines)
Comprehensive logging and event tracking infrastructure.

**Enumerations (2)**
- `RFQEventType` - 24+ event types for full workflow tracking
- `EventSeverity` - INFO, WARNING, ERROR, CRITICAL

**Data Models (2)**
- `RFQEvent` - Individual event with full context
- `WorkflowTraceMetadata` - Workflow execution summary

**Components (3)**
- `StructuredJsonFormatter` - JSON logging formatter
- `RFQLogger` - Centralized logger interface
- `EventCollector` - Event collection and audit trails

**Global Instances**
- `rfq_logger` - Default logger
- `event_collector` - Default event collector

## Quick Start

### Import All Components
```python
from src.agents.workflows.rfq import (
    # Models
    RFQRequest, ProductRequirements, VendorProfile, QuoteResponse,
    VendorEvaluation, NormalizedQuote, ComparisonReport,
    NegotiationRecommendation, ApprovalRequest, ApprovalGateResponse,
    PurchaseOrder,
    # Enumerations
    VendorStatus, RFQStatus, ApprovalDecision, RiskLevel,
    # Configuration
    RFQWorkflowConfig, DEMO_CONFIG, PRODUCTION_CONFIG,
    # Observability
    RFQEventType, RFQEvent, WorkflowTraceMetadata,
    RFQLogger, EventCollector, rfq_logger, event_collector,
)
```

### Use Development Configuration
```python
from src.agents.workflows.rfq import DEVELOPMENT_CONFIG

config = DEVELOPMENT_CONFIG
print(config.simulation_mode)  # True
print(config.timeouts.vendor_response_timeout_seconds)  # 5
```

### Create an RFQ Request
```python
from src.agents.workflows.rfq import RFQRequest

rfq = RFQRequest(
    request_id="RFQ-001",
    product_id="PROD-123",
    product_name="Industrial Component",
    category="components",
    quantity=500,
    requestor_name="John Doe",
    requestor_email="john@example.com",
    budget_amount=50000.00,
)
```

### Log Events
```python
from src.agents.workflows.rfq import RFQEvent, RFQEventType, rfq_logger
import uuid
from datetime import datetime

event = RFQEvent(
    event_id=str(uuid.uuid4()),
    event_type=RFQEventType.PRODUCT_REQUIREMENTS_DETERMINED,
    timestamp=datetime.utcnow(),
    workflow_id="WF-001",
    stage="product_review",
    message="Product requirements determined",
)

rfq_logger.log_event(event)
```

## Configuration Usage

### Enable/Disable Features
```python
from src.agents.workflows.rfq import DEMO_CONFIG

config = DEMO_CONFIG
config.features_enabled["parallel_evaluation"] = True
config.features_enabled["human_approval_gate"] = True
config.features_enabled["negotiation_strategy"] = True
```

### Adjust Timeouts
```python
config.timeouts.vendor_response_timeout_seconds = 300  # 5 minutes
config.timeouts.human_approval_timeout_hours = 24    # 1 day
config.timeouts.negotiation_timeout_seconds = 120     # 2 minutes
```

### Customize Evaluation Weights
```python
config.evaluation_weights.price_weight = 0.40
config.evaluation_weights.delivery_weight = 0.30
config.evaluation_weights.quality_weight = 0.20
config.evaluation_weights.vendor_rating_weight = 0.10
```

## Event Types

### Workflow Lifecycle (4)
- WORKFLOW_STARTED, WORKFLOW_COMPLETED, WORKFLOW_FAILED, WORKFLOW_PAUSED

### Stage Events (3)
- STAGE_STARTED, STAGE_COMPLETED, STAGE_FAILED

### Process Events (12)
- Product review, vendor qualification, RFQ submission, quote responses

### Parallel Evaluation (4)
- Evaluation started/completed, individual agent completion, results merged

### Approval & Negotiation (4)
- Approval requested/received, renegotiation requested

### Error Handling (2)
- Error occurred, retry attempted, fallback activated

## Phase Information

**Phase**: 1 - Foundation & Architecture Setup ✅ **COMPLETE**

**What's Included**:
- ✅ 12 core data models
- ✅ 4 data enumerations
- ✅ 80+ configuration parameters
- ✅ 4 configuration presets
- ✅ 24+ event types
- ✅ Comprehensive logging infrastructure
- ✅ Audit trail collection
- ✅ JSON-formatted structured logging

**Ready For**:
- Phase 2: Sequential pre-processing agents
- Phase 3: Parallel evaluation stage
- Phase 4-10: Complete workflow implementation

## Integration Points

These models and configuration are designed to integrate with:

1. **Microsoft Agent Framework** - For agent orchestration
2. **SQL Database** - For vendor lookup (Phase 2)
3. **LLM APIs** - For agent reasoning (Phase 2+)
4. **Persistence Layer** - For state management (Phase 8)
5. **API Endpoints** - For vendor communication (Phase 3+)

## Best Practices

1. **Use Configuration Presets**: Start with DEVELOPMENT_CONFIG or DEMO_CONFIG
2. **Enable JSON Logging**: All logs are structured JSON for easy parsing
3. **Collect Events**: Use event_collector for audit trails
4. **Validate Models**: Pydantic validates all data at runtime
5. **Use Enumerations**: Ensures type safety for status/decision fields

## Files and Line Counts

| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py` | 60+ | Package exports |
| `models.py` | 750+ | Data models |
| `config.py` | 350+ | Configuration |
| `observability.py` | 450+ | Logging & events |
| **Total** | **1,610+** | **Complete Phase 1** |

## Testing

```bash
cd backend
python -c "from src.agents.workflows.rfq import *; print('✅ Import successful')"
```

## Next Phase

**Phase 2: Sequential Pre-Processing Stage**
- ProductReviewAgent
- VendorQualificationAgent
- Sequential orchestrator

These agents will use the models, configuration, and observability infrastructure from Phase 1.

---

**Status**: ✅ Phase 1 Complete - Ready for Phase 2

For more information, see:
- `RFQ-PARALLEL-WORKFLOW-PLAN.md` - Complete project plan
- `PHASE-1-COMPLETE.md` - Detailed Phase 1 summary
- `PHASE-1-QUICK-REF.md` - Quick reference guide
