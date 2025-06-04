# Damien MCP Migration Guide

This guide provides detailed instructions for migrating from the current MCP server implementation to the new minimal MCP server, which resolves Claude Desktop compatibility issues.

## Overview

The minimal MCP server is a complete rewrite of the MCP adapter layer, designed to be Claude MAX-compatible and prevent the crashes experienced with the current implementation. It preserves all backend functionality while providing a more stable and efficient interface.

### Key Benefits

- **Claude MAX Compatibility**: Prevents crashes in Claude Desktop
- **Improved Performance**: Optimized caching and request handling
- **Phased Tool Deployment**: Gradually introduces functionality across 6 phases
- **Comprehensive Testing**: Validates functionality at each phase
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

## Phase Progression

The minimal MCP server implements a phased approach to tool deployment:

1. **Phase 1**: Essential core functionality (5 tools)
   - damien_list_emails, damien_get_email_details, damien_create_draft, damien_send_draft, damien_list_drafts

2. **Phase 2**: Basic actions (7 tools)
   - damien_trash_emails, damien_label_emails, damien_mark_emails, damien_update_draft, damien_delete_draft, damien_get_draft_details, damien_delete_emails_permanently

3. **Phase 3-6**: Additional tools (23 tools)
   - Thread management, rule management, AI intelligence, account settings

To change the active phase, set the `DAMIEN_INITIAL_PHASE` environment variable:

```bash
# In .env file
DAMIEN_INITIAL_PHASE=2  # Enable Phase 2 tools
```

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
