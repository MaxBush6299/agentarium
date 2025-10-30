#!/usr/bin/env python3
"""Test script for handoff workflow execution."""

import asyncio
import json
import sys

async def test_handoff_workflow():
    """Test the handoff workflow via API."""
    import httpx
    
    print("\n" + "=" * 80)
    print("TESTING HANDOFF WORKFLOW")
    print("=" * 80 + "\n")
    
    # Test message
    test_message = "What are our top 10 customers by sales volume?"
    
    # API endpoint
    url = "http://localhost:8000/api/agents/intelligent-handoff/chat"
    
    payload = {
        "message": test_message,
        "thread_id": "test-thread-001"
    }
    
    print(f"📤 Sending request to: {url}")
    print(f"📝 Message: {test_message}\n")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            
            print(f"Status Code: {response.status_code}\n")
            
            if response.status_code == 200:
                data = response.json()
                
                if "data" in data:
                    response_data = json.loads(data["data"])
                    print(f"✓ Response received!")
                    print(f"  - Response: {response_data.get('response', 'N/A')[:100]}...")
                    if "trace_metadata" in response_data:
                        trace = response_data["trace_metadata"]
                        print(f"  - Handoff Path: {' → '.join(trace.get('handoff_path', []))}")
                        print(f"  - Primary Agent: {trace.get('primary_agent', 'N/A')}")
                        print(f"  - Satisfaction: {trace.get('satisfaction_score', 'N/A')}")
                    return True
                else:
                    print(f"✗ Unexpected response format: {data}")
                    return False
            else:
                print(f"✗ Error: {response.status_code}")
                print(f"  Response: {response.text[:200]}")
                return False
                
    except Exception as e:
        print(f"✗ Connection error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_handoff_workflow())
    print("\n" + "=" * 80)
    if result:
        print("✓ Handoff workflow test PASSED")
        sys.exit(0)
    else:
        print("✗ Handoff workflow test FAILED")
        sys.exit(1)
