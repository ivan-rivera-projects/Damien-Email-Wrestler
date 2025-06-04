# Damien MCP Minimal Server

A minimal, Claude MAX-compatible MCP server for Damien Email Wrestler that replaces the current broken implementation.

## Overview

This minimal server is designed to:
- ✅ Provide Claude MAX compatibility without crashes
- ✅ Start with a stable foundation (no tools initially)
- ✅ Enable gradual tool expansion through phases
- ✅ Preserve all existing backend functionality

## Current Status

**Phase: Foundation Complete**
- ✅ Basic MCP server structure implemented
- ✅ Proper error handling and logging
- ✅ Graceful shutdown mechanisms
- ✅ Claude MAX protocol compliance
- 🚫 No tools implemented yet (by design)

## Quick Start

### Prerequisites
- Node.js 18+
- Existing Damien Python backend running on port 8892

### Installation
```bash
cd damien-mcp-minimal
npm install
```

### Testing
```bash
npm test
```

### Running
```bash
npm start
```

## Architecture

```
Claude Desktop ←→ [Minimal MCP Server] ←→ [Python FastAPI Backend]
                        (this)                   (unchanged)
```

The minimal server acts as a clean, compatible adapter layer while preserving all existing backend infrastructure.

## Phase Expansion Plan

1. **Phase 1**: 5 core tools (damien_list_emails, damien_get_email_details, etc.)
2. **Phase 2**: 7 basic action tools (trash, label, mark, etc.)
3. **Phase 3**: 5 thread management tools
4. **Phase 4**: 5 rule management tools
5. **Phase 5**: 9 AI intelligence tools
6. **Phase 6**: 6 account settings tools

**Total**: All 40 original tools restored across 6 phases

## Files Structure

```
damien-mcp-minimal/
├── server.js              # Main MCP server implementation
├── package.json           # Dependencies and scripts
├── core/                  # Core functionality (future)
├── config/                # Configuration management (future)
├── tests/                 # Test suite
│   └── basic-test.js      # Foundation tests
└── README.md              # This file
```

## Next Steps

1. Execute Task 2: Implement Backend Communication Client
2. Execute Task 3: Implement Tool Phase Management System
3. Execute Task 4: Implement Core MCP Request Handlers
4. Test Phase 1 with 5 core tools
5. Migrate Claude Desktop configuration

## Verification

The foundation is complete when:
- ✅ Server compiles without errors
- ✅ Basic tests pass
- ✅ Server can be started and stopped gracefully
- ✅ MCP protocol structure is correct
- ✅ Ready for tool implementation

**Status: Foundation Complete ✅**
