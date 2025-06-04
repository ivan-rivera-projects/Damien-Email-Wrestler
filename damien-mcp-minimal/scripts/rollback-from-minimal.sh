#!/bin/bash
#
# Rollback Script for Damien MCP Minimal Server Migration
#
# This script performs a controlled rollback from the minimal MCP server
# to the original implementation, restoring the previous configuration.
#
# Usage:
#   ./rollback-from-minimal.sh [options]
#
# Options:
#   --backup-id ID  Specify the backup ID (timestamp) to use
#   --list          List available backups
#   --latest        Use the most recent backup (default)
#   --force         Skip confirmation prompts
#   --dry-run       Show what would be done without making changes
#   --help          Show this help message
#

# Set script to exit on any error
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default options
FORCE=false
DRY_RUN=false
LIST_BACKUPS=false
USE_LATEST=true
BACKUP_ID=""

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --backup-id)
      BACKUP_ID="$2"
      USE_LATEST=false
      shift
      ;;
    --list)
      LIST_BACKUPS=true
      ;;
    --latest)
      USE_LATEST=true
      ;;
    --force)
      FORCE=true
      ;;
    --dry-run)
      DRY_RUN=true
      ;;
    --help)
      echo "Usage: ./rollback-from-minimal.sh [options]"
      echo ""
      echo "Options:"
      echo "  --backup-id ID  Specify the backup ID (timestamp) to use"
      echo "  --list          List available backups"
      echo "  --latest        Use the most recent backup (default)"
      echo "  --force         Skip confirmation prompts"
      echo "  --dry-run       Show what would be done without making changes"
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
cd "$SCRIPT_DIR/../.."
PROJECT_ROOT=$(pwd)
MINIMAL_DIR="$PROJECT_ROOT/damien-mcp-minimal"
SMITHERY_DIR="$PROJECT_ROOT/damien-smithery-adapter"
BACKUP_DIR="${DAMIEN_BACKUP_DIR:-$MINIMAL_DIR/backups}"

# Import .env file if it exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Set configuration values
MINIMAL_PORT="${DAMIEN_MCP_MINIMAL_PORT:-8893}"
ORIGINAL_PORT="${DAMIEN_MCP_SERVER_PORT:-8892}"
SMITHERY_PORT="${SMITHERY_ADAPTER_PORT:-8081}"

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

# Function to check if a process is running on a port
check_port_in_use() {
  local port=$1
  if command -v lsof &> /dev/null; then
    if lsof -i:"$port" &> /dev/null; then
      return 0
    else
      return 1
    fi
  elif command -v netstat &> /dev/null; then
    if netstat -tulpn 2>/dev/null | grep ":$port " &> /dev/null; then
      return 0
    else
      return 1
    fi
  else
    echo -e "${YELLOW}Warning: Neither lsof nor netstat available. Cannot check port usage.${NC}"
    return 1
  fi
}

# Function to list available backups
list_backups() {
  echo -e "${BLUE}Available migration backups:${NC}"
  
  # Check if backup directory exists
  if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${YELLOW}No backups found (directory does not exist)${NC}"
    return
  fi
  
  # Extract unique timestamps from migration backup filenames
  local backups=$(find "$BACKUP_DIR" -name "migration_backup_*" | grep -o "migration_backup_[0-9_]*" | sort -u)
  
  if [ -z "$backups" ]; then
    echo -e "${YELLOW}No migration backups found${NC}"
    return
  fi
  
  echo "ID                  Date Time           Files"
  echo "------------------------------------------------------"
  
  for backup in $backups; do
    # Extract timestamp
    local timestamp=${backup#migration_backup_}
    
    # Format date and time
    local formatted_date=$(echo $timestamp | sed 's/\([0-9]\{8\}\)_\([0-9]\{6\}\)/\1 \2/' | sed 's/\([0-9]\{4\}\)\([0-9]\{2\}\)\([0-9]\{2\}\) \([0-9]\{2\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)/\1-\2-\3 \4:\5:\6/')
    
    # Count number of files in this backup
    local file_count=$(find "$BACKUP_DIR" -name "${backup}*" | wc -l | tr -d ' ')
    
    echo "$timestamp  $formatted_date  $file_count"
  done
}

# Print header
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}    Damien MCP Rollback from Minimal    ${NC}"
echo -e "${BLUE}=========================================${NC}"

# List backups if requested
if [ "$LIST_BACKUPS" = true ]; then
  list_backups
  exit 0
fi

# Step 1: Check prerequisites
echo -e "\n${BLUE}Step 1: Checking prerequisites${NC}"

# Check if Claude Desktop config exists
if [ ! -f "$CLAUDE_DESKTOP_CONFIG_PATH" ]; then
  echo -e "${YELLOW}Warning: Claude Desktop config not found at: $CLAUDE_DESKTOP_CONFIG_PATH${NC}"
  echo -e "${YELLOW}This script may not work correctly without a valid Claude Desktop installation.${NC}"
  
  if ! confirm "Continue without Claude Desktop configuration?"; then
    echo -e "${RED}Rollback aborted.${NC}"
    exit 1
  fi
