"""
RFQ Workflow Observability and Logging

Structured logging, tracing, and monitoring infrastructure for the RFQ workflow.
Provides audit trails, performance metrics, and debugging capabilities.
"""

import logging
import json
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


# ============================================================================
# Event Types
# ============================================================================

class RFQEventType(str, Enum):
    """Event types for RFQ workflow tracking."""
    # Workflow lifecycle
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    WORKFLOW_PAUSED = "workflow_paused"
    
    # Stage transitions
    STAGE_STARTED = "stage_started"
    STAGE_COMPLETED = "stage_completed"
    STAGE_FAILED = "stage_failed"
    
    # Product review
    PRODUCT_REVIEW_STARTED = "product_review_started"
    PRODUCT_REQUIREMENTS_DETERMINED = "product_requirements_determined"
    
    # Vendor qualification
    VENDOR_QUALIFICATION_STARTED = "vendor_qualification_started"
    VENDORS_QUALIFIED = "vendors_qualified"
    VENDOR_QUERY_EXECUTED = "vendor_query_executed"
    
    # RFQ Submission
    RFQ_SUBMISSION_STARTED = "rfq_submission_started"
    RFQ_SUBMITTED = "rfq_submitted"
    RFQ_ACKNOWLEDGMENT_RECEIVED = "rfq_acknowledgment_received"
    RFQ_TIMEOUT = "rfq_timeout"
    
    # Quote Response
    QUOTE_RECEIVED = "quote_received"
    QUOTE_PARSED = "quote_parsed"
    QUOTE_VALIDATION_ERROR = "quote_validation_error"
    
    # Parallel Evaluation
    PARALLEL_EVALUATION_STARTED = "parallel_evaluation_started"
    PARALLEL_EVALUATION_COMPLETED = "parallel_evaluation_completed"
    AGENT_EVALUATION_COMPLETED = "agent_evaluation_completed"
    RESULTS_MERGED = "results_merged"
    
    # Comparison and Analysis
    COMPARISON_STARTED = "comparison_started"
    COMPARISON_COMPLETED = "comparison_completed"
    RISK_ASSESSMENT_COMPLETED = "risk_assessment_completed"
    
    # Negotiation
    NEGOTIATION_STARTED = "negotiation_started"
    NEGOTIATION_RECOMMENDATION_GENERATED = "negotiation_recommendation_generated"
    NEGOTIATION_COMPLETED = "negotiation_completed"
    
    # Approval Gate
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_RESPONSE_RECEIVED = "approval_response_received"
    APPROVAL_COMPLETED = "approval_completed"
    RENEGOTIATION_REQUESTED = "renegotiation_requested"
    
    # PO Generation
    PO_GENERATION_STARTED = "po_generation_started"
    PO_GENERATED = "po_generated"
    PO_DISTRIBUTED = "po_distributed"
    
    # Errors and Failures
    ERROR_OCCURRED = "error_occurred"
    RETRY_ATTEMPTED = "retry_attempted"
    FALLBACK_ACTIVATED = "fallback_activated"


class EventSeverity(str, Enum):
    """Event severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ============================================================================
# Event Models
# ============================================================================

@dataclass
class RFQEvent:
    """
    Base event for RFQ workflow tracking.
    
    Provides comprehensive context for audit trails and debugging.
    """
    event_id: str
    event_type: RFQEventType
    timestamp: datetime
    workflow_id: str
    thread_id: Optional[str] = None
    
    # Event context
    stage: Optional[str] = None  # Current stage name
    step: Optional[str] = None  # Current step within stage
    
    # Severity and status
    severity: EventSeverity = EventSeverity.INFO
    success: bool = True
    
    # Detailed information
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)  # Event-specific data
    
    # Error information
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    
    # Performance metrics
    duration_ms: Optional[float] = None  # How long this event took
    
    # Tracing
    parent_event_id: Optional[str] = None
    related_event_ids: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize default values."""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "workflow_id": self.workflow_id,
            "thread_id": self.thread_id,
            "stage": self.stage,
            "step": self.step,
            "severity": self.severity.value,
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
            "parent_event_id": self.parent_event_id,
            "related_event_ids": self.related_event_ids,
        }


