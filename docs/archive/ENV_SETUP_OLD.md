# Environment Configuration

The Damien Email Wrestler system requires several environment variables to be set consistently across multiple components. To ensure proper configuration:

## Initial Setup

1. Copy the example environment file to create your own:
   ```bash
   cp .env.example .env
   ```

2. Generate a secure API key:
   ```bash
   # Generate a random 32-byte hex string for your API key
   openssl rand -hex 32
   ```

3. Update the `.env` file with your API key and other required values.

## Maintaining Configuration Sync

The system includes a sync script that ensures all components use the same environment variables:

- **Automatic sync**: The `start-all.sh` script automatically runs `sync-env.sh` to synchronize environment variables across components.
  
- **Manual sync**: If you update the root `.env` file, you can manually sync the changes:
  ```bash
  ./scripts/sync-env.sh
  ```

## Troubleshooting

If you encounter authentication errors between services:

1. Check if the API key is consistent across all components:
   ```bash
   grep DAMIEN_MCP_SERVER_API_KEY .env damien-mcp-server/.env damien-smithery-adapter/.env
   ```

2. Run the sync script to fix any discrepancies:
   ```bash
   ./scripts/sync-env.sh
   ```

3. Restart all services:
   ```bash
   ./scripts/stop-all.sh && ./scripts/start-all.sh
   ```