fi

# Check if backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
  echo -e "${RED}Error: Backup directory not found at: $BACKUP_DIR${NC}"
  exit 1
fi

# Check if jq is installed (for JSON manipulation)
if ! command -v jq &> /dev/null && [ -f "$CLAUDE_DESKTOP_CONFIG_PATH" ]; then
  echo -e "${YELLOW}Warning: jq is required for JSON manipulation but not installed.${NC}"
  echo -e "${YELLOW}Cannot restore Claude Desktop configuration without jq.${NC}"
  
  if ! confirm "Continue without restoring Claude Desktop configuration?"; then
    echo -e "${RED}Rollback aborted.${NC}"
    exit 1
  fi
fi

echo -e "${GREEN}✓ All prerequisites checked${NC}"

# Step 2: Determine which backup to use
echo -e "\n${BLUE}Step 2: Identifying backup to restore${NC}"

if [ "$USE_LATEST" = true ]; then
  # Find the most recent migration backup
  LATEST_BACKUP=$(find "$BACKUP_DIR" -name "migration_backup_*" | grep -o "migration_backup_[0-9_]*" | sort -u | tail -1)
  
  if [ -z "$LATEST_BACKUP" ]; then
    echo -e "${RED}No migration backups found${NC}"
    
    # Try regular backups instead
    LATEST_BACKUP=$(find "$BACKUP_DIR" -name "damien_mcp_backup_*" | grep -o "damien_mcp_backup_[0-9_]*" | sort -u | tail -1)
    
    if [ -z "$LATEST_BACKUP" ]; then
      echo -e "${RED}No backups found at all${NC}"
      exit 1
    else
      echo -e "${YELLOW}No migration backups found, using regular backup: ${LATEST_BACKUP#damien_mcp_backup_}${NC}"
      BACKUP_ID=${LATEST_BACKUP#damien_mcp_backup_}
      BACKUP_PREFIX="damien_mcp_backup_$BACKUP_ID"
    fi
  else
    echo -e "${CYAN}Using latest migration backup: ${LATEST_BACKUP#migration_backup_}${NC}"
    BACKUP_ID=${LATEST_BACKUP#migration_backup_}
    BACKUP_PREFIX="migration_backup_$BACKUP_ID"
  fi
elif [ -z "$BACKUP_ID" ]; then
  echo -e "${RED}No backup ID specified. Use --backup-id or --latest${NC}"
  echo -e "${YELLOW}Available backups:${NC}"
  list_backups
  exit 1
else
  # Check if specified backup exists as a migration backup
  if find "$BACKUP_DIR" -name "migration_backup_${BACKUP_ID}*" -quit; then
    BACKUP_PREFIX="migration_backup_$BACKUP_ID"
  # Check if specified backup exists as a regular backup
  elif find "$BACKUP_DIR" -name "damien_mcp_backup_${BACKUP_ID}*" -quit; then
    BACKUP_PREFIX="damien_mcp_backup_$BACKUP_ID"
  else
    echo -e "${RED}Backup with ID $BACKUP_ID not found${NC}"
    echo -e "${YELLOW}Available backups:${NC}"
    list_backups
    exit 1
  fi
fi

# Find backup files
CLAUDE_CONFIG_BACKUP=$(find "$BACKUP_DIR" -name "${BACKUP_PREFIX}_claude_desktop_config.json" -print -quit)

# Confirm rollback
if ! confirm "Are you sure you want to roll back to backup $BACKUP_ID?"; then
  echo -e "${YELLOW}Rollback cancelled${NC}"
  exit 0
fi

# Step 3: Stop minimal MCP server
echo -e "\n${BLUE}Step 3: Stopping minimal MCP server${NC}"

# Check if minimal server is running
if check_port_in_use "$MINIMAL_PORT"; then
  log_action "Stopping minimal MCP server on port $MINIMAL_PORT"
  
  if [ "$DRY_RUN" = false ]; then
    # Try to find the PID file
    if [ -f "$MINIMAL_DIR/.server.pid" ]; then
      SERVER_PID=$(cat "$MINIMAL_DIR/.server.pid")
      kill $SERVER_PID 2>/dev/null || true
      rm "$MINIMAL_DIR/.server.pid"
      echo -e "${GREEN}✓ Stopped minimal MCP server (PID: $SERVER_PID)${NC}"
    else
      # Try to find the process by name/port
      if command -v pgrep &> /dev/null; then
        PIDS=$(pgrep -f "node.*server.js")
        if [ ! -z "$PIDS" ]; then
          kill $PIDS || true
          echo -e "${GREEN}✓ Stopped minimal MCP server processes${NC}"
        fi
      else
        echo -e "${YELLOW}Cannot stop minimal MCP server (pgrep not available).${NC}"
        echo -e "${YELLOW}Please stop it manually.${NC}"
      fi
    fi
    
    # Verify server stopped
    sleep 2
    if check_port_in_use "$MINIMAL_PORT"; then
      echo -e "${YELLOW}Warning: Minimal MCP server still appears to be running.${NC}"
      if confirm "Attempt to force kill?"; then
        if command -v lsof &> /dev/null; then
          PID=$(lsof -t -i:$MINIMAL_PORT)
          if [ ! -z "$PID" ]; then
            kill -9 $PID
            echo -e "${GREEN}✓ Force killed process on port $MINIMAL_PORT${NC}"
          fi
        else
          echo -e "${YELLOW}Cannot force kill (lsof not available).${NC}"
        fi
      fi
    fi
  fi
else
  echo -e "${CYAN}Minimal MCP server is not running, nothing to stop.${NC}"
fi

# Step 4: Restore Claude Desktop configuration
echo -e "\n${BLUE}Step 4: Restoring Claude Desktop configuration${NC}"

if [ ! -z "$CLAUDE_CONFIG_BACKUP" ]; then
  log_action "Restoring Claude Desktop config from: $CLAUDE_CONFIG_BACKUP"
  
  if [ "$DRY_RUN" = false ]; then
    if [ -f "$CLAUDE_DESKTOP_CONFIG_PATH" ]; then
      # Create a backup of the current config just in case
      cp "$CLAUDE_DESKTOP_CONFIG_PATH" "${CLAUDE_DESKTOP_CONFIG_PATH}.bak"
    else
      # Ensure directory exists
      mkdir -p "$(dirname "$CLAUDE_DESKTOP_CONFIG_PATH")"
    fi
    
    # Restore from backup
    cp "$CLAUDE_CONFIG_BACKUP" "$CLAUDE_DESKTOP_CONFIG_PATH"
    echo -e "${GREEN}✓ Claude Desktop configuration restored${NC}"
    
    # Extract and display the restored MCP URL
    if command -v jq &> /dev/null; then
      RESTORED_MCP_URL=$(jq -r '.mcpConfig.mcpUrl // "not-set"' "$CLAUDE_DESKTOP_CONFIG_PATH")
      if [ "$RESTORED_MCP_URL" != "not-set" ]; then
        echo -e "${CYAN}Restored MCP URL: $RESTORED_MCP_URL${NC}"
      fi
    fi
  fi
else
  echo -e "${YELLOW}No Claude Desktop config backup found for ID: $BACKUP_ID${NC}"
  echo -e "${YELLOW}Cannot restore Claude Desktop configuration.${NC}"
fi

# Step 5: Start original services
echo -e "\n${BLUE}Step 5: Starting original services${NC}"

# Check if original services need to be started
ORIGINAL_RUNNING=$(check_port_in_use "$ORIGINAL_PORT" && echo true || echo false)
SMITHERY_RUNNING=$(check_port_in_use "$SMITHERY_PORT" && echo true || echo false)

if [ "$ORIGINAL_RUNNING" = true ]; then
  echo -e "${CYAN}Original MCP server already running on port $ORIGINAL_PORT.${NC}"
else
  if confirm "Start original MCP services?"; then
    log_action "Would start original MCP services (not implemented in this script)"
    echo -e "${YELLOW}Please start the original MCP services manually:${NC}"
    echo -e "1. Start the backend server on port $ORIGINAL_PORT"
    echo -e "2. Start the Smithery adapter on port $SMITHERY_PORT if needed"
  else
    echo -e "${YELLOW}Skipping startup of original services.${NC}"
  fi
fi

# Step 6: Validate rollback
echo -e "\n${BLUE}Step 6: Validating rollback${NC}"

log_action "Checking Claude Desktop configuration"

if [ -f "$CLAUDE_DESKTOP_CONFIG_PATH" ] && command -v jq &> /dev/null; then
  CURRENT_MCP_URL=$(jq -r '.mcpConfig.mcpUrl // "not-set"' "$CLAUDE_DESKTOP_CONFIG_PATH")
  
  if [ "$CURRENT_MCP_URL" != "http://localhost:$MINIMAL_PORT" ]; then
    echo -e "${GREEN}✓ Claude Desktop configuration is no longer pointing to minimal server${NC}"
  else
    echo -e "${RED}Warning: Claude Desktop still configured to use minimal server: $CURRENT_MCP_URL${NC}"
    echo -e "${YELLOW}Please update it manually to the original MCP URL.${NC}"
  fi
else
  echo -e "${YELLOW}Cannot validate Claude Desktop configuration.${NC}"
fi

# Step 7: Print success message and next steps
echo -e "\n${BLUE}Step 7: Rollback complete${NC}"
echo -e "${GREEN}✅ Rollback from minimal MCP server completed!${NC}"

if [ "$DRY_RUN" = true ]; then
  echo -e "${YELLOW}Note: This was a dry run. No changes were actually made.${NC}"
}

echo -e "\n${CYAN}Next steps:${NC}"
echo -e "1. Restart Claude Desktop to apply the restored configuration"
echo -e "2. Verify that Claude Desktop can connect to the original MCP server"
echo -e "3. Test basic email functionality through Claude Desktop"

echo -e "\n${GREEN}Rollback completed successfully!${NC}"
