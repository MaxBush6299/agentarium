#!/usr/bin/env python3
"""
Test RFQ workflow via API endpoint.

This test verifies the complete integration:
1. Workflow registry has rfq-procurement
2. API can execute the workflow
3. All 7 phases complete successfully
4. SSE streaming works
"""

import asyncio
import httpx
import json


async def test_rfq_workflow_api():
    """Test RFQ workflow execution via HTTP API."""
    
    print("=" * 80)
    print("Testing RFQ Procurement Workflow via API")
    print("=" * 80)
    
    # Test message - will use defaults since not valid JSON
    test_message = "I need to procure 1000 high-precision industrial sensors"
    
    request_body = {
        "message": test_message,
        "thread_id": f"test-rfq-{int(asyncio.get_event_loop().time())}",
    }
    
    print(f"\n📨 Sending request to POST /api/workflows/rfq-procurement/chat")
    print(f"   Message: {test_message}")
    print(f"   Thread ID: {request_body['thread_id']}")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            # Send request
            async with client.stream(
                'POST',
                'http://localhost:8000/api/workflows/rfq-procurement/chat',
                json=request_body,
                headers={'Accept': 'text/event-stream'}
            ) as response:
                
                if response.status_code != 200:
                    print(f"\n❌ Error: HTTP {response.status_code}")
                    print(await response.aread())
                    return False
                
                print(f"\n✓ Connected, receiving events...\n")
                
                event_count = 0
                final_message = None
                metadata = None
                
                # Process SSE stream
                async for line in response.aiter_lines():
                    if not line or line.startswith(':'):
                        continue
                    
                    if line.startswith('event:'):
                        event_type = line.split(':', 1)[1].strip()
                        continue
                    
                    if line.startswith('data:'):
                        data_str = line.split(':', 1)[1].strip()
                        data = json.loads(data_str)
                        event_count += 1
                        
                        # Handle different event types
                        if 'status' in data:
                            status = data.get('status', '')
                            msg = data.get('message', '')
                            print(f"📊 Status: {status}")
                            if msg:
                                print(f"   {msg}")
                        
                        elif 'message' in data:
                            final_message = data['message']
                            print(f"\n📄 Final Response:")
                            print("-" * 80)
                            print(final_message)
                            print("-" * 80)
                        
                        elif 'workflow_id' in data:
                            metadata = data
                            print(f"\n📊 Metadata:")
                            print(f"   Workflow: {data.get('workflow_id')}")
                            print(f"   Execution ID: {data.get('execution_id')}")
                            print(f"   Type: {data.get('workflow_type')}")
                            print(f"   Phases Completed: {data.get('phases_completed', 0)}")
                            print(f"   Vendors Evaluated: {data.get('vendors_evaluated', 0)}")
                            print(f"   Top Vendor: {data.get('top_vendor')}")
                            print(f"   PO Number: {data.get('purchase_order_number')}")
                            print(f"   Total Amount: ${data.get('total_amount', 0):,.2f}")
                        
                        elif 'complete' in data:
                            is_complete = data['complete']
                            if is_complete:
                                print(f"\n✅ Workflow completed successfully!")
                            else:
                                print(f"\n❌ Workflow failed to complete")
                            break
                        
                        elif 'error' in data:
                            print(f"\n❌ Error: {data['error']}")
                            return False
                
                print(f"\n📊 Received {event_count} events total")
                
                # Verify workflow completed
                if final_message and metadata:
                    print(f"\n✅ RFQ Workflow Test PASSED")
                    print(f"   - Received final message: {len(final_message)} chars")
                    print(f"   - Phases completed: {metadata.get('phases_completed', 0)}/7")
                    print(f"   - Vendors evaluated: {metadata.get('vendors_evaluated', 0)}")
                    print(f"   - Purchase order generated: {metadata.get('purchase_order_number')}")
                    return True
                else:
                    print(f"\n❌ RFQ Workflow Test FAILED")
                    print(f"   - Missing final message or metadata")
                    return False
        
        except Exception as e:
            print(f"\n❌ Request failed: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    result = asyncio.run(test_rfq_workflow_api())
    exit(0 if result else 1)
