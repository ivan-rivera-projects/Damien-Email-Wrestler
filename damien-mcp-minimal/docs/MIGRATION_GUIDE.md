# Damien MCP Migration Guide

This guide provides detailed instructions for migrating from the current MCP server implementation to the new minimal MCP server, which resolves Claude Desktop compatibility issues.

## Overview

The minimal MCP server is a complete rewrite of the MCP adapter layer, designed to be Claude MAX-compatible and prevent the crashes experienced with the current implementation. It preserves all backend functionality while providing a more stable and efficient interface.

### Key Benefits

- **Claude MAX Compatibility**: Prevents crashes in Claude Desktop
- **Improved Performance**: Optimized caching and request handling
- **Direct Tool Access**: Provides immediate access to all 46 tools
- **Comprehensive Testing**: Validates all tool functionality
- **Full Rollback Capability**: Safe migration with easy reversal if needed

## Prerequisites

Before beginning the migration, ensure you have:

1. **Node.js 18+**: Required for running the minimal server
2. **jq**: Recommended for JSON manipulation (optional but helpful)
3. **Claude Desktop**: Installed and previously working with the original MCP server
4. **Backend Server**: Running and accessible (default: http://localhost:8892)

## Migration Process

### Step 1: Backup Current Configuration

The migration script automatically backs up your current configuration, but you can also do this manually:

```bash
mkdir -p damien-mcp-minimal/backups
cp "~/Library/Application Support/Claude Desktop/config.json" damien-mcp-minimal/backups/claude_desktop_config_backup.json
```

### Step 2: Run Migration Script

The easiest way to migrate is using the provided script:

```bash
cd damien-mcp-minimal
chmod +x scripts/migrate-to-minimal.sh
./scripts/migrate-to-minimal.sh
```

This script will:
1. Back up your current configuration
2. Stop any running MCP services
3. Start the minimal MCP server
4. Update Claude Desktop configuration
5. Validate the migration

### Step 3: Verify Migration

After migration, verify that:

1. Claude Desktop can connect to the minimal MCP server
2. Basic email functionality works through Claude MAX
3. No crashes occur during normal usage

The validation script runs these checks automatically, but you should also manually verify functionality with Claude Desktop.

## Manual Migration

If you prefer to migrate manually, follow these steps:

1. **Start the minimal MCP server**:
   ```bash
   cd damien-mcp-minimal
   npm install
   npm start
   ```

2. **Update Claude Desktop configuration**:
   - Open Claude Desktop config file: `~/Library/Application Support/Claude Desktop/config.json`
   - Update the MCP URL to point to the minimal server: `"mcpUrl": "http://localhost:8893"`
   - Save the file

3. **Restart Claude Desktop**:
   - Close and reopen Claude Desktop to apply the new configuration

## Troubleshooting

### Common Issues

1. **Claude Desktop can't connect to MCP server**:
   - Verify minimal server is running on the correct port
   - Check Claude Desktop configuration has the correct URL
   - Ensure no firewall is blocking the connection

2. **Tools not appearing in Claude MAX**:
   - Verify backend server is running
   - Check minimal server logs for connection errors
   - Restart the minimal server

3. **Migration script fails**:
   - Check error messages for specific issues
   - Try running with `--verbose` for more detailed output
   - Attempt manual migration steps

### Rollback Procedure

If you need to revert to the original MCP server:

```bash
cd damien-mcp-minimal
./scripts/rollback-from-minimal.sh
```

This will:
1. Stop the minimal MCP server
2. Restore Claude Desktop's original configuration
3. Verify the rollback was successful

You can also specify a particular backup to restore:

```bash
./scripts/rollback-from-minimal.sh --list            # List available backups
./scripts/rollback-from-minimal.sh --backup-id ID    # Restore specific backup
```

## Tool Access

The minimal MCP server provides direct access to all Damien tools:

**All 46 Tools Available**: Complete email management suite immediately accessible
- Email Management: List, get details, trash, label, mark read/unread
- Draft Operations: Create, update, send, delete drafts
- Thread Management: Full conversation-level operations
- Rule Management: Email automation and filtering
- AI Intelligence: Advanced analysis and insights
- Account Settings: Configuration management

The server automatically discovers and exposes all available tools from the backend without any configuration needed.

## Performance Monitoring

The minimal server includes built-in performance monitoring:

- Response time tracking for each tool execution
- Error rate monitoring
- Cache hit rate analysis

To view performance metrics:

```bash
cd damien-mcp-minimal
npm run benchmark
```

## Advanced Configuration

See the [Configuration Guide](./CONFIGURATION.md) for detailed information on configuring the minimal MCP server, including:

- Environment variables
- Logging options
- Performance tuning
- Deployment settings

## Support

If you encounter issues during migration:

1. Check the logs: `damien-mcp-minimal/logs/server.log`
2. Run validation tests: `./scripts/validate-migration.sh --verbose`
3. Open an issue in the project repository with detailed information about the problem
