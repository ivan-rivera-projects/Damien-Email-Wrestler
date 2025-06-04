# Damien MCP Minimal Server - Configuration Guide

This document provides detailed information on configuring and deploying the Damien MCP Minimal Server, a Claude MAX-compatible replacement for the original MCP server that caused crashes in Claude Desktop.

## Configuration Overview

The minimal server uses a robust configuration system with several layers:

1. **Default values** hardcoded in `config/claude-max-config.js`
2. **Environment variables** loaded from `.env` file
3. **Command-line arguments** for deployment and testing

## Environment Variables

The server supports the following environment variables:

### Core Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `DAMIEN_MCP_SERVER_URL` | URL of the backend FastAPI server | `http://localhost:8892` |
| `DAMIEN_MCP_SERVER_API_KEY` | API key for authentication | *See .env.example* |
| `DAMIEN_MCP_MINIMAL_PORT` | Port for the minimal MCP server | `8893` |

### Phase Management

| Variable | Description | Default |
|----------|-------------|---------|
| `DAMIEN_INITIAL_PHASE` | Initial phase to start with | `1` |
| `DAMIEN_PHASE_AUTO_PROGRESS` | Enable automatic phase progression | `false` |

### Request Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DAMIEN_DEFAULT_TIMEOUT` | Default timeout for requests (ms) | `30000` |
| `DAMIEN_HEALTH_CHECK_TIMEOUT` | Health check timeout (ms) | `5000` |
| `DAMIEN_MAX_RETRIES` | Maximum number of retries for failed requests | `3` |
| `DAMIEN_RETRY_DELAY` | Delay between retries (ms) | `1000` |
| `DAMIEN_TOOL_CACHE_DURATION` | Tool cache duration (ms) | `3600000` |

### Logging Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Log level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `VERBOSE_LOGGING` | Enable verbose logging | `false` |
| `DAMIEN_LOG_TO_FILE` | Enable logging to file | `false` |
| `DAMIEN_LOG_FILE_PATH` | Path to log file | `./logs/mcp-minimal.log` |

### Development Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `NODE_ENV` | Environment (development, production) | `production` |

### Deployment Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `CLAUDE_DESKTOP_CONFIG_PATH` | Path to Claude Desktop config.json | *OS-specific* |
| `DAMIEN_BACKUP_DIR` | Directory for backups | `./backups` |

## Setup Instructions

### Basic Setup

1. **Copy environment template**:
   ```bash
   cp .env.example .env
   ```

2. **Edit environment variables** in `.env`:
   ```bash
   # Update with your backend URL and API key
   DAMIEN_MCP_SERVER_URL=http://localhost:8892
   DAMIEN_MCP_SERVER_API_KEY=your_api_key_here
   ```

3. **Install dependencies**:
   ```bash
   npm install
   ```

4. **Start the server**:
   ```bash
   npm start
   ```

### Deployment

The deployment script automates the process of setting up the minimal server:

```bash
./scripts/deploy-minimal.sh
```

Options:
- `--dry-run`: Show what would be done without making changes
- `--force`: Skip confirmation prompts
- `--no-backup`: Skip backup steps (not recommended)
- `--no-test`: Skip connectivity tests
- `--help`: Show help message

### Rollback

If you need to revert to a previous configuration:

```bash
./scripts/rollback-minimal.sh
```

Options:
- `--backup-id ID`: Specify the backup ID (timestamp) to use
- `--list`: List available backups
- `--latest`: Use the most recent backup (default)
- `--dry-run`: Show what would be done without making changes
- `--force`: Skip confirmation prompts
- `--help`: Show help message

## Phase Configuration

The server implements a phase-based approach for tool rollout:

1. **Phase 1**: Essential core functionality (5 tools)
2. **Phase 2**: Basic email actions (7 tools)
3. **Phase 3**: Thread management (5 tools)
4. **Phase 4**: Rule management (5 tools)
5. **Phase 5**: AI intelligence (9 tools)
6. **Phase 6**: Account settings (6 tools)

To change the active phase:

```bash
# In .env file
DAMIEN_INITIAL_PHASE=2
```

## Troubleshooting

### Common Issues

1. **Server won't start**:
   - Check if the port is already in use
   - Verify environment variables in `.env`
   - Check logs for errors

2. **Claude Desktop can't connect**:
   - Verify Claude Desktop is configured to use the minimal server
   - Check that the server is running on the expected port
   - Verify firewall settings

3. **Tools not available**:
   - Check if backend server is running
   - Verify API key is correct
   - Check which phase is active
   - Clear tool cache by restarting the server

### Logs

Logs are written to stderr by default. To enable file logging:

```bash
# In .env file
DAMIEN_LOG_TO_FILE=true
DAMIEN_LOG_FILE_PATH=./logs/mcp-minimal.log
```

## Testing

Run tests to verify server functionality:

```bash
# Run basic tests
npm test

# Run all tests
npm run test:all

# Run specific test suites
npm run test:compat    # Claude MAX compatibility tests
npm run test:phase     # Phase progression tests
npm run test:integration # Integration tests
```

## Performance Benchmarking

Run performance benchmarks:

```bash
npm run benchmark
```

This will measure:
- Response times for tool list requests
- Memory usage
- Overall performance metrics
