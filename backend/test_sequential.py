#!/usr/bin/env python3
"""
Test the sequential workflow orchestration pattern via HTTP endpoint.

Sequential pattern:
- data-agent → analyst
- Single-turn execution with shared conversation context
- Useful for fixed pipelines (retrieve → analyze)
"""

import asyncio
import httpx
import json


async def test_workflow(message: str):
    """Test a single query through the sequential workflow."""
    
    url = "http://localhost:8000/api/workflows/sequential-data-analysis/chat"
    request_body = {"message": message, "thread_id": "test-seq-001"}
    
    print(f"\n{'='*80}")
    print(f"Query: {message}")
    print(f"{'='*80}\n")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, json=request_body) as response:
                if response.status_code != 200:
                    print(f"ERROR: Status {response.status_code}")
                    return
                
                async for line in response.aiter_lines():
                    if line.startswith("event:"):
                        event_type = line.split(":", 1)[1].strip()
                        print(f"\n[{event_type.upper()}]")
                    elif line.startswith("data:"):
                        data_str = line.split(":", 1)[1].strip()
                        data = json.loads(data_str)
                        
                        if "message" in data:
                            msg = data['message']
                            print(f"  {msg[:100]}..." if len(msg) > 100 else f"  {msg}\n")
                        elif "workflow_type" in data:
                            print(f"  Workflow Type: {data.get('workflow_type')}")
                            print(f"  Pattern: {data.get('pattern')}")
                            print(f"  Execution Path: {data.get('execution_path')}\n")
                        elif "status" in data:
                            print(f"  {data['status']}")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run multiple test queries."""
    
    print("=" * 80)
    print("TESTING SEQUENTIAL WORKFLOW")
    print("=" * 80)
    
    queries = [
        "What are our top 5 customers by revenue?",
        "How much inventory do we have of product 215?",
        "Analyze our sales trends this quarter",
    ]
    
    for query in queries:
        await test_workflow(query)
        await asyncio.sleep(1)
    
    print(f"\n{'=' * 80}")
    print("SEQUENTIAL WORKFLOW TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
