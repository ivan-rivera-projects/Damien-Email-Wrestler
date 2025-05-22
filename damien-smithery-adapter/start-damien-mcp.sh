#!/bin/bash
cd /Users/ivanrivera/Downloads/AWS/DamienPlatform/damien-email-wrestler/damien-smithery-adapter
export DAMIEN_MCP_SERVER_URL="http://localhost:8892"
export DAMIEN_MCP_SERVER_API_KEY="ytest_api_key"
export SERVER_NAME="Damien Email Wrestler"
export SERVER_VERSION="1.0.0"
export NODE_ENV="development_no_registry"
exec node dist/stdioServer.js "$@"
