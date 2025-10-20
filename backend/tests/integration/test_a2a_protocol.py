"""
Integration tests for A2A (Agent-to-Agent) Protocol implementation.

Tests the A2A server endpoints following the official specification:
https://a2a-protocol.org/latest/specification/

Test Coverage:
- Agent Card discovery at /.well-known/agent.json
- JSON-RPC 2.0 message/send method
- JSON-RPC 2.0 tasks/get method
- JSON-RPC 2.0 tasks/cancel method
- Error handling for invalid requests
"""

import pytest
import uuid
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


class TestA2AAgentCard:
    """Test Agent Card discovery per A2A spec Section 5"""
    
    async def test_agent_card_available_at_well_known_location(self, test_client: AsyncClient):
        """
        Test that the agent card is available at /.well-known/agent.json
        
        Per A2A spec Section 5.3:
        "The recommended location for an agent's Agent Card is:
         https://{server_domain}/.well-known/agent-card.json (for C#)
         https://{server_domain}/.well-known/agent.json (for Python)"
        """
        response = await test_client.get("/.well-known/agent.json")
        
        assert response.status_code == 200
        agent_card = response.json()
        
        # Validate required fields per spec Section 5.5
        assert agent_card["protocolVersion"] == "0.3.0"
        assert agent_card["name"] == "Support Triage Agent"
        assert "description" in agent_card
        assert agent_card["url"]  # Should contain the A2A endpoint URL
        assert agent_card["preferredTransport"] == "JSONRPC"
        assert agent_card["version"] == "1.0.0"
    
    async def test_agent_card_has_valid_capabilities(self, test_client: AsyncClient):
        """Validate agent capabilities structure per spec Section 5.5.2"""
        response = await test_client.get("/.well-known/agent.json")
        agent_card = response.json()
        
        capabilities = agent_card["capabilities"]
        assert isinstance(capabilities["streaming"], bool)
        assert isinstance(capabilities["pushNotifications"], bool)
        assert isinstance(capabilities["stateTransitionHistory"], bool)
    
    async def test_agent_card_has_skills(self, test_client: AsyncClient):
        """Validate agent skills structure per spec Section 5.5.4"""
        response = await test_client.get("/.well-known/agent.json")
        agent_card = response.json()
        
        skills = agent_card["skills"]
        assert len(skills) > 0
        
        # Validate first skill structure
        skill = skills[0]
        assert skill["id"] == "support-triage"
        assert skill["name"]
        assert skill["description"]
        assert isinstance(skill["tags"], list)
        assert len(skill["tags"]) > 0
        assert "examples" in skill
        assert len(skill["examples"]) > 0


class TestA2AMessageSend:
    """Test message/send method per A2A spec Section 7.1"""
    
    async def test_message_send_creates_new_task(self, test_client: AsyncClient):
        """
        Test that message/send creates a new task and returns it
        
        Per spec Section 7.1:
        "Sends a message to an agent to initiate a new interaction or
         to continue an existing one."
        """
        # Prepare JSON-RPC request per spec Section 6.11.1
        request_id = str(uuid.uuid4())
        message_id = str(uuid.uuid4())
        
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "message/send",
            "params": {
                "message": {
                    "role": "user",
                    "parts": [
                        {
                            "kind": "text",
                            "text": "How do I deploy a FastAPI app to Azure?"
                        }
                    ],
                    "messageId": message_id
                }
            }
        }
        
        response = await test_client.post("/a2a", json=payload)
        
        assert response.status_code == 200
        rpc_response = response.json()
        
        # Validate JSON-RPC response structure per spec Section 6.11.2
        assert rpc_response["jsonrpc"] == "2.0"
        assert rpc_response["id"] == request_id
        assert "result" in rpc_response
        assert "error" not in rpc_response
        
        # Validate Task structure per spec Section 6.1
        task = rpc_response["result"]
        assert task["kind"] == "task"
        assert "id" in task
        assert "contextId" in task
        assert "status" in task
        
        # Validate TaskStatus per spec Section 6.2
        status = task["status"]
        assert status["state"] in ["submitted", "working", "completed"]
        assert "timestamp" in status
    
    async def test_message_send_with_context_continuation(self, test_client: AsyncClient):
        """Test continuing a conversation with an existing task ID"""
        # First message
        message_id_1 = str(uuid.uuid4())
        payload_1 = {
            "jsonrpc": "2.0",
            "id": "req-1",
            "method": "message/send",
            "params": {
                "message": {
                    "role": "user",
                    "parts": [{"kind": "text", "text": "What is Azure Container Apps?"}],
                    "messageId": message_id_1
                }
            }
        }
        
        response_1 = await test_client.post("/a2a", json=payload_1)
        task_1 = response_1.json()["result"]
        task_id = task_1["id"]
        context_id = task_1["contextId"]
        
        # Second message continuing the conversation
        message_id_2 = str(uuid.uuid4())
        payload_2 = {
            "jsonrpc": "2.0",
            "id": "req-2",
            "method": "message/send",
            "params": {
                "message": {
                    "role": "user",
                    "parts": [{"kind": "text", "text": "How do I scale it?"}],
                    "messageId": message_id_2,
                    "taskId": task_id,
                    "contextId": context_id
                }
            }
        }
        
        response_2 = await test_client.post("/a2a", json=payload_2)
        task_2 = response_2.json()["result"]
        
        # Should be the same task ID
        assert task_2["id"] == task_id
        assert task_2["contextId"] == context_id
        
        # History should contain both messages
        assert len(task_2["history"]) >= 2


