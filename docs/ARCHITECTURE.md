# Damien Platform Architecture

## Overview

The Damien Platform is a comprehensive email management solution that enables AI assistants like Claude to interact with Gmail accounts through advanced filtering, organization, and automation capabilities.

## Architecture Components

### 1. Damien CLI (`damien-cli/`)
**Purpose**: Core Gmail management logic and rule-based automation engine
**Technologies**: Python 3.13+, Poetry, Gmail API
**Key Features**:
- Gmail API integration with OAuth2 authentication
- Rule-based email filtering and automation
- Bulk email operations with safety mechanisms
- Comprehensive logging and error handling

### 2. Damien MCP Server (`damien-mcp-server/`)
**Purpose**: Model Context Protocol adapter for AI assistant integration
**Technologies**: Python 3.13+, FastAPI, DynamoDB
**Key Features**:
- 28 MCP tools for complete Gmail management
- Session context management via DynamoDB
- Secure authentication and validation
- RESTful API with comprehensive error handling

### 3. Damien Smithery Adapter (`damien-smithery-adapter/`)
**Purpose**: Smithery SDK integration for AI assistant discovery
**Technologies**: Node.js 18+, TypeScript, Smithery SDK
**Key Features**:
- Smithery Registry integration
- MCP protocol bridging
- Tool discovery and registration
- Standardized AI assistant integration

## Data Flow

```
AI Assistant (Claude) → Smithery Adapter → MCP Server → Damien CLI → Gmail API
                    ↑                   ↑             ↑
                    └─ Registry ────────┴─ DynamoDB ──┴─ Local Storage
```

## Component Interactions

1. **AI Assistant** sends natural language requests
2. **Smithery Adapter** translates to MCP protocol
3. **MCP Server** validates and routes requests
4. **Damien CLI** executes Gmail operations
5. **Results** flow back through the chain

## Security Model

- **OAuth2 Authentication** for Gmail API access
- **API Key Authentication** between components
- **Session Management** via DynamoDB with TTL
- **Input Validation** at every layer
- **Audit Logging** for all operations

## Deployment Architecture

- **Local Development**: All components run locally
- **Production**: Docker Compose orchestration
- **Scaling**: Individual component scaling
- **Monitoring**: Comprehensive logging and health checks

For detailed component documentation, see individual component README files.
