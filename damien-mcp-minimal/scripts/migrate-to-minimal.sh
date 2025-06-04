#!/bin/bash
#
# Migration Script for Damien MCP Minimal Server
#
# This script performs a controlled migration from the current MCP server
# to the minimal MCP server implementation, with extensive validation
# at each step to ensure a safe transition.
#
# Usage:
#   ./migrate-to-minimal.sh [options]
#
# Options:
#   --force           Skip confirmation prompts
#   --no-backup       Skip backup steps (not recommended)
#   --dry-run         Show what would be done without making changes
#   --skip-validation Skip validation steps
#   --help            Show this help message
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
SKIP_BACKUP=false
DRY_RUN=false
SKIP_VALIDATION=false

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --force)
      FORCE=true
      ;;
    --no-backup)
      SKIP_BACKUP=true
      ;;
    --dry-run)
      DRY_RUN=true
      ;;
    --skip-validation)
      SKIP_VALIDATION=true
      ;;
    --help)
      echo "Usage: ./migrate-to-minimal.sh [options]"
      echo ""
      echo "Options:"
      echo "  --force           Skip confirmation prompts"
      echo "  --no-backup       Skip backup steps (not recommended)"
      echo "  --dry-run         Show what would be done without making changes"
      echo "  --skip-validation Skip validation steps"
      echo "  --help            Show this help message"
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
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_PREFIX="migration_backup_$TIMESTAMP"

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

# Print header
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}    Damien MCP Migration to Minimal    ${NC}"
echo -e "${BLUE}=========================================${NC}"

# Step 1: Check prerequisites
echo -e "\n${BLUE}Step 1: Checking prerequisites${NC}"

# Check if Claude Desktop config exists
if [ ! -f "$CLAUDE_DESKTOP_CONFIG_PATH" ]; then
  echo -e "${YELLOW}Warning: Claude Desktop config not found at: $CLAUDE_DESKTOP_CONFIG_PATH${NC}"
  echo -e "${YELLOW}This script may not work correctly without a valid Claude Desktop installation.${NC}"
  
  if ! confirm "Continue without Claude Desktop configuration?"; then
    echo -e "${RED}Migration aborted.${NC}"
    exit 1
  fi
fi

# Check if minimal server directory exists
if [ ! -d "$MINIMAL_DIR" ]; then
  echo -e "${RED}Error: Minimal server directory not found at: $MINIMAL_DIR${NC}"
  exit 1
fi

# Check if node is installed
if ! command -v node &> /dev/null; then
  echo -e "${RED}Error: Node.js is required but not installed.${NC}"
  exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
  echo -e "${RED}Error: npm is required but not installed.${NC}"
  exit 1
fi

# Check if jq is installed (for JSON manipulation)
if ! command -v jq &> /dev/null; then
  echo -e "${YELLOW}Warning: jq is recommended for JSON manipulation but not installed.${NC}"
  echo -e "${YELLOW}Some functions may not work correctly without jq.${NC}"
  
  if ! confirm "Continue without jq?"; then
    echo -e "${RED}Migration aborted.${NC}"
    exit 1
  fi
fi

echo -e "${GREEN}✓ All prerequisites checked${NC}"

# Step 2: Check current configuration
echo -e "\n${BLUE}Step 2: Checking current configuration${NC}"

# Check current MCP configuration in Claude Desktop
CURRENT_MCP_URL=""
if [ -f "$CLAUDE_DESKTOP_CONFIG_PATH" ] && command -v jq &> /dev/null; then
  CURRENT_MCP_URL=$(jq -r '.mcpConfig.mcpUrl // "not-set"' "$CLAUDE_DESKTOP_CONFIG_PATH")
  
  if [ "$CURRENT_MCP_URL" != "not-set" ]; then
    echo -e "${CYAN}Current MCP URL in Claude Desktop: $CURRENT_MCP_URL${NC}"
  else
    echo -e "${YELLOW}No MCP URL currently set in Claude Desktop.${NC}"
  fi
else
  echo -e "${YELLOW}Cannot determine current MCP URL (missing jq or config file).${NC}"
fi

# Check if original MCP server is running
if check_port_in_use "$ORIGINAL_PORT"; then
  echo -e "${CYAN}Original MCP server appears to be running on port $ORIGINAL_PORT.${NC}"
  ORIGINAL_RUNNING=true
else
  echo -e "${YELLOW}Original MCP server does not appear to be running on port $ORIGINAL_PORT.${NC}"
  ORIGINAL_RUNNING=false
fi

# Check if Smithery adapter is running
if check_port_in_use "$SMITHERY_PORT"; then
  echo -e "${CYAN}Smithery adapter appears to be running on port $SMITHERY_PORT.${NC}"
  SMITHERY_RUNNING=true
else
  echo -e "${YELLOW}Smithery adapter does not appear to be running on port $SMITHERY_PORT.${NC}"
  SMITHERY_RUNNING=false
fi

