# Damien Email Wrestler - Issue Management Guide

## 🎯 **Overview**

This document outlines the issue tracking and management process for the Damien Email Wrestler project. We use GitHub Issues with a structured approach to maintain professional development standards and prepare for team scaling.

## 🏷️ **Issue Labels System**

### **Label Categories:**

| Label | Description | Color | Usage |
|-------|-------------|--------|--------|
| 🐛 bug | Something isn't working | `#d73a4a` | Functional defects, errors |
| 🚀 enhancement | New feature or request | `#a2eeef` | Feature improvements, additions |
| 📝 documentation | Improvements to docs | `#0075ca` | README, guides, code comments |
| 🔧 technical-debt | Code quality improvements | `#e4e669` | Refactoring, optimization |
| 🎯 user-experience | UX/UI improvements | `#c2e0c6` | Interface, workflow improvements |
| 🚨 critical | Needs immediate attention | `#b60205` | Blocking issues, security |
| 💡 feature-request | User suggested features | `#d876e3` | Community/user driven features |

### **Label Creation Commands:**
```bash
gh label create "🐛 bug" --description "Something isn't working" --color "d73a4a"
gh label create "🚀 enhancement" --description "New feature or request" --color "a2eeef"
gh label create "📝 documentation" --description "Improvements to docs" --color "0075ca"
gh label create "🔧 technical-debt" --description "Code quality improvements" --color "e4e669"
gh label create "🎯 user-experience" --description "UX/UI improvements" --color "c2e0c6"
gh label create "🚨 critical" --description "Needs immediate attention" --color "b60205"
gh label create "💡 feature-request" --description "User suggested features" --color "d876e3"
```

## 📋 **Issue Templates**

### **🐛 Bug Report Template**

```markdown
## Bug Description
[Clear, concise description of the issue]

## Steps to Reproduce
1. [First step]
2. [Second step]
3. [Third step]

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Environment
- Tool: [specific tool name]
- Query: [if applicable]
- Result: [actual output]
- Version: [if applicable]

## Logs/Screenshots
[Include relevant log snippets or screenshots]

## Priority
- [ ] Critical (blocks core functionality)
- [ ] High (affects user experience)
- [ ] Medium (minor issue)
- [ ] Low (nice to have)
```

### **🚀 Enhancement Template**

```markdown
## Feature Description
[Clear description of the proposed enhancement]

## Problem Statement
[What problem does this solve?]

## Proposed Solution
[How should this be implemented?]

## Alternative Solutions
[Any alternative approaches considered]

## Use Cases
- [Use case 1]
- [Use case 2]

## Acceptance Criteria
- [ ] [Criteria 1]
- [ ] [Criteria 2]

## Priority
- [ ] Critical (must have)
- [ ] High (should have)
- [ ] Medium (could have)
- [ ] Low (nice to have)
```

### **📝 Documentation Template**

```markdown
## Documentation Issue
[What documentation needs improvement?]

## Current State
[What exists now]

## Desired State
[What should be documented]

## Target Audience
- [ ] New developers
- [ ] End users
- [ ] Contributors
- [ ] System administrators

## Acceptance Criteria
- [ ] [Clear criteria for completion]
```

## 🔄 **Workflow Process**

### **1. Issue Creation**
```bash
# Create bug report
gh issue create --title "Bug: [Brief description]" --label "🐛 bug" --body-file bug_template.md

# Create enhancement request
gh issue create --title "Enhancement: [Brief description]" --label "🚀 enhancement" --body-file enhancement_template.md
```

### **2. Issue Lifecycle**

**States:**
- **📥 Open** - New issue, needs triage
- **🔄 In Progress** - Actively being worked on
- **👀 Review** - Implementation ready for review
- **✅ Closed** - Completed or resolved

**Labels during lifecycle:**
```bash
# Start working on issue
gh issue edit 123 --add-label "in-progress"

# Mark for review
gh issue edit 123 --remove-label "in-progress" --add-label "review"

# Close when complete
gh issue close 123 --comment "Fixed in commit abc123"
```

### **3. Linking Issues to Code**

**In commit messages:**
```bash
# Reference issue
git commit -m "fix: resolve email trash query issue (ref #123)"

# Close issue via commit
git commit -m "fix: resolve email trash query issue (closes #123)"
```

**In pull requests:**
```markdown
## Description
Brief description of changes

## Related Issues
- Fixes #123
- Addresses #456
- Related to #789
```

