#!/bin/bash
#
# Phase Expansion Script for Damien MCP Minimal Server
#
# This script manages the safe expansion of the minimal MCP server
# through different phases, with validation and rollback capabilities.
#
# Usage:
#   ./expand-to-phase.sh [options]
#
# Options:
#   --phase NUMBER    Target phase number (2-6)
#   --rollback        Roll back to previous phase
#   --force           Skip confirmation prompts
#   --skip-validation Skip validation steps
#   --dry-run         Show what would be done without making changes
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
TARGET_PHASE=""
ROLLBACK=false
FORCE=false
SKIP_VALIDATION=false
DRY_RUN=false

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --phase)
      TARGET_PHASE="$2"
      shift
      ;;
    --rollback)
      ROLLBACK=true
      ;;
    --force)
      FORCE=true
      ;;
    --skip-validation)
      SKIP_VALIDATION=true
      ;;
    --dry-run)
      DRY_RUN=true
      ;;
    --help)
      echo "Usage: ./expand-to-phase.sh [options]"
      echo ""
      echo "Options:"
      echo "  --phase NUMBER    Target phase number (2-6)"
      echo "  --rollback        Roll back to previous phase"
      echo "  --force           Skip confirmation prompts"
      echo "  --skip-validation Skip validation steps"
      echo "  --dry-run         Show what would be done without making changes"
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
cd "$SCRIPT_DIR/.."
PROJECT_ROOT=$(pwd)
BACKUP_DIR="$PROJECT_ROOT/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_PREFIX="phase_expansion_$TIMESTAMP"

# Import .env file if it exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
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

# Function to get current phase
get_current_phase() {
  # Try to get from environment variable
  if [ ! -z "$DAMIEN_INITIAL_PHASE" ]; then
    echo "$DAMIEN_INITIAL_PHASE"
    return
  fi
  
  # Try to extract from .env file
  if [ -f .env ]; then
    PHASE_FROM_ENV=$(grep "DAMIEN_INITIAL_PHASE" .env | cut -d'=' -f2)
    if [ ! -z "$PHASE_FROM_ENV" ]; then
      echo "$PHASE_FROM_ENV"
      return
    fi
  fi
  
  # Default to phase 1
  echo "1"
}

# Function to update phase in .env file
update_phase_in_env() {
  local new_phase=$1
  
  if [ -f .env ]; then
    # Check if DAMIEN_INITIAL_PHASE exists in .env
    if grep -q "DAMIEN_INITIAL_PHASE" .env; then
      # Update existing value
      if [ "$DRY_RUN" = false ]; then
        sed -i.bak "s/DAMIEN_INITIAL_PHASE=.*/DAMIEN_INITIAL_PHASE=$new_phase/" .env
        rm .env.bak 2>/dev/null || true
      fi
    else
      # Add new entry
      if [ "$DRY_RUN" = false ]; then
        echo "DAMIEN_INITIAL_PHASE=$new_phase" >> .env
      fi
    fi
  else
    # Create new .env file
    if [ "$DRY_RUN" = false ]; then
      echo "DAMIEN_INITIAL_PHASE=$new_phase" > .env
    fi
  fi
  
  log_action "Updated phase to $new_phase in .env file"
}

# Print header
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}    Damien MCP Phase Expansion Tool    ${NC}"
echo -e "${BLUE}=========================================${NC}"

# Get current phase
CURRENT_PHASE=$(get_current_phase)
echo -e "${CYAN}Current phase: ${CURRENT_PHASE}${NC}"

# Handle rollback mode
if [ "$ROLLBACK" = true ]; then
  # Calculate previous phase
  PREV_PHASE=$((CURRENT_PHASE - 1))
  
  if [ $PREV_PHASE -lt 1 ]; then
    echo -e "${RED}Error: Cannot roll back below Phase 1${NC}"
    exit 1
  fi
  
  if ! confirm "Roll back from Phase $CURRENT_PHASE to Phase $PREV_PHASE?"; then
    echo -e "${YELLOW}Rollback cancelled.${NC}"
    exit 0
  fi
  
  # Set target phase to previous phase
  TARGET_PHASE=$PREV_PHASE
  echo -e "${CYAN}Rolling back to Phase $TARGET_PHASE${NC}"
