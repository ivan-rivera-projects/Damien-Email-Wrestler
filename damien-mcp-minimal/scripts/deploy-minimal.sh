#!/bin/bash
#
# Deployment Script for Damien MCP Minimal Server
#
# This script handles deployment of the minimal MCP server,
# including updating Claude Desktop configuration, backing up
# existing configuration, and testing connectivity.
#
# Usage:
#   ./deploy-minimal.sh [options]
#
# Options:
#   --dry-run       Show what would be done without making changes
#   --force         Skip confirmation prompts
#   --no-backup     Skip backup steps (not recommended)
#   --no-test       Skip connectivity tests
#   --help          Show this help message
#

# Set script to exit on any error
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
DRY_RUN=false
FORCE=false
SKIP_BACKUP=false
SKIP_TEST=false

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --dry-run)
      DRY_RUN=true
      ;;
    --force)
      FORCE=true
      ;;
    --no-backup)
      SKIP_BACKUP=true
      ;;
    --no-test)
      SKIP_TEST=true
      ;;
    --help)
      echo "Usage: ./deploy-minimal.sh [options]"
      echo ""
      echo "Options:"
      echo "  --dry-run       Show what would be done without making changes"
      echo "  --force         Skip confirmation prompts"
      echo "  --no-backup     Skip backup steps (not recommended)"
      echo "  --no-test       Skip connectivity tests"
      echo "  --help          Show this help message"
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown parameter: $1${NC}"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
  shift
done

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
# Go to the project root directory
cd "$SCRIPT_DIR/.."

# Import .env file if it exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
elif [ -f ./damien-mcp-minimal/.env ]; then
  export $(grep -v '^#' ./damien-mcp-minimal/.env | xargs)
fi

# Configuration values
PROJECT_ROOT=$(pwd)
MINIMAL_DIR="$PROJECT_ROOT/damien-mcp-minimal"
BACKUP_DIR="${DAMIEN_BACKUP_DIR:-$MINIMAL_DIR/backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_PREFIX="damien_mcp_backup_$TIMESTAMP"

# Claude Desktop config path based on OS
if [ -z "$CLAUDE_DESKTOP_CONFIG_PATH" ]; then
  if [ "$(uname)" == "Darwin" ]; then
    # macOS
    CLAUDE_DESKTOP_CONFIG_PATH="$HOME/Library/Application Support/Claude Desktop/config.json"
  elif [ "$(uname)" == "Linux" ]; then
    # Linux
    CLAUDE_DESKTOP_CONFIG_PATH="$HOME/.config/Claude Desktop/config.json"
  elif [ "$(expr substr $(uname -s) 1 5)" == "MINGW" ] || [ "$(expr substr $(uname -s) 1 6)" == "CYGWIN" ]; then
    # Windows
    CLAUDE_DESKTOP_CONFIG_PATH="$APPDATA\\Claude Desktop\\config.json"
  else
    echo -e "${RED}Unsupported operating system${NC}"
    exit 1
  fi
fi

# Function to show what would be done in dry run mode
log_action() {
  if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}[DRY RUN]${NC} $1"
  else
    echo -e "${BLUE}$1${NC}"
  fi
}

# Function to ask for confirmation
confirm() {
  if [ "$FORCE" = true ]; then
    return 0
  fi
  
  read -p "$1 (y/n) " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    return 0
  else
    return 1
  fi
}

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}    Damien MCP Minimal Server Deployment    ${NC}"
echo -e "${BLUE}=========================================${NC}"

# Create backup directory if it doesn't exist
if [ "$SKIP_BACKUP" = false ]; then
  if [ ! -d "$BACKUP_DIR" ]; then
    log_action "Creating backup directory: $BACKUP_DIR"
    if [ "$DRY_RUN" = false ]; then
      mkdir -p "$BACKUP_DIR"
    fi
  fi
fi

# Step 1: Backup existing configuration
if [ "$SKIP_BACKUP" = false ]; then
  echo -e "\n${BLUE}Step 1: Backing up existing configuration${NC}"
  
  # Backup Claude Desktop config if it exists
  if [ -f "$CLAUDE_DESKTOP_CONFIG_PATH" ]; then
    CLAUDE_CONFIG_BACKUP="$BACKUP_DIR/${BACKUP_PREFIX}_claude_desktop_config.json"
    log_action "Backing up Claude Desktop config to: $CLAUDE_CONFIG_BACKUP"
    if [ "$DRY_RUN" = false ]; then
      cp "$CLAUDE_DESKTOP_CONFIG_PATH" "$CLAUDE_CONFIG_BACKUP"
    fi
  else
    echo -e "${YELLOW}Claude Desktop config not found at: $CLAUDE_DESKTOP_CONFIG_PATH${NC}"
    echo -e "${YELLOW}Skipping Claude Desktop config backup${NC}"
  fi
  
  # Backup any existing .env file
  if [ -f "$MINIMAL_DIR/.env" ]; then
    ENV_BACKUP="$BACKUP_DIR/${BACKUP_PREFIX}_env"
    log_action "Backing up .env file to: $ENV_BACKUP"
    if [ "$DRY_RUN" = false ]; then
      cp "$MINIMAL_DIR/.env" "$ENV_BACKUP"
    fi
  fi
fi

# Step 2: Verify minimal server configuration
echo -e "\n${BLUE}Step 2: Verifying minimal server configuration${NC}"

