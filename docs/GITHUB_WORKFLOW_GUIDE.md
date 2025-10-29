# GitHub Workflow Guide - Damien Email Wrestler

Complete guide to working with GitHub issues, pull requests, and automation in this project.

## Table of Contents

- [Quick Start](#quick-start)
- [Phase 2: Ongoing Workflow](#phase-2-ongoing-workflow)
- [Phase 3: Advanced Integration](#phase-3-advanced-integration)
- [Tools and Scripts](#tools-and-scripts)
- [Automation Features](#automation-features)
- [Best Practices](#best-practices)

## Quick Start

### Prerequisites

```bash
# Verify GitHub CLI is installed and authenticated
gh auth status

# Verify git is configured
git config user.name
git config user.email
```

### Your First Issue

```bash
# Create an issue using our interactive script
node scripts/create-issue-quick.js

# Or use GitHub web interface with templates
gh issue create --web
```

### Your First PR

```bash
# 1. Create feature branch
git checkout -b feature/issue-25-description

# 2. Make changes
# ... edit files ...

# 3. Commit with issue reference
git add .
git commit -m "Feature: Add new capability (#25)"

# 4. Push and create PR
git push origin feature/issue-25-description
gh pr create --web  # Will use PR template
```

## Phase 2: Ongoing Workflow

This is your day-to-day development workflow.

### Working with Issues

#### Creating Issues

**Method 1: Interactive CLI** (Fastest)
```bash
node scripts/create-issue-quick.js
```

**Method 2: GitHub Templates** (Most Detailed)
```bash
gh issue create --web
# Select template: Bug Report or Feature Request
```

**Method 3: Direct CLI** (Quickest for simple issues)
```bash
gh issue create \
  --title "Fix: Email parsing issue" \
  --body "Description of the issue" \
  --label "bug,high" \
  --assignee "@me"
```

#### Managing Issues

```bash
# List open issues
gh issue list

# Search issues
gh issue list --search "keyword"

# View specific issue
gh issue view 25

# Close issue
gh issue close 25 --comment "Fixed in PR #30"

# Reopen issue
gh issue reopen 25
```

#### Issue Linking

Always link issues in commits and PRs:

```bash
# In commit messages
git commit -m "Fix: Resolve email body issue (#20)"

# In PR descriptions (auto-closes when merged)
Fixes #20
Closes #25
Relates to #30
```

### Creating Pull Requests

#### PR Workflow

```bash
# 1. Create and checkout feature branch
git checkout -b feature/issue-25-description

# 2. Make changes
# ... code changes ...

# 3. Test locally
./scripts/stop-all.sh
./scripts/start-all.sh
./scripts/status.sh

# 4. Commit changes
git add .
git commit -m "Feature: Add email organization tool (#25)

- Implement natural language pattern matching
- Add dry-run preview mode
- Update documentation

Fixes #25"

# 5. Push to GitHub
git push origin feature/issue-25-description

# 6. Create PR (template auto-populates)
gh pr create --web

# Or with CLI
gh pr create \
  --title "Feature: Add email organization tool (#25)" \
  --body "Fixes #25" \
  --label "enhancement"
```

#### PR Best Practices

1. **Link Issues**: Use `Fixes #123` to auto-close issues
2. **Small PRs**: One feature/fix per PR
3. **Fill Template**: Complete all sections of PR template
4. **Self-Review**: Review your own changes first
5. **Tests**: Verify all services restart cleanly
6. **Documentation**: Update docs for new features

### Automated PR Validation

When you create a PR, automated validation runs:

✅ **Automatic Checks:**
- Issue linkage verification
- Title format check
- Description completeness
- Testing checklist validation
- Breaking change detection
- Documentation update verification

⚠️ **If Validation Fails:**
- PR comment shows specific issues
- Fix issues and push updates
- Validation re-runs automatically

### Code Review Process

```bash
# Request review
gh pr review --request @reviewer-username

# View PR status
gh pr status

# View PR checks
gh pr checks

# View PR diff
gh pr diff

# Merge PR (after approval)
gh pr merge --squash  # Recommended
# or
gh pr merge --merge   # Keep all commits
```

## Phase 3: Advanced Integration

### Automated Features

#### 1. Auto-labeling (✅ Enabled)

**Triggers**: When issues are created or edited

**What it does**:
- Scans issue title and body for keywords
- Automatically adds relevant labels
- Posts comment explaining label choices

**Keywords Detected**:
- **Severity**: `critical`, `urgent`, `high priority`, `minor`
- **Type**: `bug`, `feature`, `documentation`, `enhancement`
- **Component**: `mcp`, `ai analysis`, `lambda`, `aws`
- **Status**: `investigate`, `data integrity`, `needs investigation`

**Example**:
```
Issue Title: "Tool fails with timeout error"
→ Auto-labels: bug, type:tool-failure, needs-investigation
```

#### 2. PR Validation (✅ Enabled)

**Triggers**: When PRs are created or updated

**What it does**:
- Validates issue links (`Fixes #123` format)
- Checks title follows convention
- Ensures description is filled out
- Verifies testing checklist completion
- Detects breaking changes
- Checks for documentation updates

**Validation Report**:
```markdown
## 🔍 PR Validation Report

✅ Issue Links Found: Fixes #25
✅ Title Format: Follows convention
⚠️ Testing: Please check completed testing items
✅ All Critical Checks Passed: PR looks good!
```

#### 3. Changelog Generation (✅ Enabled)

**Triggers**: Manual workflow or on release creation

**What it does**:
- Scans commits between tags
- Extracts issue/PR numbers
- Categorizes changes (features, fixes, docs, etc.)
- Generates formatted changelog
- Updates CHANGELOG.md
- Creates release notes

**Usage**:

```bash
# Generate changelog manually
gh workflow run generate-changelog.yml \
  -f from_tag=v1.0.0 \
  -f to_tag=v1.1.0

# Or during release creation (automatic)
gh release create v1.1.0 --generate-notes
```

**Generated Format**:
```markdown
# Changelog

## [v1.1.0] - 2025-01-15

**Full Changelog**: https://github.com/.../compare/v1.0.0...v1.1.0

## 🚨 Breaking Changes
- Breaking change description (#30)

## ✨ New Features
- Feature description (#25)
- Another feature (#26)

## 🐛 Bug Fixes
- Fix description (#20)
- Another fix (#21)

## 📚 Documentation
- Doc update (#23)
```

### Release Process

```bash
# 1. Ensure all PRs for release are merged
gh pr list --state merged

# 2. Generate changelog
gh workflow run generate-changelog.yml \
  -f from_tag=v1.0.0 \
  -f to_tag=HEAD

# 3. Update version numbers
# Edit package.json, pyproject.toml, etc.

# 4. Commit version bump
git add .
git commit -m "chore: Bump version to v1.1.0"
git push

# 5. Create tag
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin v1.1.0

# 6. Create GitHub release
gh release create v1.1.0 \
  --title "v1.1.0 - Feature Release" \
  --generate-notes

# 7. Verify release
gh release view v1.1.0
```

## Tools and Scripts

### Available Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `create-github-issues.js` | Bulk issue creation | `node scripts/create-github-issues.js` |
| `create-labels.js` | Setup GitHub labels | `node scripts/create-labels.js` |
| `create-issue-quick.js` | Interactive issue creator | `node scripts/create-issue-quick.js` |

### GitHub CLI Commands

```bash
# Issues
gh issue list
gh issue create --web
gh issue view 25
gh issue close 25
gh issue comment 25 --body "Comment text"

# Pull Requests
gh pr list
gh pr create --web
gh pr view 30
gh pr merge 30 --squash
gh pr review 30 --approve
gh pr checks 30

# Repository
gh repo view
gh repo view --web

# Workflows
gh workflow list
gh workflow run workflow-name.yml
gh run list
gh run view 12345

# Releases
gh release list
gh release create v1.0.0
gh release view v1.0.0
```

### Useful Aliases

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
# Issue management
alias ghil='gh issue list'
alias ghic='node scripts/create-issue-quick.js'
alias ghiv='gh issue view'

# PR management
alias ghpl='gh pr list'
alias ghpc='gh pr create --web'
alias ghpv='gh pr view'
alias ghpm='gh pr merge --squash'

# Quick status
alias ghstatus='gh pr status && echo "\n" && gh issue list --assignee @me'

# Damien workflow
alias damien-issue='node scripts/create-issue-quick.js'
alias damien-status='./scripts/status.sh && ghstatus'
```

## Automation Features

### What's Automated

✅ **Issue Auto-labeling**: Keywords → Labels
✅ **PR Validation**: Checks requirements before merge
✅ **Changelog Generation**: Auto-generates from issues/PRs
✅ **Issue Templates**: Structured bug/feature forms
✅ **PR Template**: Auto-populated PR description

### What's Manual (But Easy)

- Creating issues (use `create-issue-quick.js`)
- Creating PRs (use templates)
- Code review and approval
- Merging PRs
- Creating releases

## Best Practices

### Issue Management

1. **Search First**: Check if issue exists
2. **Use Templates**: Provides structure and context
3. **Be Specific**: Include reproduction steps, environment details
4. **Link Related Issues**: Use `#issue-number` to reference
5. **Add Labels**: Use appropriate severity and type labels
6. **Assign Issues**: Assign to yourself when working on it

### Pull Request Management

1. **One Issue Per PR**: Keep PRs focused
2. **Link Issues**: Use `Fixes #123` to auto-close
3. **Fill Template**: Complete all sections
4. **Test Thoroughly**: Verify all services work
5. **Update Docs**: Keep documentation current
6. **Respond to Feedback**: Address review comments promptly
7. **Squash Merge**: Keep history clean (recommended)

### Commit Messages

Follow the convention:

```
Type: Short description (#issue-number)

- Detailed change 1
- Detailed change 2

Fixes #issue-number
```

**Types**: `Fix:`, `Feature:`, `Docs:`, `Refactor:`, `Test:`, `Chore:`, `Perf:`

### Branch Naming

```
feature/issue-25-description
bugfix/issue-20-description
docs/issue-23-description
refactor/issue-30-description
```

## Troubleshooting

### Common Issues

**Issue**: PR validation fails with "Missing Issue Link"
```bash
# Solution: Add to PR description
Fixes #25
```

**Issue**: Can't push to main branch
```bash
# Solution: Create feature branch and PR
git checkout -b feature/my-fix
git push origin feature/my-fix
gh pr create --web
```

**Issue**: Auto-labeling not working
```bash
# Check workflow status
gh run list --workflow=auto-label-issues.yml

# View specific run
gh run view <run-id>
```

**Issue**: Changelog not generating
```bash
# Verify you have commits with issue references
git log --grep="#[0-9]"

# Run workflow manually
gh workflow run generate-changelog.yml \
  -f from_tag=v1.0.0 \
  -f to_tag=HEAD
```

## Next Steps

1. ✅ **Set Up Branch Protection**: See `docs/BRANCH_PROTECTION_SETUP.md`
2. ✅ **Create First Issue**: Try `node scripts/create-issue-quick.js`
3. ✅ **Make First PR**: Follow the workflow above
4. ✅ **Test Automation**: Verify auto-labeling and validation work
5. ✅ **Create First Release**: When ready for v1.0.0

## Resources

- **Contributing Guide**: `.github/CONTRIBUTING.md`
- **Branch Protection**: `docs/BRANCH_PROTECTION_SETUP.md`
- **Issue Templates**: `.github/ISSUE_TEMPLATE/`
- **PR Template**: `.github/pull_request_template.md`
- **Workflows**: `.github/workflows/`

## Getting Help

- **Issues**: Create an issue for questions
- **Discussions**: Use GitHub Discussions
- **Documentation**: Check `docs/` directory

---

**Happy coding!** 🚀 This workflow ensures quality, consistency, and collaboration across the project.