else
  # Handle phase expansion mode
  
  # Validate target phase
  if [ -z "$TARGET_PHASE" ]; then
    # If no target specified, assume next phase
    TARGET_PHASE=$((CURRENT_PHASE + 1))
  fi
  
  # Validate target phase range
  if ! [[ "$TARGET_PHASE" =~ ^[1-6]$ ]]; then
    echo -e "${RED}Error: Invalid phase number. Must be between 1 and 6.${NC}"
    exit 1
  fi
  
  # Check if already at target phase
  if [ "$TARGET_PHASE" = "$CURRENT_PHASE" ]; then
    echo -e "${YELLOW}Already at Phase $TARGET_PHASE. No changes needed.${NC}"
    exit 0
  fi
  
  # Check if trying to go backwards (without --rollback flag)
  if [ "$TARGET_PHASE" -lt "$CURRENT_PHASE" ]; then
    echo -e "${YELLOW}Warning: Moving to a lower phase ($TARGET_PHASE) from current phase ($CURRENT_PHASE).${NC}"
    echo -e "${YELLOW}This is a rollback operation and should be done with the --rollback flag.${NC}"
    
    if ! confirm "Continue with rollback to Phase $TARGET_PHASE?"; then
      echo -e "${YELLOW}Operation cancelled.${NC}"
      exit 0
    fi
  else
    # Normal forward expansion
    echo -e "${CYAN}Expanding from Phase $CURRENT_PHASE to Phase $TARGET_PHASE${NC}"
    
    # Check if skipping phases
    if [ $((TARGET_PHASE - CURRENT_PHASE)) -gt 1 ]; then
      echo -e "${YELLOW}Warning: Skipping phases is not recommended.${NC}"
      echo -e "${YELLOW}Consider expanding one phase at a time for better stability.${NC}"
      
      if ! confirm "Continue with multi-phase expansion to Phase $TARGET_PHASE?"; then
        echo -e "${YELLOW}Operation cancelled.${NC}"
        exit 0
      fi
    fi
  fi
fi

# Step 1: Create backup
echo -e "\n${BLUE}Step 1: Creating backup${NC}"

# Create backup directory if it doesn't exist
if [ ! -d "$BACKUP_DIR" ]; then
  log_action "Creating backup directory: $BACKUP_DIR"
  if [ "$DRY_RUN" = false ]; then
    mkdir -p "$BACKUP_DIR"
  fi
fi

# Backup .env file if it exists
if [ -f .env ]; then
  ENV_BACKUP="$BACKUP_DIR/${BACKUP_PREFIX}_env"
  log_action "Backing up .env file to: $ENV_BACKUP"
  if [ "$DRY_RUN" = false ]; then
    cp .env "$ENV_BACKUP"
  fi
fi

echo -e "${GREEN}✓ Backup completed${NC}"

# Step 2: Update configuration
echo -e "\n${BLUE}Step 2: Updating configuration${NC}"

# Update phase in .env file
log_action "Setting phase to $TARGET_PHASE"
if [ "$DRY_RUN" = false ]; then
  update_phase_in_env "$TARGET_PHASE"
fi

echo -e "${GREEN}✓ Configuration updated${NC}"

# Step 3: Restart server
echo -e "\n${BLUE}Step 3: Restarting server${NC}"

# Check if server is running
SERVER_RUNNING=false
SERVER_PORT="${DAMIEN_MCP_MINIMAL_PORT:-8893}"

if check_port_in_use "$SERVER_PORT"; then
  SERVER_RUNNING=true
  log_action "Stopping current server instance"
  
  if [ "$DRY_RUN" = false ]; then
    # Try to find the PID file
    if [ -f .server.pid ]; then
      SERVER_PID=$(cat .server.pid)
      kill $SERVER_PID 2>/dev/null || true
      rm .server.pid
      echo -e "${GREEN}✓ Stopped server (PID: $SERVER_PID)${NC}"
    else
      # Try to find the process by name/port
      if command -v pgrep &> /dev/null; then
        PIDS=$(pgrep -f "node.*server.js")
        if [ ! -z "$PIDS" ]; then
          kill $PIDS || true
          echo -e "${GREEN}✓ Stopped server processes${NC}"
        fi
      else
        echo -e "${YELLOW}Cannot stop server (pgrep not available).${NC}"
        echo -e "${YELLOW}Please stop it manually and restart.${NC}"
        
        if ! confirm "Continue anyway?"; then
          echo -e "${YELLOW}Operation cancelled.${NC}"
          exit 1
        fi
      fi
    fi
    
    # Give server time to stop
    sleep 2
  fi
