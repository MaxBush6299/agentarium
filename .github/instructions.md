Project Overview

This project is a web application that demonstrates and manages AI agents using Microsoft’s Agent Framework SDK (aka.ms/agentframework). It includes:

A React (TypeScript) frontend for chatting with agents, viewing tool traces (invocations, inputs/outputs, statuses), and managing agents.

A Python (FastAPI) backend that hosts agents built with the agent_framework package, connects to MCP servers (e.g., Microsoft Learn MCP, Azure MCP Server, and a custom adventure-mcp), and exposes streaming endpoints.

Azure-only infrastructure (Azure Container Apps, Cosmos DB, Key Vault, App Insights, API Management, Azure OpenAI/AI Foundry).

Folder Structure



Libraries and Frameworks

Frontend: React (TypeScript), Fluent UI (design system), Vite, MSAL for Entra ID auth.

Backend: Python, FastAPI, agent_framework (Microsoft Agent Framework SDK), Azure SDKs, pydantic.

Data: Azure Cosmos DB (Core/NoSQL) for threads, runs, tool logs.

Tools/Orchestration:

MCP clients: Microsoft Learn MCP, Azure MCP Server, custom adventure-mcp

OpenAPI tools via Azure API Management (mocked placeholders for demo)

Observability: OpenTelemetry → Azure Monitor / App Insights.

Coding Standards
Frontend (TypeScript/React)

Use semicolons at the end of statements.

Use single quotes for strings.

Use function components with hooks; prefer arrow functions for callbacks.

Strong typing with TypeScript (no any in new code).

Keep UI state local; use lightweight stores or React Query for server state.

Backend (Python/FastAPI)

Follow PEP 8; format with black; lint with ruff.

Type-hint all public functions; validate I/O with pydantic models.

Encapsulate Agent Framework usage in /backend/agents and /backend/tools.

Never log secrets or model prompts that include user-sensitive data.

UI Guidelines

Use Fluent UI for a modern, accessible, Microsoft-aligned design.

Provide a light/dark mode toggle.

Chat Console includes: token-streaming transcript and a trace panel (tool calls, inputs/outputs, durations, statuses). Do not display hidden chain-of-thought; show concise reasoning summaries only.

Agents Management: list agents; edit system prompt, model/deployment, tools.

Testing Strategy

Unit Tests

Frontend: components, hooks, and utility functions (e.g., React Testing Library + Vitest).

Backend: handlers, repositories, utilities (pytest), with mocks for Azure services and MCP.

Integration Tests

Backend: spin up FastAPI test server; use Cosmos DB emulator or a test database; exercise agent runs end-to-end with agent_framework wired to mock MCP and APIM mock endpoints.

MCP: verify discovery and tool invocation flow against a local/contained MCP server (e.g., adventure-mcp running in a test container or subprocess).

OpenAPI tools: call APIM mock endpoints and assert schema/response handling.

Auth: test MSAL token flow in dev mode (bypass where necessary with test providers).

E2E (optional but recommended): Playwright to validate core user flows (login, chat, traces, manage agents).

CI: run unit tests on every PR; run integration tests on main or nightly; collect coverage; fail fast on lint/format errors.

Agent Framework Usage (Callout)

The backend must use the Microsoft Agent Framework SDK (agent_framework) to:

Define agents with system prompts, tool catalogs, and model bindings.

Register MCP tools/clients and optional exposure of agents as MCP tools/servers.

Stream responses to the frontend and record runs/steps in Cosmos DB.

Prefer the Responses API with GPT-5; fallback to GPT-4.1.

When committing, use [frontend] to deploy frontend code, [backend] for backend code, or [all] for both.