# Agentarium - Frontend

React + TypeScript + Vite frontend application for Agentarium.

## Overview

This is a modern React application that provides:
- Interactive chat interface with agents
- Agent management and configuration
- Real-time streaming responses via Server-Sent Events (SSE)
- Azure Entra ID authentication via MSAL
- Tool execution tracing and visualization
- A2A (Agent-to-Agent) communication visualization

## Technology Stack

- **React 18.2** - UI framework
- **TypeScript 5.3** - Type-safe development
- **Vite 5.0** - Build tool and dev server
- **React Router 6.20** - Client-side routing
- **MSAL React 1.18** - Azure Entra ID authentication
- **Fluent UI React 9.48** - Component library
- **Axios 1.6** - HTTP client
- **Zustand 4.4** - State management
- **OpenTelemetry** - Observability (integrated with backend tracing)

## Prerequisites

- Node.js 18+ and npm/yarn
- Access to backend API (running on `http://localhost:8000`)
- Azure Entra ID tenant ID and app registration

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

Copy `.env.example` to `.env.local` and update with your values:

```bash
cp .env.example .env.local
```

Update the following variables:
- `VITE_AUTH_CLIENT_ID` - Azure Entra ID app registration client ID
- `VITE_AUTH_AUTHORITY` - Azure Entra ID tenant authority URL
- `VITE_AUTH_REDIRECT_URI` - Redirect URI after authentication
- `VITE_AUTH_SCOPES` - API scopes for the backend
- `VITE_API_URL` - Backend API URL (default: `http://localhost:8000/api`)

### 3. Development Server

Start the development server:

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

The dev server includes:
- Hot Module Reloading (HMR)
- Proxy to backend API (`/api` requests forward to backend)
- Source maps for debugging
- TypeScript checking

### 4. Building for Production

Build the application:

```bash
npm run build
```

Output will be in the `dist/` directory.