fi

# Start server with new phase
log_action "Starting server with Phase $TARGET_PHASE"

if [ "$DRY_RUN" = false ]; then
  # Start the server in the background
  nohup node server.js > logs/server.log 2>&1 &
  SERVER_PID=$!
  
  # Save PID to a file for later reference
  echo "$SERVER_PID" > .server.pid
  
  # Give server time to start
  sleep 3
  
  # Check if server started successfully
  if check_port_in_use "$SERVER_PORT"; then
    echo -e "${GREEN}✓ Server started successfully (PID: $SERVER_PID)${NC}"
  else
    echo -e "${RED}Failed to start server. Check logs at: logs/server.log${NC}"
    
    # Print last few lines of log
    if [ -f logs/server.log ]; then
      echo -e "${YELLOW}Last few lines of server log:${NC}"
      tail -n 10 logs/server.log
    fi
    
    echo -e "${YELLOW}Rolling back to previous phase...${NC}"
    if [ -f "$ENV_BACKUP" ]; then
      cp "$ENV_BACKUP" .env
    fi
    
    echo -e "${RED}Phase expansion failed. Configuration restored.${NC}"
    exit 1
  fi
fi

# Step 4: Validate new phase
if [ "$SKIP_VALIDATION" = false ]; then
  echo -e "\n${BLUE}Step 4: Validating Phase $TARGET_PHASE${NC}"
  
  log_action "Running phase validation tests"
  
  if [ "$DRY_RUN" = false ]; then
    # Set specific validation for each phase
    case $TARGET_PHASE in
      1)
        VALIDATION_CMD="npm run test:phase"
        ;;
      2)
        VALIDATION_CMD="DAMIEN_INITIAL_PHASE=2 npm run test:phase"
        ;;
      3)
        VALIDATION_CMD="DAMIEN_INITIAL_PHASE=3 npm run test:phase"
        ;;
      4)
        VALIDATION_CMD="DAMIEN_INITIAL_PHASE=4 npm run test:phase"
        ;;
      5)
        VALIDATION_CMD="DAMIEN_INITIAL_PHASE=5 npm run test:phase"
        ;;
      6)
        VALIDATION_CMD="DAMIEN_INITIAL_PHASE=6 npm run test:phase"
        ;;
      *)
        VALIDATION_CMD="npm run test:phase"
        ;;
    esac
    
    # Run validation
    if eval "$VALIDATION_CMD"; then
      echo -e "${GREEN}✓ Phase $TARGET_PHASE validation successful${NC}"
    else
      echo -e "${RED}Phase $TARGET_PHASE validation failed${NC}"
      
      if confirm "Would you like to roll back to Phase $CURRENT_PHASE?"; then
        echo -e "${YELLOW}Rolling back to Phase $CURRENT_PHASE...${NC}"
        
        # Restore .env
        if [ -f "$ENV_BACKUP" ]; then
          cp "$ENV_BACKUP" .env
        else
          update_phase_in_env "$CURRENT_PHASE"
        fi
        
        # Restart server
        if [ -f .server.pid ]; then
          SERVER_PID=$(cat .server.pid)
          kill $SERVER_PID 2>/dev/null || true
          rm .server.pid
        fi
        
        # Start server with previous phase
        nohup node server.js > logs/server.log 2>&1 &
        NEW_SERVER_PID=$!
        echo "$NEW_SERVER_PID" > .server.pid
        
        echo -e "${YELLOW}Rolled back to Phase $CURRENT_PHASE${NC}"
        echo -e "${RED}Phase expansion failed. Please check logs and troubleshooting guide.${NC}"
        exit 1
      else
        echo -e "${YELLOW}Continuing despite validation failure.${NC}"
      fi
    fi
  fi
else
  echo -e "\n${YELLOW}Skipping validation as requested (--skip-validation).${NC}"
fi

# Step 5: Run performance tests
echo -e "\n${BLUE}Step 5: Running performance tests${NC}"

log_action "Checking performance metrics for Phase $TARGET_PHASE"

if [ "$DRY_RUN" = false ] && [ "$SKIP_VALIDATION" = false ]; then
  # Create a temporary performance test file
  PERF_TEST_FILE=$(mktemp)
  
  cat > "$PERF_TEST_FILE" << 'EOF'
