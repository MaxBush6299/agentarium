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

**Phase 2** (In Progress): Agent Implementation
- Backend scaffolding
- Frontend scaffolding
- Tool integration (MCP, OpenAPI, A2A)

**Phase 3** (Planned): Testing & Deployment
- CI/CD pipelines
- Load testing
- Production deployment

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes and commit: `git commit -m "feat: description"`
3. Push to GitHub: `git push origin feature/your-feature`
4. Create a Pull Request

## 📝 License

[Add your license here]

## 📞 Support

For questions or issues, refer to the documentation in `dev-docs/` or create a GitHub issue.

---

**Repository**: https://github.com/MaxBush6299/multiagentdemo  
**Status**: Phase 1 Complete, Phase 2 In Progress