# Check if minimal server is already running
if check_port_in_use "$MINIMAL_PORT"; then
  echo -e "${CYAN}Minimal MCP server appears to be already running on port $MINIMAL_PORT.${NC}"
  MINIMAL_RUNNING=true
else
  echo -e "${YELLOW}Minimal MCP server is not running on port $MINIMAL_PORT.${NC}"
  MINIMAL_RUNNING=false
fi

# Step 3: Backup current configuration
if [ "$SKIP_BACKUP" = false ]; then
  echo -e "\n${BLUE}Step 3: Backing up current configuration${NC}"
  
  # Create backup directory if it doesn't exist
  if [ ! -d "$BACKUP_DIR" ]; then
    log_action "Creating backup directory: $BACKUP_DIR"
    if [ "$DRY_RUN" = false ]; then
      mkdir -p "$BACKUP_DIR"
    fi
  fi
  
  # Backup Claude Desktop config if it exists
  if [ -f "$CLAUDE_DESKTOP_CONFIG_PATH" ]; then
    CLAUDE_CONFIG_BACKUP="$BACKUP_DIR/${BACKUP_PREFIX}_claude_desktop_config.json"
    log_action "Backing up Claude Desktop config to: $CLAUDE_CONFIG_BACKUP"
    if [ "$DRY_RUN" = false ]; then
      cp "$CLAUDE_DESKTOP_CONFIG_PATH" "$CLAUDE_CONFIG_BACKUP"
    fi
  else
    echo -e "${YELLOW}Claude Desktop config not found, skipping backup.${NC}"
  fi
  
  echo -e "${GREEN}✓ Backup completed${NC}"
else
  echo -e "\n${YELLOW}Skipping backup as requested (--no-backup).${NC}"
fi

# Step 4: Stop current services (if running and if not --dry-run)
echo -e "\n${BLUE}Step 4: Managing services${NC}"

SERVICES_STOPPED=false
if [ "$DRY_RUN" = false ]; then
  # Only attempt to stop services if we're not in dry run mode
  if [ "$SMITHERY_RUNNING" = true ] || [ "$ORIGINAL_RUNNING" = true ]; then
    if confirm "Stop currently running MCP services?"; then
      if [ "$SMITHERY_RUNNING" = true ]; then
        log_action "Stopping Smithery adapter"
        # Find and kill Smithery adapter process
        if command -v pgrep &> /dev/null; then
          PIDS=$(pgrep -f ".*smithery.*adapter.*")
          if [ ! -z "$PIDS" ]; then
            kill $PIDS || true
            echo -e "${GREEN}✓ Stopped Smithery adapter${NC}"
          fi
        else
          echo -e "${YELLOW}Cannot stop Smithery adapter (pgrep not available).${NC}"
        fi
      fi
      
      if [ "$ORIGINAL_RUNNING" = true ]; then
        log_action "Stopping original MCP server"
        # Find and kill original MCP server process
        if command -v pgrep &> /dev/null; then
          PIDS=$(pgrep -f ".*damien.*mcp.*server.*")
          if [ ! -z "$PIDS" ]; then
            kill $PIDS || true
            echo -e "${GREEN}✓ Stopped original MCP server${NC}"
          fi
        else
          echo -e "${YELLOW}Cannot stop original MCP server (pgrep not available).${NC}"
        fi
      fi
      
      # Give services time to stop
      sleep 2
      SERVICES_STOPPED=true
    else
      echo -e "${YELLOW}Continuing without stopping current services.${NC}"
    fi
  else
    echo -e "${CYAN}No MCP services currently running, nothing to stop.${NC}"
  fi
else
  # In dry run mode, just log what would be done
  if [ "$SMITHERY_RUNNING" = true ] || [ "$ORIGINAL_RUNNING" = true ]; then
    log_action "Would stop currently running MCP services"
  else
    echo -e "${CYAN}No MCP services currently running, nothing to stop.${NC}"
  fi
fi

# Step 5: Start minimal server
echo -e "\n${BLUE}Step 5: Starting minimal MCP server${NC}"

if [ "$MINIMAL_RUNNING" = true ]; then
  echo -e "${CYAN}Minimal MCP server is already running.${NC}"
else
  log_action "Starting minimal MCP server on port $MINIMAL_PORT"
  
  if [ "$DRY_RUN" = false ]; then
    # Change to minimal server directory
    cd "$MINIMAL_DIR"
    
    # Start the server in the background
    nohup node server.js > logs/server.log 2>&1 &
    MINIMAL_PID=$!
    
    # Save PID to a file for later reference
    echo "$MINIMAL_PID" > .server.pid
    
    # Give the server time to start
    sleep 3
    
    # Check if the server started successfully
    if check_port_in_use "$MINIMAL_PORT"; then
      echo -e "${GREEN}✓ Minimal MCP server started successfully (PID: $MINIMAL_PID)${NC}"
    else
      echo -e "${RED}Failed to start minimal MCP server. Check logs at: $MINIMAL_DIR/logs/server.log${NC}"
      
      if [ -f .server.pid ]; then
        rm .server.pid
      fi
      
      # Print last few lines of log for debugging
      if [ -f logs/server.log ]; then
        echo -e "${YELLOW}Last few lines of server log:${NC}"
        tail -n 10 logs/server.log
      fi
      
      if ! confirm "Continue despite server startup failure?"; then
        echo -e "${RED}Migration aborted.${NC}"
        exit 1
      fi
    fi
    
    # Return to the project root
    cd "$PROJECT_ROOT"
  fi