class TestA2ATasksGet:
    """Test tasks/get method per A2A spec Section 7.3"""
    
    async def test_tasks_get_retrieves_existing_task(self, test_client: AsyncClient):
        """
        Test retrieving a task by ID
        
        Per spec Section 7.3:
        "Retrieves the current state (including status, artifacts, and
         optionally history) of a previously initiated task."
        """
        # First create a task
        create_payload = {
            "jsonrpc": "2.0",
            "id": "create-req",
            "method": "message/send",
            "params": {
                "message": {
                    "role": "user",
                    "parts": [{"kind": "text", "text": "Test message"}],
                    "messageId": str(uuid.uuid4())
                }
            }
        }
        
        create_response = await test_client.post("/a2a", json=create_payload)
        task = create_response.json()["result"]
        task_id = task["id"]
        
        # Now retrieve it
        get_payload = {
            "jsonrpc": "2.0",
            "id": "get-req",
            "method": "tasks/get",
            "params": {
                "id": task_id
            }
        }
        
        get_response = await test_client.post("/a2a", json=get_payload)
        
        assert get_response.status_code == 200
        rpc_response = get_response.json()
        
        retrieved_task = rpc_response["result"]
        assert retrieved_task["id"] == task_id
        assert "status" in retrieved_task
        assert "history" in retrieved_task
    
    async def test_tasks_get_with_history_length_limit(self, test_client: AsyncClient):
        """Test limiting history length in tasks/get"""
        # Create task with multiple messages
        task_id = None
        for i in range(3):
            payload = {
                "jsonrpc": "2.0",
                "id": f"req-{i}",
                "method": "message/send",
                "params": {
                    "message": {
                        "role": "user",
                        "parts": [{"kind": "text", "text": f"Message {i}"}],
                        "messageId": str(uuid.uuid4()),
                        **({"taskId": task_id} if task_id else {})
                    }
                }
            }
            response = await test_client.post("/a2a", json=payload)
            task_id = response.json()["result"]["id"]
        
        # Retrieve with history length limit
        get_payload = {
            "jsonrpc": "2.0",
            "id": "get-req",
            "method": "tasks/get",
            "params": {
                "id": task_id,
                "historyLength": 2
            }
        }
        
        get_response = await test_client.post("/a2a", json=get_payload)
        retrieved_task = get_response.json()["result"]
        
        # History should be limited to last 2 messages
        assert len(retrieved_task["history"]) <= 2


