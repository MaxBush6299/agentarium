# AI Agents Demo - Multi-Agent LLM Application

A production-ready multi-agent AI application demonstrating advanced patterns for agent orchestration, real-time streaming, and tool integration.

## 📁 Project Structure

```
agent-demo/
├── dev-docs/                    # Development documentation & project plans
│   ├── 01-project-plan-part1.md # Phase 1: Foundation & Architecture
│   ├── 01-project-plan-part2.md # Phase 2: Implementation Plan
│   ├── 01-project-plan-part3.md # Phase 3: Testing & Deployment
│   ├── 02-architecture-part1.md # System Architecture Overview
│   ├── 02-architecture-part2.md # Component Design & Patterns
│   ├── 02-architecture-part3.md # Data Models & Integration
│   └── ...                      # Additional documentation
│
├── infra/                       # Infrastructure as Code (Bicep)
│   ├── main.bicep              # Main infrastructure template
│   ├── parameters/              # Environment-specific parameters
│   │   ├── dev.bicepparam
│   │   └── prod.bicepparam
│   └── modules/                # Bicep modules
│       ├── container-apps.bicep
│       ├── cosmos-db.bicep
│       ├── key-vault.bicep
│       ├── network.bicep
│       ├── observability.bicep
│       ├── private-endpoints.bicep
│       └── storage.bicep
│
├── 01-project-plan-part1.md    # Project plan & timeline
├── 01-project-plan-part2.md    # Implementation details
├── 01-project-plan-part3.md    # Testing & deployment strategy
├── 02-architecture-part1.md    # Architecture overview
├── 02-architecture-part2.md    # Component design
├── 02-architecture-part3.md    # Data models
├── 03-overview.md              # Project overview
├── .env.template               # Environment variables template
└── README.md                   # This file
```

## 🎯 Project Goals

- Build a production-ready multi-agent AI system
- Demonstrate real-time streaming with trace visualization
- Integrate multiple tool types (MCP, OpenAPI, A2A protocols)
- Deploy to Azure with full observability

## 📚 Documentation

All project documentation is in the `dev-docs/` folder:

- **Project Plans**: Phase 1, 2, and 3 timelines and deliverables
- **Architecture**: System design, component patterns, and integration flows
- **Development**: Setup guides, API specifications, and best practices

## 🏗️ Architecture

The system consists of:

- **Backend**: FastAPI with real-time streaming support
- **Frontend**: React TypeScript with MSAL authentication
- **Infrastructure**: Azure-hosted with Cosmos DB, OpenAI, and observability

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- Azure CLI
- Git

### Setup

1. **Clone and navigate to project**
   ```bash
   git clone https://github.com/MaxBush6299/multiagentdemo.git
   cd multiagentdemo
   ```

2. **Review documentation**
   ```bash
   # Start with these docs in dev-docs/ folder
   - Read 01-project-plan-part1.md for overview
   - Read 02-architecture-part1.md for system design
   ```

3. **Deploy infrastructure** (when ready)
   ```bash
   az login
   az deployment sub create \
     --template-file infra/main.bicep \
     --parameters infra/parameters/dev.bicepparam
   ```

## 📖 Key Documentation Files

| File | Purpose |
|------|---------|
| `dev-docs/01-project-plan-*.md` | Project timeline, phases, and deliverables |
| `dev-docs/02-architecture-*.md` | System design, components, and patterns |
| `03-overview.md` | High-level project overview |
| `infra/README.md` | Infrastructure deployment guide |

## 🔧 Technology Stack

- **Backend**: Python, FastAPI, Cosmos DB
- **Frontend**: React, TypeScript, Vite
- **Infrastructure**: Azure, Bicep, Docker
- **AI/ML**: Azure OpenAI, LangChain patterns
- **DevOps**: GitHub Actions, Azure Container Registry

## 📊 Project Status

**Phase 1** (Complete): Infrastructure as Code ✅
- Bicep templates for all Azure resources
- Parameter files for dev/prod environments
- Network and security configuration

