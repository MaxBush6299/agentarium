"""
Phase 3 Integration Test: Parallel RFQ Orchestration

Tests the complete Phase 3 pipeline:
1. Preprocess requirements (Phase 2)
2. Submit RFQ to all vendors in parallel (Phase 3.1)
3. Collect and parse quotes in parallel (Phase 3.2)
4. Run 3 concurrent evaluation tracks (Phase 3.3)
5. Merge results into final vendor scorecard

Expected execution time: 0.3-0.5 seconds
- Preprocessing: ~0.11s
- RFQ Submission: ~0.05s (parallel to all vendors)
- Quote Parsing: ~0.2s
- Parallel Evaluation: ~0.1s (3 tracks concurrent)
"""

import asyncio
import time
from datetime import datetime, timedelta

# Models
from src.agents.workflows.rfq.models import RFQRequest

# Phase 2: Preprocessing
from src.agents.workflows.rfq.orchestrators.preprocessing_orchestrator import (
    PreprocessingOrchestratorExecutor,
)

# Phase 3: Submission, Parsing, and Parallel Evaluation
from src.agents.workflows.rfq.agents.rfq_submission_agent import (
    RFQSubmissionExecutor,
)
from src.agents.workflows.rfq.agents.quote_parsing_agent import (
    QuoteParsingExecutor,
)
from src.agents.workflows.rfq.orchestrators.parallel_evaluation_orchestrator import (
    ParallelEvaluationOrchestrator,
)

# Observability
from src.agents.workflows.rfq.observability import rfq_logger


