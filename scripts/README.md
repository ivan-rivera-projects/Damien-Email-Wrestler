# 📜 Damien Email Wrestler Scripts

This directory contains utility scripts for managing the Damien Email Wrestler services.

## 🚀 Available Scripts

### `start-all.sh`
**Purpose**: Start both the Damien MCP Server and Smithery Adapter

```bash
./scripts/start-all.sh
```

This script:
- Synchronizes environment variables using `sync-env.sh`
- Checks if services are already running (won't start duplicates)
- Starts the Damien MCP Server on port 8892
- Starts the Smithery Adapter on port 8081
- Waits for both services to be healthy
- Creates log files in the `logs/` directory
- Provides clear status output

**Output files:**
- `logs/damien-mcp-server.log` - MCP Server logs
- `logs/smithery-adapter.log` - Smithery Adapter logs

### `stop-all.sh`
**Purpose**: Stop all running Damien services

```bash
./scripts/stop-all.sh
```

This script:
- Stops processes on ports 8892 and 8081
- Cleans up any remaining Damien-related processes
- Provides confirmation of stopped services

### `status.sh`
**Purpose**: Check the health and status of all services

```bash
./scripts/status.sh
```

This script shows:
- Whether each service is running
- Health check results
- Number of available tools
- Connection status between services
- Log file information

### `test.sh`
**Purpose**: Run the complete test suite

```bash
./scripts/test.sh
```

This script:
- Checks that both services are running (fails early if not)
- Verifies configuration files exist
- Tests health endpoints
- Validates tool discovery
- Provides a summary of passed/failed tests

**Prerequisites**: Both services must be running. Use `start-all.sh` first.

### `sync-env.sh`
**Purpose**: Synchronize environment variables across all components

```bash
./scripts/sync-env.sh
```

This script:
- Reads the API key and other configuration from the root `.env` file
- Updates all component-specific `.env` files with consistent values
- Ensures all services use the same authentication credentials
- Prevents API key mismatch issues

**When to use**: After changing the root `.env` file or if experiencing authentication errors between services.

### Typical Workflow

1. **Start services:**
   ```bash
   ./scripts/start-all.sh
   ```

2. **Check status:**
   ```bash
   ./scripts/status.sh
   ```

3. **Run tests:**
   ```bash
   ./scripts/test.sh
   ```

4. **Stop services when done:**
   ```bash
   ./scripts/stop-all.sh
   ```

### API Key Synchronization

If you update the API key in the root `.env` file:

1. **Sync environment variables:**
   ```bash
   ./scripts/sync-env.sh
   ```

2. **Restart services:**
   ```bash
   ./scripts/stop-all.sh
   ./scripts/start-all.sh
   ```

## 🚨 Troubleshooting

### Services won't start
- Check if ports 8892 or 8081 are already in use: `lsof -i :8892,8081`
- Review log files in the `logs/` directory
- Ensure all dependencies are installed in both server directories

### Tests are failing
- Run `./scripts/status.sh` to check service health
- Ensure both services are running: `./scripts/start-all.sh`
- Check that `credentials.json` exists in the project root
- Verify `.env` file is properly configured

### Can't stop services
- Use `./scripts/stop-all.sh` which handles stubborn processes
- As a last resort: `killall -9 node` (warning: kills ALL Node.js processes)

## 📝 Script Requirements

All scripts require:
- Bash shell (included in macOS/Linux, use Git Bash on Windows)
- `curl` for health checks
- `lsof` for port checking (macOS/Linux)
- Node.js and npm installed
- Proper directory structure with both server directories

## 🔧 Customization

You can modify these scripts for your needs:
- Change ports in the scripts and corresponding `.env` files
- Adjust health check timeouts
- Add additional logging or notifications
- Integrate with process managers like PM2 or systemd

## 📍 Important Paths

From the project root:
- MCP Server: `./damien-mcp-server/`
- Smithery Adapter: `./damien-smithery-adapter/`
- Logs: `./logs/`
- Configuration: `./.env`
- Credentials: `./credentials.json`
