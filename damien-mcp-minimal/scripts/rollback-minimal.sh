#!/bin/bash
#
# Rollback Script for Damien MCP Minimal Server
#
# This script handles rollback of the minimal MCP server deployment,
# restoring configurations from a backup.
#
# Usage:
#   ./rollback-minimal.sh [options]
#
# Options:
#   --backup-id ID  Specify the backup ID (timestamp) to use
#   --list          List available backups
#   --latest        Use the most recent backup (default)
#   --dry-run       Show what would be done without making changes
#   --force         Skip confirmation prompts
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
    --dry-run)
      DRY_RUN=true
      ;;
    --force)
      FORCE=true
      ;;
    --help)
      echo "Usage: ./rollback-minimal.sh [options]"
      echo ""
      echo "Options:"
      echo "  --backup-id ID  Specify the backup ID (timestamp) to use"
      echo "  --list          List available backups"
      echo "  --latest        Use the most recent backup (default)"
      echo "  --dry-run       Show what would be done without making changes"
      echo "  --force         Skip confirmation prompts"
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

# Function to list available backups
list_backups() {
  echo -e "${BLUE}Available backups:${NC}"
  
  # Check if backup directory exists
  if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${YELLOW}No backups found (directory does not exist)${NC}"
    return
  fi
  
  # Extract unique timestamps from backup filenames
  local backups=$(find "$BACKUP_DIR" -name "damien_mcp_backup_*" | grep -o "damien_mcp_backup_[0-9_]*" | sort -u)
  
  if [ -z "$backups" ]; then
    echo -e "${YELLOW}No backups found${NC}"
    return
  fi
  
  echo "ID                  Date Time           Files"
  echo "------------------------------------------------------"
  
  for backup in $backups; do
    # Extract timestamp
    local timestamp=${backup#damien_mcp_backup_}
    
    # Format date and time
    local formatted_date=$(echo $timestamp | sed 's/\([0-9]\{8\}\)_\([0-9]\{6\}\)/\1 \2/' | sed 's/\([0-9]\{4\}\)\([0-9]\{2\}\)\([0-9]\{2\}\) \([0-9]\{2\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)/\1-\2-\3 \4:\5:\6/')
    
    # Count number of files in this backup
    local file_count=$(find "$BACKUP_DIR" -name "${backup}*" | wc -l | tr -d ' ')
    
    echo "$timestamp  $formatted_date  $file_count"
  done
}

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  Damien MCP Minimal Server Rollback  ${NC}"
echo -e "${BLUE}=========================================${NC}"

# List backups if requested
if [ "$LIST_BACKUPS" = true ]; then
  list_backups
  exit 0
fi

# Check if backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
  echo -e "${RED}Backup directory not found: $BACKUP_DIR${NC}"
  exit 1
fi

# Determine which backup to use
if [ "$USE_LATEST" = true ]; then
  # Find the most recent backup
  LATEST_BACKUP=$(find "$BACKUP_DIR" -name "damien_mcp_backup_*" | grep -o "damien_mcp_backup_[0-9_]*" | sort -u | tail -1)
  
  if [ -z "$LATEST_BACKUP" ]; then
    echo -e "${RED}No backups found${NC}"
    exit 1
  fi
  
  BACKUP_ID=${LATEST_BACKUP#damien_mcp_backup_}
  echo -e "${BLUE}Using latest backup: $BACKUP_ID${NC}"
elif [ -z "$BACKUP_ID" ]; then
  echo -e "${RED}No backup ID specified. Use --backup-id or --latest${NC}"
  echo -e "${YELLOW}Available backups:${NC}"
  list_backups
  exit 1
fi

# Check if specified backup exists
if ! find "$BACKUP_DIR" -name "damien_mcp_backup_${BACKUP_ID}*" -quit; then
  echo -e "${RED}Backup with ID $BACKUP_ID not found${NC}"
  echo -e "${YELLOW}Available backups:${NC}"
  list_backups
  exit 1
fi

BACKUP_PREFIX="damien_mcp_backup_$BACKUP_ID"

# Find backup files
CLAUDE_CONFIG_BACKUP=$(find "$BACKUP_DIR" -name "${BACKUP_PREFIX}_claude_desktop_config.json" -print -quit)
ENV_BACKUP=$(find "$BACKUP_DIR" -name "${BACKUP_PREFIX}_env" -print -quit)

# Confirm rollback
if ! confirm "Are you sure you want to roll back to backup $BACKUP_ID?"; then
  echo -e "${YELLOW}Rollback cancelled${NC}"
  exit 0
fi

echo -e "\n${BLUE}Step 1: Stopping running services${NC}"
# Find and kill any running minimal MCP server processes
if command -v pgrep &> /dev/null; then
  log_action "Checking for running minimal MCP server processes"
  if [ "$DRY_RUN" = false ]; then
    PIDS=$(pgrep -f "node.*server.js")
    if [ ! -z "$PIDS" ]; then
      echo -e "${YELLOW}Found running MCP server processes. Stopping...${NC}"
      kill $PIDS || true
    else
      echo -e "${GREEN}No running MCP server processes found${NC}"
    fi
  fi
fi

echo -e "\n${BLUE}Step 2: Restoring configurations${NC}"

# Restore Claude Desktop config if available
if [ ! -z "$CLAUDE_CONFIG_BACKUP" ]; then
  log_action "Restoring Claude Desktop config from: $CLAUDE_CONFIG_BACKUP"
  if [ "$DRY_RUN" = false ]; then
    # Make sure the directory exists
    mkdir -p "$(dirname "$CLAUDE_DESKTOP_CONFIG_PATH")"
    cp "$CLAUDE_CONFIG_BACKUP" "$CLAUDE_DESKTOP_CONFIG_PATH"
  fi
else
  echo -e "${YELLOW}Claude Desktop config backup not found${NC}"
fi

# Restore .env file if available
if [ ! -z "$ENV_BACKUP" ]; then
  log_action "Restoring .env file from: $ENV_BACKUP"
  if [ "$DRY_RUN" = false ]; then
    cp "$ENV_BACKUP" "$MINIMAL_DIR/.env"
  fi
else
  echo -e "${YELLOW}.env file backup not found${NC}"
fi

echo -e "\n${BLUE}Step 3: Rollback complete${NC}"
echo -e "${GREEN}The minimal MCP server has been rolled back to backup $BACKUP_ID.${NC}"
echo -e "${GREEN}To start the server with the restored configuration, run:${NC}"
echo -e "  cd $MINIMAL_DIR"
echo -e "  npm start"

echo -e "\n${GREEN}Rollback completed successfully!${NC}"
if [ "$DRY_RUN" = true ]; then
  echo -e "${YELLOW}This was a dry run. No changes were made.${NC}"
fi