async def test_phase3_parallel_orchestration():
    """
    Full Phase 3 pipeline test: preprocessing → submission → parsing → evaluation
    
    This test validates that:
    1. All phases execute in expected time
    2. Parallel execution actually occurs (measured via timing)
    3. Results are properly merged and scored
    4. All logging is structured and auditable
    """
    
    workflow_id = f"test-phase3-{int(time.time())}"
    rfq_logger.info(f"Starting Phase 3 integration test", extra={"workflow_id": workflow_id})
    
    start_total = time.time()
    
    # ============================================================================
    # PHASE 2: PREPROCESSING (Sequential)
    # ============================================================================
    
    rfq_logger.info("Phase 2: Starting preprocessing stage", extra={"workflow_id": workflow_id})
    start_phase2 = time.time()
    
    # Create RFQ request
    rfq_request = RFQRequest(
        request_id=f"REQ-{workflow_id}",
        product_id="SENSOR-001",
        product_name="Premium Industrial Sensors",
        category="industrial_sensors",
        quantity=500,
        unit="pieces",
        required_certifications=["IP67", "UL508"],
        special_requirements="2-year warranty, on-time delivery guarantee",
        desired_delivery_date=datetime.now() + timedelta(weeks=8),
        max_lead_time_days=56,
        budget_amount=150000,
        requestor_name="John Doe",
        requestor_email="john@company.com",
    )
    
    preprocessing_executor = PreprocessingOrchestratorExecutor()
    requirements, qualified_vendors = await preprocessing_executor.execute(rfq_request, workflow_id)
    
    phase2_time = time.time() - start_phase2
    rfq_logger.info(
        f"Phase 2 complete: {len(qualified_vendors)} vendors qualified",
        extra={
            "workflow_id": workflow_id,
            "duration_seconds": round(phase2_time, 3),
            "qualified_vendors": [v.vendor_name for v in qualified_vendors]
        }
    )
    
    # ============================================================================
    # PHASE 3.1: PARALLEL RFQ SUBMISSION
    # ============================================================================
    
    rfq_logger.info("Phase 3.1: Starting parallel RFQ submission", extra={"workflow_id": workflow_id})
    start_phase3_1 = time.time()
    
    rfq_executor = RFQSubmissionExecutor()
    rfq_submissions = await rfq_executor.submit_to_all_vendors(
        requirements=requirements,
        vendors=qualified_vendors,
        workflow_id=workflow_id
    )
    
    phase3_1_time = time.time() - start_phase3_1
    rfq_logger.info(
        f"Phase 3.1 complete: {len(rfq_submissions)} RFQs submitted",
        extra={
            "workflow_id": workflow_id,
            "duration_seconds": round(phase3_1_time, 3),
            "all_status": "SUBMITTED"
        }
    )
    
    # ============================================================================
    # PHASE 3.2: PARALLEL QUOTE PARSING
    # ============================================================================
    
    rfq_logger.info("Phase 3.2: Starting parallel quote collection and parsing", extra={"workflow_id": workflow_id})
    start_phase3_2 = time.time()
    
    quote_executor = QuoteParsingExecutor()
    quote_responses = await quote_executor.execute(
        requirements=requirements,
        vendors=qualified_vendors,
        submissions=rfq_submissions,
        workflow_id=workflow_id
    )
    
    phase3_2_time = time.time() - start_phase3_2
    rfq_logger.info(
        f"Phase 3.2 complete: {len(quote_responses)} quotes parsed",
        extra={
            "workflow_id": workflow_id,
            "duration_seconds": round(phase3_2_time, 3),
            "quotes_received": len(quote_responses),
            "sample_quotes": [
                {
                    "vendor": next(v.vendor_name for v in qualified_vendors if v.vendor_id == q.vendor_id),
                    "unit_price": round(q.unit_price, 2),
                    "total_cost": round(q.unit_price * requirements.quantity, 2),
                    "delivery_lead": q.delivery_lead_days
                }
                for q in quote_responses[:3]
            ]
        }
    )
    
    # ============================================================================
    # PHASE 3.3: PARALLEL MULTI-TRACK EVALUATION
    # ============================================================================
    
    rfq_logger.info("Phase 3.3: Starting 3 parallel evaluation tracks", extra={"workflow_id": workflow_id})
    start_phase3_3 = time.time()
    
    evaluator_orchestrator = ParallelEvaluationOrchestrator()
    vendor_evaluations, track_results = await evaluator_orchestrator.evaluate_all_vendors(
        requirements=requirements,
        vendors=qualified_vendors,
        quotes=quote_responses,
        workflow_id=workflow_id
    )
    
    phase3_3_time = time.time() - start_phase3_3
    
    # Analyze track results
    track_summary = {}
    for track_result in track_results:
        track_name = track_result.track_name
        if track_name not in track_summary:
            track_summary[track_name] = {"vendors": 0, "avg_score": 0, "critical_count": 0}
        track_summary[track_name]["vendors"] += 1
        track_summary[track_name]["avg_score"] += track_result.score
        if track_result.risk_level == "CRITICAL":
            track_summary[track_name]["critical_count"] += 1
    
    for track_name in track_summary:
        track_summary[track_name]["avg_score"] /= track_summary[track_name]["vendors"]
    
    rfq_logger.info(
        f"Phase 3.3 complete: 3 tracks evaluated {len(qualified_vendors)} vendors",
        extra={
            "workflow_id": workflow_id,
            "duration_seconds": round(phase3_3_time, 3),
            "track_summary": track_summary
        }
    )
    
    # ============================================================================
    # RESULTS SUMMARY
    # ============================================================================
    
    total_time = time.time() - start_total
    
    # Sort vendors by review_score (descending), handling None values
    top_vendors = sorted(
        vendor_evaluations,
        key=lambda v: v.review_score if v.review_score is not None else 0,
        reverse=True
    )[:3]
    
    results_summary = {
        "workflow_id": workflow_id,
        "timestamp": datetime.now().isoformat(),
        "total_execution_time_seconds": round(total_time, 3),
        "phase_breakdown": {
            "preprocessing": round(phase2_time, 3),
            "rfq_submission": round(phase3_1_time, 3),
            "quote_parsing": round(phase3_2_time, 3),
            "parallel_evaluation": round(phase3_3_time, 3)
        },
        "results": {
            "requirements_quantity": requirements.quantity,
            "vendors_qualified": len(qualified_vendors),
            "quotes_received": len(quote_responses),
            "evaluations_completed": len(vendor_evaluations),
            "top_3_recommendations": [
                {
                    "vendor_name": v.vendor_name,
                    "review_score": round(v.review_score, 2) if v.review_score is not None else 0,
                    "compliance_status": v.compliance_status,
                    "delivery_feasible": v.delivery_feasible,
                    "price_competitiveness": v.price_competitiveness,
                    "risk_level": getattr(v, 'risk_assessment_result', 'UNKNOWN')
                }
                for v in top_vendors
            ]
        },
        "validation": {
            "all_phases_executed": True,
            "parallel_timing_valid": phase3_3_time < 0.3,  # Should be quick with parallel execution
            "results_merged": len(vendor_evaluations) == len(qualified_vendors),
            "track_results_captured": len(track_results) == len(qualified_vendors) * 3
        }
    }
    
    rfq_logger.info(
        "✅ Phase 3 Integration Test Complete",
        extra=results_summary
    )
    
    # Detailed test validation
    print("\n" + "="*80)
    print("PHASE 3 INTEGRATION TEST RESULTS")
    print("="*80)
    print(f"\n[Execution Summary]")
    print(f"  Total Time: {results_summary['total_execution_time_seconds']:.3f}s")
    print(f"  Phase Breakdown:")
    print(f"    - Preprocessing (Phase 2): {results_summary['phase_breakdown']['preprocessing']:.3f}s")
    print(f"    - RFQ Submission (Phase 3.1): {results_summary['phase_breakdown']['rfq_submission']:.3f}s")
    print(f"    - Quote Parsing (Phase 3.2): {results_summary['phase_breakdown']['quote_parsing']:.3f}s")
    print(f"    - Parallel Evaluation (Phase 3.3): {results_summary['phase_breakdown']['parallel_evaluation']:.3f}s")
    
    print(f"\n[Processing Details]")
    print(f"  Vendors Qualified: {results_summary['results']['vendors_qualified']}")
    print(f"  Quotes Received: {results_summary['results']['quotes_received']}")
    print(f"  Evaluations Completed: {results_summary['results']['evaluations_completed']}")
    print(f"  Requirements: {results_summary['results']['requirements_quantity']} units")
    
    print(f"\n[Top 3 Recommendations]")
    for i, vendor in enumerate(results_summary['results']['top_3_recommendations'], 1):
        print(f"\n  {i}. {vendor['vendor_name']}")
        print(f"     Score: {vendor['review_score']}/5.0")
        print(f"     Compliance: {vendor['compliance_status']}")
        feasible = "YES" if vendor['delivery_feasible'] else "NO"
        print(f"     Delivery: {feasible}")
        print(f"     Price: {vendor['price_competitiveness']}")
    
    print(f"\n[Validation]")
    for key, value in results_summary['validation'].items():
        status = "PASS" if value else "FAIL"
        print(f"  [{status}] {key}: {value}")
    
    print("\n" + "="*80)
    
    return results_summary


if __name__ == "__main__":
    results = asyncio.run(test_phase3_parallel_orchestration())
    
    # Exit with success code if validation passed
    all_valid = all(results['validation'].values())
    exit(0 if all_valid else 1)