# Check if .env file exists, if not create from example
if [ ! -f "$MINIMAL_DIR/.env" ] && [ -f "$MINIMAL_DIR/.env.example" ]; then
  if confirm "No .env file found. Create one from .env.example?"; then
    log_action "Creating .env from .env.example"
    if [ "$DRY_RUN" = false ]; then
      cp "$MINIMAL_DIR/.env.example" "$MINIMAL_DIR/.env"
    fi
  else
    echo -e "${YELLOW}Skipping .env file creation${NC}"
  fi
fi

# Verify dependencies are installed
echo -e "\n${BLUE}Step 3: Installing dependencies${NC}"
log_action "Installing npm dependencies for minimal server"
if [ "$DRY_RUN" = false ]; then
  cd "$MINIMAL_DIR"
  npm install
  cd "$PROJECT_ROOT"
fi

# Step 4: Update Claude Desktop configuration
echo -e "\n${BLUE}Step 4: Updating Claude Desktop configuration${NC}"

if [ -f "$CLAUDE_DESKTOP_CONFIG_PATH" ]; then
  # Parse current config to extract MCP server URL
  if command -v jq &> /dev/null; then
    CURRENT_MCP_URL=$(jq -r '.mcpConfig.mcpUrl // "not-set"' "$CLAUDE_DESKTOP_CONFIG_PATH")
    log_action "Current MCP URL: $CURRENT_MCP_URL"
    
    # Only update if different from what we want
    NEW_MCP_URL="http://localhost:${DAMIEN_MCP_MINIMAL_PORT:-8893}"
    if [ "$CURRENT_MCP_URL" != "$NEW_MCP_URL" ]; then
      if confirm "Update Claude Desktop MCP URL to $NEW_MCP_URL?"; then
        log_action "Updating Claude Desktop config with new MCP URL: $NEW_MCP_URL"
        if [ "$DRY_RUN" = false ]; then
          # Create a temporary file
          TEMP_CONFIG=$(mktemp)
          jq ".mcpConfig.mcpUrl = \"$NEW_MCP_URL\"" "$CLAUDE_DESKTOP_CONFIG_PATH" > "$TEMP_CONFIG"
          mv "$TEMP_CONFIG" "$CLAUDE_DESKTOP_CONFIG_PATH"
        fi
      else
        echo -e "${YELLOW}Skipping Claude Desktop config update${NC}"
      fi
    else
      echo -e "${GREEN}Claude Desktop already configured with correct MCP URL${NC}"
    fi
  else
    echo -e "${YELLOW}jq command not found. Cannot parse Claude Desktop config.${NC}"
    echo -e "${YELLOW}Please manually update MCP URL in: $CLAUDE_DESKTOP_CONFIG_PATH${NC}"
  fi
else
  echo -e "${YELLOW}Claude Desktop config not found at: $CLAUDE_DESKTOP_CONFIG_PATH${NC}"
  echo -e "${YELLOW}Please manually configure Claude Desktop to use:${NC}"
  echo -e "${YELLOW}  MCP URL: http://localhost:${DAMIEN_MCP_MINIMAL_PORT:-8893}${NC}"
fi

# Step 5: Test minimal server connectivity
if [ "$SKIP_TEST" = false ]; then
  echo -e "\n${BLUE}Step 5: Testing minimal server connectivity${NC}"
  
  log_action "Starting minimal server for testing"
  if [ "$DRY_RUN" = false ]; then
    # Start the server in the background
    cd "$MINIMAL_DIR"
    node server.js > /dev/null 2>&1 &
    SERVER_PID=$!
    
    # Give it a moment to start
    sleep 2
    
    # Run a simple test
    echo -e "${BLUE}Running basic connectivity test...${NC}"
    if node tests/basic-test.js; then
      echo -e "${GREEN}✓ Basic connectivity test passed${NC}"
    else
      echo -e "${RED}✗ Basic connectivity test failed${NC}"
    fi
    
    # Kill the server
    kill $SERVER_PID
    cd "$PROJECT_ROOT"
  else
    echo -e "${YELLOW}[DRY RUN] Would run: node tests/basic-test.js${NC}"
  fi
fi

# Step 6: Provide instructions for running the server
echo -e "\n${BLUE}Step 6: Deployment complete${NC}"
echo -e "${GREEN}The minimal MCP server has been configured.${NC}"
echo -e "${GREEN}To start the server, run:${NC}"
echo -e "  cd $MINIMAL_DIR"
echo -e "  npm start"
echo ""
echo -e "${GREEN}If you need to restore the previous configuration:${NC}"
if [ "$SKIP_BACKUP" = false ]; then
  echo -e "  1. Restore Claude Desktop config from: $CLAUDE_CONFIG_BACKUP"
  if [ -f "$ENV_BACKUP" ]; then
    echo -e "  2. Restore .env file from: $ENV_BACKUP"
  fi
else
  echo -e "${YELLOW}No backups were created during this deployment.${NC}"
fi

# Print rollback script
echo -e "\n${BLUE}Rollback Script${NC}"
echo -e "To rollback this deployment, you can use:"
echo -e "${YELLOW}./scripts/rollback-minimal.sh --backup-id $TIMESTAMP${NC}"

echo -e "\n${GREEN}Deployment completed successfully!${NC}"
if [ "$DRY_RUN" = true ]; then
  echo -e "${YELLOW}This was a dry run. No changes were made.${NC}"
fi