class TestA2ATasksCancel:
    """Test tasks/cancel method per A2A spec Section 7.5"""
    
    async def test_tasks_cancel_marks_task_as_canceled(self, test_client: AsyncClient):
        """
        Test canceling a task
        
        Per spec Section 7.5:
        "Requests the cancellation of an ongoing task. The server will
         attempt to cancel the task, but success is not guaranteed."
        """
        # Create a task
        create_payload = {
            "jsonrpc": "2.0",
            "id": "create-req",
            "method": "message/send",
            "params": {
                "message": {
                    "role": "user",
                    "parts": [{"kind": "text", "text": "Long running task"}],
                    "messageId": str(uuid.uuid4())
                }
            }
        }
        
        create_response = await test_client.post("/a2a", json=create_payload)
        task_id = create_response.json()["result"]["id"]
        
        # Cancel it (note: in this implementation, task likely completes too fast)
        # But we test the cancel endpoint works
        cancel_payload = {
            "jsonrpc": "2.0",
            "id": "cancel-req",
            "method": "tasks/cancel",
            "params": {
                "id": task_id
            }
        }
        
        cancel_response = await test_client.post("/a2a", json=cancel_payload)
        
        # Should get a response (may or may not be canceled depending on timing)
        assert cancel_response.status_code == 200
        rpc_response = cancel_response.json()
        
        # If task was already completed, we get an error
        if "error" in rpc_response:
            assert rpc_response["error"]["code"] == -32602  # Invalid params
        else:
            # If successfully canceled
            canceled_task = rpc_response["result"]
            assert canceled_task["status"]["state"] == "canceled"


class TestA2AErrorHandling:
    """Test error handling per A2A spec Section 8"""
    
    async def test_method_not_found_error(self, test_client: AsyncClient):
        """
        Test error code -32601 for unknown methods
        
        Per spec Section 8.1:
        "The requested A2A RPC method does not exist or is not supported."
        """
        payload = {
            "jsonrpc": "2.0",
            "id": "error-req",
            "method": "unknown/method",
            "params": {}
        }
        
        response = await test_client.post("/a2a", json=payload)
        
        assert response.status_code == 200
        rpc_response = response.json()
        
        assert "error" in rpc_response
        assert rpc_response["error"]["code"] == -32601
        assert "method not found" in rpc_response["error"]["message"].lower()
    
    async def test_invalid_params_error(self, test_client: AsyncClient):
        """
        Test error code -32602 for invalid parameters
        
        Per spec Section 8.1:
        "The params provided for the method are invalid."
        """
        payload = {
            "jsonrpc": "2.0",
            "id": "error-req",
            "method": "tasks/get",
            "params": {}  # Missing required 'id' parameter
        }
        
        response = await test_client.post("/a2a", json=payload)
        
        assert response.status_code == 200
        rpc_response = response.json()
        
        assert "error" in rpc_response
        assert rpc_response["error"]["code"] == -32602
        assert "invalid params" in rpc_response["error"]["message"].lower()
    
    async def test_parse_error_for_invalid_json(self, test_client: AsyncClient):
        """
        Test error code -32700 for malformed JSON
        
        Per spec Section 8.1:
        "Invalid JSON payload"
        """
        # Send invalid JSON
        response = await test_client.post(
            "/a2a",
            content=b"{invalid json}",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 400
        rpc_response = response.json()
        
        assert "error" in rpc_response
        assert rpc_response["error"]["code"] == -32700
        assert "parse error" in rpc_response["error"]["message"].lower()


class TestA2ACompliance:
    """Test A2A protocol compliance per spec Section 11"""
    
    async def test_json_rpc_version_is_2_0(self, test_client: AsyncClient):
        """All JSON-RPC messages must specify version 2.0"""
        payload = {
            "jsonrpc": "2.0",
            "id": "test",
            "method": "message/send",
            "params": {
                "message": {
                    "role": "user",
                    "parts": [{"kind": "text", "text": "test"}],
                    "messageId": str(uuid.uuid4())
                }
            }
        }
        
        response = await test_client.post("/a2a", json=payload)
        rpc_response = response.json()
        
        assert rpc_response["jsonrpc"] == "2.0"
    
    async def test_content_type_is_application_json(self, test_client: AsyncClient):
        """Per spec Section 3.2.1, Content-Type must be application/json"""
        payload = {
            "jsonrpc": "2.0",
            "id": "test",
            "method": "message/send",
            "params": {
                "message": {
                    "role": "user",
                    "parts": [{"kind": "text", "text": "test"}],
                    "messageId": str(uuid.uuid4())
                }
            }
        }
        
        response = await test_client.post(
            "/a2a",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
