# Contributing to Damien Email Wrestler

Thank you for your interest in contributing to Damien Email Wrestler! This guide will help you understand our development workflow and best practices.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Working with Issues](#working-with-issues)
- [Creating Pull Requests](#creating-pull-requests)
- [Testing Guidelines](#testing-guidelines)
- [Code Style](#code-style)
- [Commit Messages](#commit-messages)
- [Release Process](#release-process)

## Getting Started

### Prerequisites

- **Git**: Version control
- **GitHub CLI (gh)**: For issue/PR management
- **Python 3.9+**: For CLI and backend services
- **Node.js 18+**: For MCP servers
- **Gmail API Credentials**: For email access

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/ivan-rivera-projects/Damien-Email-Wrestler.git
cd damien-email-wrestler

# Install dependencies
cd damien-cli && poetry install && cd ..
cd damien-mcp-server && npm install && cd ..
cd damien-mcp-minimal && npm install && cd ..

# Start all services
./scripts/start-all.sh

# Verify setup
./scripts/status.sh
```

## Development Workflow

### 1. Find or Create an Issue

**Before starting any work**, ensure there's a GitHub issue for it:

```bash
# Search existing issues
gh issue list --search "keyword"

# Create a new issue (use templates)
gh issue create --web

# Or use our quick CLI
node scripts/create-issue-quick.js
```

### 2. Create a Feature Branch

**Always branch from `main`:**

```bash
# Update main branch
git checkout main
git pull origin main

# Create feature branch (include issue number)
git checkout -b feature/issue-17-fix-script-naming
# or
git checkout -b bugfix/issue-20-email-body-retrieval
```

**Branch Naming Convention:**
- `feature/issue-#-description` - New features
- `bugfix/issue-#-description` - Bug fixes
- `docs/issue-#-description` - Documentation updates
- `refactor/issue-#-description` - Code refactoring
- `test/issue-#-description` - Testing improvements

### 3. Make Your Changes

```bash
# Stop services before making changes
./scripts/stop-all.sh

# Make your changes
# ... edit files ...

# Restart services to test
./scripts/start-all.sh

# Verify your changes work
./scripts/status.sh
```

### 4. Commit Your Changes

Follow our commit message convention:

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "Fix: Correct script naming in damien-work-start.sh (#17)

- Update comments to reference 'Claude Desktop' instead of 'Claude Code'
- Add clarification about MCP server support
- Update user-facing messages"
```

See [Commit Messages](#commit-messages) section for detailed guidelines.

### 5. Push and Create PR

```bash
# Push your branch
git push origin feature/issue-17-fix-script-naming

# Create pull request (will use PR template)
gh pr create --web
# or
gh pr create --title "Fix: Correct script naming (#17)" --body "Fixes #17"
```

## Working with Issues

### Issue Creation Guidelines

1. **Search First**: Check if similar issue exists
2. **Use Templates**: Use bug report or feature request templates
3. **Be Specific**: Include reproduction steps, environment details, error messages
4. **Add Labels**: Use appropriate labels (severity, type, component)
5. **Link Related Issues**: Reference related issues using `#issue-number`

### Issue Labels

**Severity Labels:**
- `critical` - Blocks workflow, needs immediate attention
- `high` - Significant impact, high priority
- `medium` - Noticeable impact, normal priority
- `low` - Minor impact, low priority

**Type Labels:**
- `bug` - Something isn't working
- `enhancement` - New feature or improvement
- `documentation` - Documentation updates
- `type:tool-failure` - Tool execution issues
- `type:data-retrieval` - Data fetching problems
- `needs-investigation` - Requires investigation

**Component Labels:**
- Will be created as needed based on architecture

### Quick Issue Creation

For quick issue creation from CLI:

```bash
# Interactive mode
node scripts/create-issue-quick.js

# Or use gh directly
gh issue create \
  --title "Your issue title" \
  --body "Issue description" \
  --label "bug,high" \
  --assignee "@me"
```

## Creating Pull Requests

### PR Requirements

**Every PR must:**

1. ✅ **Link to an Issue**: Use `Fixes #123` or `Closes #123` in description
2. ✅ **Pass All Tests**: Ensure all services restart cleanly
3. ✅ **Update Documentation**: Update relevant docs (README, CLAUDE.md, etc.)
4. ✅ **Follow Code Style**: Match existing code style
5. ✅ **Include Testing Notes**: Describe how you tested the changes

### PR Template

When you create a PR, GitHub will auto-populate with our template. Fill out all sections:

- **Description**: What does this PR do?
- **Related Issues**: Link issues using keywords
- **Type of Change**: Bug fix, feature, docs, etc.
- **Changes Made**: Bullet points of changes
- **Testing Performed**: How you verified it works
- **Pre-Deployment Checklist**: Complete all items
- **Deployment Notes**: Any special instructions

### PR Best Practices

- **Small, Focused PRs**: One issue per PR when possible
- **Clear Titles**: Use format: `Fix: Description (#issue-number)`
- **Detailed Description**: Explain the "why" not just the "what"
- **Link Issues**: Use `Fixes #123` to auto-close issues
- **Self-Review**: Review your own code first
- **Address Feedback**: Respond to review comments promptly

## Testing Guidelines

### Manual Testing

**Before creating a PR:**

```bash
# Stop all services
./scripts/stop-all.sh

# Start all services
./scripts/start-all.sh

# Check status
./scripts/status.sh

# Test affected functionality
# For MCP tools:
# Test via Claude Code or Claude Desktop

# For CLI tools:
cd damien-cli
poetry run python -m damien_cli.cli_entry [command]
```

### Automated Testing

```bash
# Run Python tests (when available)
cd damien-cli
poetry run pytest

# Run Node tests (when available)
cd damien-mcp-server
npm test
```

### Testing Checklist

- [ ] All services start without errors
- [ ] Affected tools/commands work as expected
- [ ] No console errors or warnings
- [ ] Documentation matches new behavior
- [ ] Edge cases handled properly

## Code Style

### Python (damien-cli)

- **Style Guide**: Follow PEP 8
- **Formatting**: Use `black` for auto-formatting
- **Linting**: Use `ruff` or `pylint`
- **Type Hints**: Include type hints where appropriate
- **Docstrings**: Use Google-style docstrings

```python
def get_email_details(email_id: str, include_body: bool = False) -> dict:
    """
    Retrieve detailed information for a specific email.

    Args:
        email_id: The Gmail message ID
        include_body: Whether to include email body content

    Returns:
        dict: Email details including headers, labels, and optionally body

    Raises:
        EmailNotFoundError: If email_id doesn't exist
    """
    pass
```

### JavaScript/Node.js (MCP Servers)

- **Style Guide**: Standard JS or ESLint config
- **Formatting**: Use Prettier
- **Modern JS**: Use ES6+ features (async/await, arrow functions)
- **Comments**: Explain complex logic

```javascript
/**
 * Handle MCP tool call request
 * @param {string} toolName - Name of the tool to execute
 * @param {object} params - Tool parameters
 * @returns {Promise<object>} Tool execution result
 */
async function handleToolCall(toolName, params) {
  // Implementation
}
```

### General Guidelines

- **DRY**: Don't Repeat Yourself
- **KISS**: Keep It Simple, Stupid
- **YAGNI**: You Aren't Gonna Need It
- **Error Handling**: Always handle errors gracefully
- **Logging**: Use appropriate log levels (DEBUG, INFO, ERROR)
- **Comments**: Explain "why" not "what"

## Commit Messages

### Commit Message Format

```
Type: Short description (#issue-number)

- Detailed bullet point 1
- Detailed bullet point 2
- Detailed bullet point 3

Fixes #issue-number
```

### Commit Types

- `Fix:` - Bug fixes
- `Feature:` - New features
- `Docs:` - Documentation updates
- `Refactor:` - Code refactoring
- `Test:` - Testing improvements
- `Chore:` - Maintenance tasks
- `Perf:` - Performance improvements

### Examples

```bash
# Bug fix
git commit -m "Fix: Resolve email body retrieval issue (#20)

- Implement proper MIME multipart parsing
- Add support for HTML and text body extraction
- Handle various character encodings

Fixes #20"

# Feature
git commit -m "Feature: Add bulk email organization tool (#25)

- Implement damien_organize_emails tool
- Support natural language pattern matching
- Add dry-run mode for preview

Fixes #25"

# Documentation
git commit -m "Docs: Update MCP tool usage guide (#23)

- Add troubleshooting section
- Document all 48 tools
- Include usage examples

Fixes #23"
```

## Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **Major** (1.0.0): Breaking changes
- **Minor** (0.1.0): New features, backward-compatible
- **Patch** (0.0.1): Bug fixes, backward-compatible

### Release Workflow

1. **Merge PRs**: Ensure all PRs for release are merged
2. **Update Changelog**: Run changelog generator
3. **Update Version**: Bump version in `package.json`, `pyproject.toml`
4. **Create Release**: Use GitHub releases
5. **Tag Release**: Create git tag

```bash
# Update changelog (automated)
npm run generate-changelog

# Commit changes
git add .
git commit -m "Chore: Prepare release v1.2.0"

# Create tag
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin v1.2.0

# Create GitHub release
gh release create v1.2.0 --generate-notes
```

## Getting Help

- **Issues**: Create an issue for bugs or questions
- **Discussions**: Use GitHub Discussions for general questions
- **Documentation**: Check `docs/` directory
- **MCP Tools**: See `MCP_TOOL_USAGE_GUIDE.md`

## Code of Conduct

- Be respectful and professional
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

## License

By contributing to Damien Email Wrestler, you agree that your contributions will be licensed under the project's license.

---

Thank you for contributing! Your efforts help make Damien Email Wrestler better for everyone.