Preview the production build locally:

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── pages/                  # Page components
│   │   ├── AgentsDirectory.tsx # Agent listing and selection
│   │   ├── AgentChat.tsx       # Chat interface template
│   │   └── Login.tsx           # Authentication page
│   │
│   ├── components/             # Reusable components
│   │   ├── chat/               # Chat-related components
│   │   │   ├── MessageStream.tsx
│   │   │   ├── TracePanel.tsx
│   │   │   ├── InputBox.tsx
│   │   │   └── ExportButton.tsx
│   │   │
│   │   ├── agents/             # Agent management components
│   │   │   ├── AgentCard.tsx
│   │   │   ├── AgentEditor.tsx
│   │   │   └── ModelSelector.tsx
│   │   │
│   │   ├── navigation/         # Navigation components
│   │   │   ├── Sidebar.tsx
│   │   │   └── TopNav.tsx
│   │   │
│   │   └── common/             # Common components
│   │       ├── Loading.tsx
│   │       └── ErrorBoundary.tsx
│   │
│   ├── services/               # API services
│   │   ├── api.ts             # Axios client with interceptors
│   │   ├── authService.ts     # MSAL authentication
│   │   ├── agentsService.ts   # Agent CRUD operations
│   │   ├── chatService.ts     # Chat and SSE streaming
│   │   └── index.ts           # Service exports
│   │
│   ├── hooks/                  # Custom React hooks
│   │   ├── useAuth.ts         # Authentication state
│   │   ├── useChat.ts         # Chat state and operations
│   │   ├── useAgents.ts       # Agent management
│   │   ├── useSSE.ts          # Server-Sent Events
│   │   └── index.ts           # Hook exports
│   │
│   ├── types/                  # TypeScript interfaces
│   │   ├── agent.ts           # Agent data structures
│   │   └── chat.ts            # Chat and trace structures
│   │
│   ├── styles/                 # Global styles
│   │   └── globals.css        # Global stylesheet
│   │
│   ├── config.ts              # Runtime configuration
│   ├── App.tsx                # Main application component
│   ├── main.tsx               # Application entry point
│   └── vite-env.d.ts          # Vite type definitions
│
├── public/                     # Static assets
├── tests/                      # Test files
├── Dockerfile                  # Container image
├── package.json               # Dependencies and scripts
├── tsconfig.json              # TypeScript configuration
├── tsconfig.node.json         # Node-specific config
├── vite.config.ts             # Vite configuration
├── .env.example               # Environment template
└── .gitignore                 # Git ignore rules
```

## Key Features

### Authentication
- MSAL integration for Azure Entra ID authentication
- Automatic token acquisition and refresh
- Role-based access control from backend claims

### Chat Interface
- Real-time message streaming via SSE
- Support for tool invocations and tracing
- Export chat history as JSON
- Thread-based conversation management

### Agent Management
- Browse and select agents
- View agent configuration (model, temperature, tools, etc.)
- Create/edit/delete agents (admin only)
- Search agents by name or description

### Observability
- OpenTelemetry integration with backend traces
- Trace visualization panel
- A2A communication visualization
- Performance metrics

## API Integration

The frontend communicates with the backend API through:

### Agents Endpoint
- `GET /agents` - List agents
- `GET /agents/{id}` - Get agent details
- `POST /agents` - Create agent (admin)
- `PUT /agents/{id}` - Update agent (admin)
- `DELETE /agents/{id}` - Delete agent (admin)

### Chat Endpoint
- `POST /chat/stream` - Stream chat with SSE
- `GET /chat/threads/{id}` - Get thread history
- `POST /chat/threads` - Create new thread
- `DELETE /chat/threads/{id}` - Delete thread

All endpoints require Bearer token authentication (except `/health`).

## Development Workflow

### 1. Component Development
Create components in `src/components/` with TypeScript interfaces defined in `src/types/`.

### 2. Service Integration
Add API calls in `src/services/` and expose through service index.

### 3. State Management
Use custom hooks in `src/hooks/` for component state. Use Zustand for global state if needed.

### 4. Testing
Add tests next to components with `.test.tsx` extension.

### 5. Type Safety
Keep TypeScript strict mode enabled. Define all types in `src/types/`.

## Troubleshooting

### "Cannot find module 'axios'"
Run `npm install` to ensure all dependencies are installed.

### "VITE_AUTH_CLIENT_ID not found"
Ensure `.env.local` is created and filled with correct values. Restart dev server after changes.

### Backend API connection refused
Verify backend is running on `http://localhost:8000` and dev server proxy is configured in `vite.config.ts`.

### Authentication redirect issues
Check redirect URI in Azure Entra ID app registration matches `VITE_AUTH_REDIRECT_URI`.

## Deployment

### Docker

Build container image:

```bash
docker build -t agent-demo-frontend .
```

Run container:

```bash
docker run -p 3000:3000 -e VITE_API_URL=http://backend:8000/api agent-demo-frontend
```

### Environment Configuration
The frontend only requires environment variables to be set at build time (they're compiled into the bundle).

For runtime configuration of API URL, use the `VITE_API_URL` environment variable during the build.

## Performance

- **Code Splitting** - Vite automatically chunks code
- **Lazy Loading** - Route-based code splitting with React Router
- **Tree Shaking** - Unused code removed at build time
- **Minification** - Production bundle minified with Terser
- **CSS Optimization** - Only used CSS included in bundle

## License

See LICENSE file in project root.

## Contributing

1. Create feature branch from `main`
2. Make changes with TypeScript strict mode enabled
3. Test locally with dev server
4. Commit with conventional commit messages
5. Push to GitHub and create pull request

## Next Steps

1. Install dependencies: `npm install`
2. Configure environment: `cp .env.example .env.local && edit .env.local`
3. Start development: `npm run dev`
4. Create page and component files as needed
5. Integrate with backend API