## 🎯 **Project Board Setup**

### **Recommended Columns:**
1. **📥 Backlog** - All new issues awaiting triage
2. **🔄 In Progress** - Currently being worked on
3. **👀 Review** - Ready for testing/review
4. **✅ Done** - Completed in current sprint

### **Automation Rules:**
- New issues → Backlog
- Add "in-progress" label → In Progress
- Add "review" label → Review
- Close issue → Done

## 📊 **Milestones Strategy**

### **Version-based Milestones:**
- **v1.0 - Core Functionality**
  - Basic email analysis and cleanup
  - Essential MCP tools working
  - Date filtering functional

- **v1.1 - Performance & Reliability**
  - Timeout issue resolution
  - Gmail API rate limiting fixes
  - Background job stability

- **v1.2 - User Experience**
  - Enhanced error messages
  - Better progress tracking
  - Improved documentation

- **v2.0 - Advanced Features**
  - Real-time processing
  - Advanced AI patterns
  - Multi-account support

## 📈 **Quality Standards**

### **Issue Quality Checklist:**
- [ ] Clear, descriptive title
- [ ] Proper labels applied
- [ ] Template used appropriately
- [ ] Reproduction steps included (for bugs)
- [ ] Priority level assigned
- [ ] Linked to relevant milestone

### **Code Quality Checklist:**
- [ ] Issue reference in commit message
- [ ] Tests updated (if applicable)
- [ ] Documentation updated
- [ ] No breaking changes (or properly documented)

## 🤝 **Team Collaboration**

### **For New Team Members:**

1. **Setup GitHub CLI:**
   ```bash
   gh auth login --web --git-protocol ssh
   ```

2. **Familiarize with labels:**
   ```bash
   gh label list
   ```

3. **Review current issues:**
   ```bash
   gh issue list --label "🐛 bug"
   gh issue list --assignee "@me"
   ```

### **Daily Workflow:**
```bash
# Check assigned issues
gh issue list --assignee "@me"

# Create new issue
gh issue create --title "..." --label "🐛 bug"

# Start working
gh issue edit 123 --add-label "in-progress"

# Commit with reference
git commit -m "fix: improve error handling (ref #123)"

# Complete issue
gh issue close 123 --comment "Resolved in commit abc123"
```

## 🔧 **Commands Reference**

### **Common GitHub CLI Commands:**
```bash
# Issues
gh issue list                           # List all issues
gh issue list --label "🐛 bug"         # List bugs only
gh issue view 123                       # View issue details
gh issue create                         # Create new issue
gh issue edit 123 --add-label "critical" # Add label
gh issue close 123                      # Close issue

# Labels
gh label list                           # List all labels
gh label create "name" --color "red"    # Create label
gh label edit "name" --color "blue"     # Edit label

# Repository
gh repo view                            # View repo info
gh repo fork                            # Fork repository
```

## 📝 **Examples**

### **Real Issues Created:**

1. **Issue #1**: Email trash operation finds emails but doesn't trash them
   - Labels: `🐛 bug`, `🎯 user-experience`
   - Priority: High
   - [View Issue](https://github.com/ivan-rivera-projects/Damien-Email-Wrestler/issues/1)

2. **Issue #2**: Background job status checks frequently timeout
   - Labels: `🐛 bug`, `🔧 technical-debt`
   - Priority: High
   - [View Issue](https://github.com/ivan-rivera-projects/Damien-Email-Wrestler/issues/2)

3. **Issue #3**: Gmail API rate limiting causes failures in concurrent operations
   - Labels: `🔧 technical-debt`, `🚀 enhancement`
   - Priority: High
   - [View Issue](https://github.com/ivan-rivera-projects/Damien-Email-Wrestler/issues/3)

## 🎯 **Success Metrics**

### **Track These KPIs:**
- Issue resolution time
- Bug-to-enhancement ratio
- Critical issue count
- Community contribution rate
- Documentation completeness

### **Monthly Review:**
- Label distribution analysis
- Milestone progress assessment
- Team velocity measurement
- User feedback incorporation

---

## 📞 **Quick Help**

**Need to create an issue?**
```bash
gh issue create
```

**Need to see all bugs?**
```bash
gh issue list --label "🐛 bug"
```

**Need to check project status?**
```bash
gh issue list --milestone "v1.1"
```

---

*This guide is a living document. Update it as our process evolves and the team grows.*