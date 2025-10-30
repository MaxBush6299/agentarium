#!/usr/bin/env python3
"""
Simple test of the handoff workflow via HTTP endpoint.

Tests the simplified handoff chain: router → data-agent → analyst → evaluator
"""

import asyncio
import httpx
import json

async def test_handoff_workflow():
    """Test handoff workflow via HTTP API."""
    
    url = "http://localhost:8000/api/workflows/intelligent-handoff/chat"
    
    request_body = {
        "message": "What are our top 5 customers by revenue?",
        "thread_id": "test-thread-001"
    }
    
    print(f"Testing handoff workflow...")
    print(f"URL: {url}")
    print(f"Request: {json.dumps(request_body, indent=2)}")
    print("\n" + "="*80 + "\n")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Send POST request
            async with client.stream("POST", url, json=request_body) as response:
                print(f"Status: {response.status_code}\n")
                
                # Process SSE events
                events_received = 0
                async for line in response.aiter_lines():
                    if line.startswith("event:"):
                        event_type = line.split(":", 1)[1].strip()
                        print(f"\n>>> Event: {event_type}")
                    elif line.startswith("data:"):
                        data_str = line.split(":", 1)[1].strip()
                        data = json.loads(data_str)
                        print(f"    Data: {json.dumps(data, indent=2)}")
                        events_received += 1
                
                print(f"\n" + "="*80)
                print(f"Total events received: {events_received}")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_handoff_workflow())