fi

# Step 6: Update Claude Desktop configuration
echo -e "\n${BLUE}Step 6: Updating Claude Desktop configuration${NC}"

if [ -f "$CLAUDE_DESKTOP_CONFIG_PATH" ] && command -v jq &> /dev/null; then
  # Determine the URL to use (localhost with the minimal port)
  NEW_MCP_URL="http://localhost:$MINIMAL_PORT"
  
  # Check if the config already has the correct URL
  if [ "$CURRENT_MCP_URL" = "$NEW_MCP_URL" ]; then
    echo -e "${CYAN}Claude Desktop already configured to use minimal MCP server.${NC}"
  else
    log_action "Updating Claude Desktop configuration to use minimal MCP server: $NEW_MCP_URL"
    
    if [ "$DRY_RUN" = false ]; then
      # Create a temporary file
      TEMP_CONFIG=$(mktemp)
      
      # Update the config using jq
      jq ".mcpConfig.mcpUrl = \"$NEW_MCP_URL\"" "$CLAUDE_DESKTOP_CONFIG_PATH" > "$TEMP_CONFIG"
      
      # Move the temporary file to the actual config
      mv "$TEMP_CONFIG" "$CLAUDE_DESKTOP_CONFIG_PATH"
      
      echo -e "${GREEN}✓ Claude Desktop configuration updated${NC}"
    fi
  fi
else
  echo -e "${YELLOW}Cannot update Claude Desktop configuration (missing jq or config file).${NC}"
  echo -e "${YELLOW}Please manually set MCP URL to: http://localhost:$MINIMAL_PORT${NC}"
fi

# Step 7: Validate migration
if [ "$SKIP_VALIDATION" = false ]; then
  echo -e "\n${BLUE}Step 7: Validating migration${NC}"
  
  log_action "Running validation tests"
  
  if [ "$DRY_RUN" = false ]; then
    # Run the validation script
    if [ -f "$SCRIPT_DIR/validate-migration.sh" ]; then
      if bash "$SCRIPT_DIR/validate-migration.sh"; then
        echo -e "${GREEN}✓ Validation successful${NC}"
      else
        echo -e "${RED}Validation failed. Please check the validation output above.${NC}"
        
        if ! confirm "Continue despite validation failure?"; then
          echo -e "${RED}Migration aborted.${NC}"
          
          # Offer to rollback
          if confirm "Would you like to rollback the migration?"; then
            bash "$SCRIPT_DIR/rollback-from-minimal.sh" --backup-id "$TIMESTAMP"
          fi
          
          exit 1
        fi
      fi
    else
      echo -e "${YELLOW}Validation script not found at: $SCRIPT_DIR/validate-migration.sh${NC}"
      echo -e "${YELLOW}Please manually verify that the minimal MCP server is working correctly.${NC}"
    fi
  fi
else
  echo -e "\n${YELLOW}Skipping validation as requested (--skip-validation).${NC}"
fi

# Step 8: Print success message and next steps
echo -e "\n${BLUE}Step 8: Migration complete${NC}"
echo -e "${GREEN}✅ Migration to minimal MCP server completed successfully!${NC}"

if [ "$DRY_RUN" = true ]; then
  echo -e "${YELLOW}Note: This was a dry run. No changes were actually made.${NC}"
}

echo -e "\n${CYAN}Next steps:${NC}"
echo -e "1. Restart Claude Desktop to apply the new configuration"
echo -e "2. Verify that Claude Desktop can connect to the minimal MCP server"
echo -e "3. Test basic email functionality through Claude Desktop"

echo -e "\n${CYAN}To rollback this migration:${NC}"
echo -e "  bash $SCRIPT_DIR/rollback-from-minimal.sh --backup-id $TIMESTAMP"

# Print any warnings or notices
if [ "$MINIMAL_RUNNING" = false ] && [ "$DRY_RUN" = false ]; then
  echo -e "\n${YELLOW}Important: The minimal MCP server is running in the background.${NC}"
  echo -e "${YELLOW}To stop it, run: kill $(cat $MINIMAL_DIR/.server.pid)${NC}"
fi

if [ "$SERVICES_STOPPED" = true ]; then
  echo -e "\n${YELLOW}Note: The original MCP services were stopped during migration.${NC}"
  echo -e "${YELLOW}If you need to restart them, please do so manually.${NC}"
fi

echo -e "\n${GREEN}Thank you for migrating to the minimal MCP server!${NC}"
