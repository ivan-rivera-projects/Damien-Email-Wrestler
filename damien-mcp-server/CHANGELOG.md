# Changelog

All notable changes to the Damien MCP Server project will be documented in this file.

## [2.0.0] - 2025-05-26

### 🔧 MAJOR OVERHAUL: Universal Tool System Fixes

This release represents a complete refactoring of the MCP tool system, fixing all previously broken tools and implementing a robust, scalable architecture.

### ✅ Fixed
- **Universal Tool Registry**: Implemented centralized tool registration system for consistent handler management
- **Context Parameter Handling**: All registry-based tools now properly receive `(params, context)` parameters
- **Authentication Flow**: Resolved Gmail service access issues across all tool categories
- **Variable Scope Issues**: Fixed critical `mcp_response` reference before creation in router
- **Response Standardization**: Consistent success/error response patterns across all tools

### 🆕 Added
- **Complete Draft Management (6 tools)**:
  - `damien_create_draft` - Create new draft emails
  - `damien_update_draft` - Update existing drafts  
  - `damien_send_draft` - Send draft emails immediately
  - `damien_list_drafts` - List drafts with filtering
  - `damien_get_draft_details` - Get detailed draft information
  - `damien_delete_draft` - Delete draft emails

- **Complete Settings Management (6 tools)**:
  - `damien_get_vacation_settings` - Get vacation responder settings
  - `damien_update_vacation_settings` - Configure vacation auto-replies
  - `damien_get_imap_settings` - Get IMAP configuration
  - `damien_update_imap_settings` - Modify IMAP settings
  - `damien_get_pop_settings` - Get POP settings
  - `damien_update_pop_settings` - Update POP configuration

- **Enhanced Email Management (6 tools)**:
  - Improved `damien_list_emails` with better filtering
  - Enhanced `damien_get_email_details` with header options
  - Fixed `damien_trash_emails` for reliable operation
  - Working `damien_label_emails` for label management
  - Functional `damien_mark_emails` for read/unread status
  - New `damien_delete_emails_permanently` for irreversible deletion

- **Complete Rules Management (5 tools)**:
  - `damien_list_rules` - List all filtering rules
  - `damien_get_rule_details` - Get detailed rule information
  - `damien_add_rule` - Create new filtering rules
  - `damien_delete_rule` - Remove existing rules
  - `damien_apply_rules` - Apply rules with dry-run support

### 🏗️ Architecture Changes
- **New Universal Registry Pattern**: `app/services/tool_registry.py`
- **Centralized Tool Organization**: All tools organized in `app/tools/` directory
- **Standardized Handler Functions**: Consistent pattern across all tool handlers
- **Enhanced Error Handling**: Comprehensive error responses and logging
- **Tool Usage Policy**: Added tool usage guidance system

### 📁 Files Added/Modified
- `app/services/tool_registry.py` - New universal tool registry
- `app/tools/draft_tools.py` - Complete draft management implementation
- `app/tools/settings_tools.py` - Complete settings management implementation
- `app/core/tool_usage_config.py` - Tool usage policy configuration
- `app/routers/tools.py` - Major router overhaul with registry integration
- Multiple documentation files for tracking fixes and implementation status

### 🔄 Migration Notes
- All existing tool calls will continue to work without changes
- New tools are immediately available after server restart
- No breaking changes to existing API contracts
- Enhanced error messages provide better debugging information

### 🧪 Testing
- Updated all test suites for new registry architecture
- Added comprehensive test coverage for new tools
- Enhanced MCP testing utilities

### 📚 Documentation
- Updated README.md with complete tool listing
- Added comprehensive tool usage examples
- Created detailed fix documentation for maintainers
- Enhanced API documentation with new tool descriptions

---

## [1.x.x] - Previous Versions

Previous version history maintained separately. This changelog starts from the major v2.0.0 overhaul.
