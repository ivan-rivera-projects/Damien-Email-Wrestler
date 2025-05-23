#!/bin/bash
cd /Users/ivanrivera/Downloads/AWS/DamienPlatform/damien-email-wrestler/damien-smithery-adapter

# Export environment variables
export DAMIEN_MCP_SERVER_URL="http://localhost:8892"
export DAMIEN_MCP_SERVER_API_KEY="ytest_api_key"
export SERVER_NAME="Damien Email Wrestler"
export SERVER_VERSION="1.0.0"
export NODE_ENV="development_no_registry"

# Create a logs directory if it doesn't exist
mkdir -p logs

# Run TypeScript compilation separately and redirect output to a log file
echo "Compiling TypeScript..." >&2
npx tsc > logs/tsc-output.log 2>&1
COMPILE_RESULT=$?

# Check if compilation was successful
if [ $COMPILE_RESULT -ne 0 ]; then
    echo "TypeScript compilation failed. See logs/tsc-output.log for details." >&2
    exit 1
fi

# Now run the server without TypeScript compilation
echo "Starting MCP server..." >&2
exec node dist/stdioServer.js "$@"