**Phase 2** (In Progress): Agent Implementation & Core Features
- ✅ Backend FastAPI scaffolding with streaming support
- ✅ Frontend React TypeScript with agent management UI
- ✅ Tool integration framework (MCP, OpenAPI, A2A protocols)
- ✅ **Agent Factory Pattern**: Dynamic agent creation from metadata
- ✅ **Auto-Card Generation**: A2A protocol cards auto-generated from agent metadata
- ✅ **Cosmos DB Persistence**: Agent configurations stored and retrieved reliably
- ✅ **User-Defined Capabilities**: Agents can be tagged with custom capabilities
- ✅ **Capabilities Editor UI**: Full React component for managing agent capabilities (FluentUI v5)
- ✅ **Agent Lifecycle**: Complete create/read/update/delete flows for agents
- ✅ **Tool Management**: UI for configuring agent tools and parameters

**Phase 3** (Planned): Testing & Deployment
- CI/CD pipelines
- Load testing
- Production deployment
- Advanced observability and tracing

## 🎯 Key Features Implemented

### Backend (`/backend`)
- **AgentFactory** (`src/agents/factory.py`): Dynamic agent instantiation from metadata
- **AgentRepository**: Cosmos DB persistence layer for agent configurations
- **A2A Protocol** (`src/a2a/`): Auto-generating agent discovery cards with:
  - Automatic tool-to-skill mapping
  - User-defined capabilities in metadata
  - Combined endpoint for multi-agent discovery
  - Graceful fallback from manual cards to auto-generation
- **REST API** (`src/api/agents.py`): Full CRUD operations for agent management
- **Tool Registry** (`src/tools/registry.py`): Extensible tool loading system

### Frontend (`/frontend`)
- **Agent Management Pages**:
  - Agent list view with filtering
  - Agent detail/edit view with full configuration
  - Agent creation workflow
- **CapabilitiesEditor Component** (`src/components/agents/CapabilitiesEditor.tsx`):
  - Add/remove capabilities with tag UI
  - Input validation and duplicate prevention
  - Fully integrated with react-hook-form
- **ToolConfigurator Component**: Manage agent tools and parameters
- **Form Validation**: Zod schemas ensuring data integrity
- **Real-time Persistence**: Changes saved immediately to backend

### Infrastructure (`/infra`)
- Bicep templates for complete Azure deployment
- Cosmos DB for reliable persistence
- Container Apps for scalable deployment
- Key Vault for secrets management
- Full network security configuration

## 🧪 Testing

All major features have been tested and verified:
- ✅ Agent creation and persistence across server restarts
- ✅ User-defined capabilities persist to Cosmos DB
- ✅ Capabilities editor component (add/remove with validation)
- ✅ A2A card auto-generation from agent metadata
- ✅ Full CRUD operations via REST API
- ✅ Frontend form submission and data loading
- ✅ Capabilities integrated into agent edit workflow
- ✅ Custom tool registration and persistence
- ✅ Dynamic model selection via API
- ✅ Agent configuration changes survive restarts

## 📋 Recent Implementation

### Phase 3.6: User-Defined Capabilities (Latest)
- ✅ **CapabilitiesEditor Component** - FluentUI-based UI for managing agent capabilities
  - Add new capabilities with input field + button
  - Remove capabilities with tag dismissal
  - Input validation (no empty, no duplicates)
  - Enter key support for quick addition
  - Full form integration with react-hook-form

- ✅ **Capabilities Integration** - Complete workflow
  - Load capabilities when editing existing agent
  - Include capabilities in PUT request to backend
  - Capabilities persist to Cosmos DB
  - Capabilities returned in API responses

- ✅ **A2A Protocol Support** - Capabilities exposed for discovery
  - Included in combined agent card metadata
  - Visible in agent skills as tags
  - Enables inter-agent capability discovery

### Phase 3.5: Model Library & Agent Persistence (Previous)
- ✅ **Custom Tool Persistence** - Tools stored in Cosmos DB
- ✅ **Agent Update Persistence** - Fixed Cosmos DB update operations
- ✅ **Dynamic Model Selection** - REST API for querying available deployments
- ✅ **ModelSelector Component** - React component with automatic model loading

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes and commit: `git commit -m "feat: description"`
3. Push to GitHub: `git push origin feature/your-feature`
4. Create a Pull Request

### Development Guidelines
- Follow the patterns established in existing code
- Test capabilities through the UI
- Update documentation for new features
- Ensure backend and frontend changes are consistent

## 📝 License

[Add your license here]

## 📞 Support

For questions or issues, refer to the documentation in `dev-docs/` or create a GitHub issue.

---

**Repository**: https://github.com/MaxBush6299/multiagentdemo  
**Status**: Phase 1 Complete, Phase 2 In Progress (Agent Factory, Auto-Card Generation, Capabilities Management ✅)