import MinimalDamienMCP from './server.js';

async function runPerformanceTest() {
  try {
    console.log('Starting performance test...');
    
    const server = new MinimalDamienMCP();
    
    // Measure tool list performance
    const startTime = Date.now();
    const iterations = 10;
    
    console.log(`Running ${iterations} consecutive tool list requests...`);
    
    for (let i = 0; i < iterations; i++) {
      await server.getCachedTools();
    }
    
    const elapsedMs = Date.now() - startTime;
    const avgMs = elapsedMs / iterations;
    
    console.log(`Completed ${iterations} tool list requests in ${elapsedMs}ms`);
    console.log(`Average response time: ${avgMs.toFixed(2)}ms per request`);
    
    // Get performance metrics
    const metrics = server.getRequestStats();
    console.log('Performance metrics:', JSON.stringify(metrics, null, 2));
    
    // Check if performance is acceptable
    if (avgMs < 200) {
      console.log('Performance is within acceptable limits');
      process.exit(0);
    } else {
      console.error('Performance is below acceptable limits');
      process.exit(1);
    }
  } catch (error) {
    console.error('Performance test failed:', error);
    process.exit(1);
  }
}

runPerformanceTest();
EOF
  
  # Run the performance test
  if node "$PERF_TEST_FILE"; then
    echo -e "${GREEN}✓ Performance tests passed${NC}"
  else
    echo -e "${YELLOW}⚠️ Performance tests failed or showed degraded performance${NC}"
    echo -e "${YELLOW}Review performance metrics and consider optimization before heavy usage${NC}"
  fi
  
  # Clean up temp file
  rm "$PERF_TEST_FILE"
fi

# Step 6: Print summary
echo -e "\n${BLUE}Step 6: Phase expansion complete${NC}"
echo -e "${GREEN}✅ Successfully expanded to Phase $TARGET_PHASE!${NC}"

if [ "$DRY_RUN" = true ]; then
  echo -e "${YELLOW}Note: This was a dry run. No changes were actually made.${NC}"
}

# Print phase information
case $TARGET_PHASE in
  1)
    echo -e "\n${CYAN}Phase 1: Essential Core${NC}"
    echo -e "Available tools: damien_list_emails, damien_get_email_details, damien_create_draft, damien_send_draft, damien_list_drafts"
    ;;
  2)
    echo -e "\n${CYAN}Phase 2: Basic Actions${NC}"
    echo -e "New tools: damien_trash_emails, damien_label_emails, damien_mark_emails, damien_update_draft, damien_delete_draft, damien_get_draft_details, damien_delete_emails_permanently"
    ;;
  3)
    echo -e "\n${CYAN}Phase 3: Thread Management${NC}"
    echo -e "New tools: damien_list_threads, damien_get_thread_details, damien_modify_thread_labels, damien_trash_thread, damien_delete_thread_permanently"
    ;;
  4)
    echo -e "\n${CYAN}Phase 4: Rule Management${NC}"
    echo -e "New tools: damien_list_rules, damien_get_rule_details, damien_add_rule, damien_delete_rule, damien_apply_rules"
    ;;
  5)
    echo -e "\n${CYAN}Phase 5: AI Intelligence${NC}"
    echo -e "New tools: damien_ai_analyze_emails, damien_ai_suggest_rules, damien_ai_quick_test, damien_ai_create_rule, damien_ai_get_insights, damien_ai_optimize_inbox, damien_ai_analyze_emails_large_scale, damien_ai_analyze_emails_async, damien_job_get_status"
    ;;
  6)
    echo -e "\n${CYAN}Phase 6: Account Settings${NC}"
    echo -e "New tools: damien_get_vacation_settings, damien_update_vacation_settings, damien_get_imap_settings, damien_update_imap_settings, damien_get_pop_settings, damien_update_pop_settings"
    ;;
esac

echo -e "\n${CYAN}Next steps:${NC}"
echo -e "1. Verify Claude Desktop can use the new tools"
echo -e "2. Monitor performance during regular usage"
echo -e "3. Check logs for any warning signs"

echo -e "\n${CYAN}To roll back if needed:${NC}"
echo -e "  ./scripts/expand-to-phase.sh --rollback"

echo -e "\n${GREEN}Phase expansion completed successfully!${NC}"
