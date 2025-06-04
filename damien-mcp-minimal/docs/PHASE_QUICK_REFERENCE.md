# Phase Expansion Quick Reference

This document provides a quick reference for expanding the Damien MCP Minimal Server through all phases.

## Phase Overview

| Phase | Focus                  | Tools | Command            |
|-------|------------------------|-------|-------------------|
| 1     | Essential Core         | 5     | Default           |
| 2     | Basic Actions          | 7     | `npm run phase:2` |
| 3     | Thread Management      | 5     | `npm run phase:3` |
| 4     | Rule Management        | 5     | `npm run phase:4` |
| 5     | AI Intelligence        | 9     | `npm run phase:5` |
| 6     | Account Settings       | 6     | `npm run phase:6` |

## Quick Commands

### Expansion Commands

```bash
# Move to next phase
npm run phase:next

# Move to specific phase
npm run phase:2  # Move to Phase 2
npm run phase:3  # Move to Phase 3
npm run phase:4  # Move to Phase 4
npm run phase:5  # Move to Phase 5
npm run phase:6  # Move to Phase 6

# Rollback to previous phase
npm run phase:rollback
```

### Advanced Options

For more control, use the script directly:

```bash
./scripts/expand-to-phase.sh --phase 3 --force
./scripts/expand-to-phase.sh --dry-run
./scripts/expand-to-phase.sh --skip-validation
```

## Testing Each Phase

```bash
# Test current phase
npm run test:phase

# Test specific phase
DAMIEN_INITIAL_PHASE=2 npm run test:phase
```

## Phase Details

### Phase 1: Essential Core
- damien_list_emails
- damien_get_email_details
- damien_create_draft
- damien_send_draft
- damien_list_drafts

### Phase 2: Basic Actions
- damien_trash_emails
- damien_label_emails
- damien_mark_emails
- damien_update_draft
- damien_delete_draft
- damien_get_draft_details
- damien_delete_emails_permanently

### Phase 3: Thread Management
- damien_list_threads
- damien_get_thread_details
- damien_modify_thread_labels
- damien_trash_thread
- damien_delete_thread_permanently

### Phase 4: Rule Management
- damien_list_rules
- damien_get_rule_details
- damien_add_rule
- damien_delete_rule
- damien_apply_rules

### Phase 5: AI Intelligence
- damien_ai_analyze_emails
- damien_ai_suggest_rules
- damien_ai_quick_test
- damien_ai_create_rule
- damien_ai_get_insights
- damien_ai_optimize_inbox
- damien_ai_analyze_emails_large_scale
- damien_ai_analyze_emails_async
- damien_job_get_status

### Phase 6: Account Settings
- damien_get_vacation_settings
- damien_update_vacation_settings
- damien_get_imap_settings
- damien_update_imap_settings
- damien_get_pop_settings
- damien_update_pop_settings

## Success Criteria Checklist

Before proceeding to the next phase, verify:

- [ ] All tests pass for the current phase
- [ ] Performance metrics meet requirements
- [ ] Claude Desktop works with all tools
- [ ] No unexpected errors during operation

## Documentation Links

For detailed information, refer to:

- [Phase Expansion Guide](./PHASE_EXPANSION_GUIDE.md) - Comprehensive expansion guide
- [Phase Troubleshooting](./PHASE_TROUBLESHOOTING.md) - Troubleshooting for each phase
- [Configuration Guide](./CONFIGURATION.md) - Server configuration options
