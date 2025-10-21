"""
Quick manual test script for the Chat API.

Usage:
    python scripts/test_chat_api.py

Requirements:
    - Backend server running (python src/main.py or uvicorn)
    - Environment variables configured (.env file)
"""

import asyncio
import httpx
import json
from datetime import datetime


async def test_chat_streaming():
    """Test the streaming chat endpoint."""
    print("\n" + "="*60)
    print("Testing Chat API - Streaming Endpoint")
    print("="*60)
    
    base_url = "http://localhost:8000"
    agent_id = "support-triage"
    
    # Test message
    message = "How do I create a storage account in Azure?"
    
    print(f"\n📤 Sending message to agent '{agent_id}':")
    print(f"   Message: {message}")
    print(f"\n🔄 Streaming response...\n")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Send chat request
        async with client.stream(
            "POST",
            f"{base_url}/api/agents/{agent_id}/chat",
            json={
                "message": message,
                "stream": True
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            }
        ) as response:
            if response.status_code != 200:
                print(f"❌ Error: {response.status_code}")
                print(await response.aread())
                return
            
            print("✅ Connected to stream\n")
            print("-" * 60)
            
            full_response = ""
            token_count = 0
            trace_events = []
            
            # Read SSE stream
            async for line in response.aiter_lines():
                if not line:
                    continue
                
                # Parse SSE format: "data: {json}"
                if line.startswith("data: "):
                    data_str = line[6:]  # Remove "data: " prefix
                    
                    try:
                        event = json.loads(data_str)
                        event_type = event.get("type")
                        
                        if event_type == "token":
                            # Print token inline
                            content = event.get("content", "")
                            print(content, end="", flush=True)
                            full_response += content
                            token_count += 1
                        
                        elif event_type == "trace_start":
                            print(f"\n\n🔧 Tool Call Started: {event.get('tool_name')}")
                            print(f"   Type: {event.get('tool_type')}")
                            print(f"   Input: {json.dumps(event.get('input'), indent=2)}")
                            trace_events.append(event)
                        
                        elif event_type == "trace_end":
                            print(f"\n✅ Tool Call Completed: {event.get('step_id')}")
                            print(f"   Status: {event.get('status')}")
                            print(f"   Latency: {event.get('latency_ms')}ms")
                            trace_events.append(event)
                        
                        elif event_type == "done":
                            print("\n\n" + "-" * 60)
                            print(f"✅ Response completed!")
                            print(f"   Run ID: {event.get('run_id')}")
                            print(f"   Thread ID: {event.get('thread_id')}")
                            print(f"   Message ID: {event.get('message_id')}")
                            print(f"   Tokens Used: {event.get('tokens_used')}")
                            print(f"   Token Events: {token_count}")
                            print(f"   Trace Events: {len(trace_events)}")
                        
                        elif event_type == "error":
                            print(f"\n\n❌ Error: {event.get('error')}")
                            print(f"   Details: {event.get('details')}")
                        
                        elif event_type == "heartbeat":
                            # Silent heartbeat
                            pass
                        
                        else:
                            print(f"\n⚠️ Unknown event type: {event_type}")
                    
                    except json.JSONDecodeError as e:
                        print(f"\n⚠️ Failed to parse event: {e}")
                        print(f"   Data: {data_str}")
    
    print("\n" + "="*60)
    print("Test completed!")
    print("="*60)


async def test_list_threads():
    """Test listing threads."""
    print("\n" + "="*60)
    print("Testing Chat API - List Threads")
    print("="*60)
    
    base_url = "http://localhost:8000"
    agent_id = "support-triage"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/api/agents/{agent_id}/threads")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Found {data['total']} threads")
            
            for thread in data['threads']:
                print(f"\n📝 Thread: {thread['id']}")
                print(f"   Status: {thread['status']}")
                print(f"   Messages: {len(thread.get('messages', []))}")
                print(f"   Created: {thread['created_at']}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
    
    print("\n" + "="*60)


async def main():
    """Run all tests."""
    try:
        # Test streaming chat
        await test_chat_streaming()
        
        # Wait a moment
        await asyncio.sleep(1)
        
        # Test listing threads
        await test_list_threads()
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Chat API Manual Test Script")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nMake sure the backend server is running!")
    print("  Command: python src/main.py")
    print("  Or: uvicorn src.main:app --reload")
    
    asyncio.run(main())