@dataclass
class WorkflowTraceMetadata:
    """
    Metadata for workflow execution trace.
    
    Summarizes workflow execution for auditing and analysis.
    """
    workflow_id: str
    workflow_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Status
    status: str = "in_progress"  # in_progress, completed, failed, paused
    success: bool = False
    
    # Execution details
    thread_id: Optional[str] = None
    stages_executed: List[str] = field(default_factory=list)
    
    # Participants
    agents_involved: List[str] = field(default_factory=list)
    human_decisions_made: int = 0
    
    # Results
    selected_vendor_id: Optional[str] = None
    selected_vendor_name: Optional[str] = None
    po_number: Optional[str] = None
    
    # Metrics
    total_duration_seconds: Optional[float] = None
    parallel_stages_count: int = 0
    total_agents_invoked: int = 0
    human_approval_time_seconds: Optional[float] = None
    
    # Events
    events: List[RFQEvent] = field(default_factory=list)
    event_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    
    # Decisions and rationale
    decision_rationale: Optional[str] = None
    risk_flags: List[str] = field(default_factory=list)
    negotiation_leverage_used: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize default values."""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status,
            "success": self.success,
            "thread_id": self.thread_id,
            "stages_executed": self.stages_executed,
            "agents_involved": self.agents_involved,
            "human_decisions_made": self.human_decisions_made,
            "selected_vendor_id": self.selected_vendor_id,
            "selected_vendor_name": self.selected_vendor_name,
            "po_number": self.po_number,
            "total_duration_seconds": self.total_duration_seconds,
            "parallel_stages_count": self.parallel_stages_count,
            "total_agents_invoked": self.total_agents_invoked,
            "human_approval_time_seconds": self.human_approval_time_seconds,
            "event_count": self.event_count,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "decision_rationale": self.decision_rationale,
            "risk_flags": self.risk_flags,
            "negotiation_leverage_used": self.negotiation_leverage_used,
        }


# ============================================================================
# JSON Formatter for Structured Logging
# ============================================================================

class StructuredJsonFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    
    Outputs logs as JSON objects for better parsing and analysis.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add custom fields if present in extra dict
        if hasattr(record, "workflow_id"):
            log_data["workflow_id"] = getattr(record, "workflow_id", None)
        if hasattr(record, "stage"):
            log_data["stage"] = getattr(record, "stage", None)
        if hasattr(record, "vendor_id"):
            log_data["vendor_id"] = getattr(record, "vendor_id", None)
        if hasattr(record, "event_type"):
            log_data["event_type"] = getattr(record, "event_type", None)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


# ============================================================================
# RFQ Logger
# ============================================================================

class RFQLogger:
    """
    Logging interface for RFQ workflow.
    
    Centralizes logging for all workflow components with structured output.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize RFQ logger.
        
        Args:
            name: Logger name (typically __name__ from module)
            config: Optional configuration dictionary
        """
        self.logger = logging.getLogger(name)
        self.config = config or {}
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up logging handlers."""
        # Only configure if not already configured
        if self.logger.handlers:
            return
        
        # Console handler with JSON formatter
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(StructuredJsonFormatter())
        self.logger.addHandler(console_handler)
        
        # File handler for RFQ logs
        try:
            file_handler = logging.FileHandler("logs/rfq_workflow.log")
            file_handler.setFormatter(StructuredJsonFormatter())
            self.logger.addHandler(file_handler)
        except Exception as e:
            self.logger.warning(f"Could not set up file handler: {e}")
        
        # Set log level
        log_level = self.config.get("log_level", "INFO")
        self.logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    def log_event(
        self,
        event: RFQEvent,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log an RFQ event.
        
        Args:
            event: RFQEvent instance to log
            extra: Additional context to include
        """
        log_level = logging.WARNING if event.severity == EventSeverity.ERROR else logging.INFO
        
        message = f"[{event.event_type.value}] {event.message}"
        
        # Add to logger with custom fields
        extra_dict = extra or {}
        extra_dict.update({
            "workflow_id": event.workflow_id,
            "stage": event.stage,
            "event_type": event.event_type.value,
        })
        
        self.logger.log(log_level, message, extra=extra_dict)
    
    def info(
        self,
        message: str,
        workflow_id: Optional[str] = None,
        stage: Optional[str] = None,
        **kwargs
    ) -> None:
        """Log info message."""
        extra = {"workflow_id": workflow_id, "stage": stage}
        extra.update(kwargs)
        self.logger.info(message, extra=extra)
    
    def warning(
        self,
        message: str,
        workflow_id: Optional[str] = None,
        stage: Optional[str] = None,
        **kwargs
    ) -> None:
        """Log warning message."""
        extra = {"workflow_id": workflow_id, "stage": stage}
        extra.update(kwargs)
        self.logger.warning(message, extra=extra)
    
    def error(
        self,
        message: str,
        workflow_id: Optional[str] = None,
        stage: Optional[str] = None,
        **kwargs
    ) -> None:
        """Log error message."""
        extra = {"workflow_id": workflow_id, "stage": stage}
        extra.update(kwargs)
        self.logger.error(message, extra=extra)


# ============================================================================
# Event Collector for Audit Trails
# ============================================================================

class EventCollector:
    """
    Collects RFQ events for audit trails and analysis.
    
    Maintains event history and provides query/analysis capabilities.
    """
    
    def __init__(self):
        """Initialize event collector."""
        self.events: List[RFQEvent] = []
        self._event_index: Dict[str, List[RFQEvent]] = {}
    
    def add_event(self, event: RFQEvent) -> None:
        """
        Add event to collection.
        
        Args:
            event: RFQEvent to add
        """
        self.events.append(event)
        
        # Index by workflow_id for quick lookup
        if event.workflow_id not in self._event_index:
            self._event_index[event.workflow_id] = []
        self._event_index[event.workflow_id].append(event)
    
    def get_events_for_workflow(self, workflow_id: str) -> List[RFQEvent]:
        """Get all events for a specific workflow."""
        return self._event_index.get(workflow_id, [])
    
    def get_events_by_type(
        self,
        workflow_id: str,
        event_type: RFQEventType,
    ) -> List[RFQEvent]:
        """Get events of specific type for workflow."""
        events = self.get_events_for_workflow(workflow_id)
        return [e for e in events if e.event_type == event_type]
    
    def get_error_events(self, workflow_id: str) -> List[RFQEvent]:
        """Get all error events for workflow."""
        events = self.get_events_for_workflow(workflow_id)
        return [e for e in events if e.severity == EventSeverity.ERROR]
    
    def export_to_json(self, workflow_id: str) -> str:
        """Export workflow events to JSON string."""
        events = self.get_events_for_workflow(workflow_id)
        return json.dumps(
            [event.to_dict() for event in events],
            indent=2,
            default=str,
        )
    
    def export_to_file(self, workflow_id: str, filepath: str) -> None:
        """Export workflow events to JSON file."""
        with open(filepath, "w") as f:
            f.write(self.export_to_json(workflow_id))


# ============================================================================
# Global Instances
# ============================================================================

# Global logger for RFQ workflow
rfq_logger = RFQLogger(__name__)

# Global event collector
event_collector = EventCollector()
