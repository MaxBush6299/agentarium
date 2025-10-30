#!/usr/bin/env python3
"""Test various queries through the handoff workflow."""

import asyncio
import httpx
import json

async def test_workflow(message: str):
    """Test a single query through the workflow."""
    
    url = "http://localhost:8000/api/workflows/intelligent-handoff/chat"
    request_body = {"message": message, "thread_id": "test-001"}
    
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
                    if line.startswith("data:"):
                        data_str = line.split(":", 1)[1].strip()
                        data = json.loads(data_str)
                        
                        if "message" in data:
                            print(f"Response: {data['message']}\n")
                        elif "handoff_path" in data:
                            path = " → ".join([p for p in data['handoff_path'] if not p.startswith('handoff')])
                            print(f"Routing: {path}")
                            print(f"Score: {data.get('final_satisfaction_score', 'N/A')}")
                
    except Exception as e:
        print(f"Error: {e}")

async def main():
    """Run multiple test queries."""
    
    queries = [
        "What are our top 5 customers by revenue?",
        "How much inventory do we have of product 215?",
        "Analyze our sales trends this quarter",
    ]
    
    for query in queries:
        await test_workflow(query)
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
