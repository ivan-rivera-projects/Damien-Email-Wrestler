# GitHub Workflow Walkthrough - Practical Examples

This guide walks through real-world scenarios to help you master the GitHub workflow.

## Branch Protection Reality Check

**With branch protection enabled:**
- ❌ Cannot push directly to `main`
- ❌ Cannot merge without approval (unless solo developer)
- ✅ Must create branch → PR → merge for ALL changes
- ✅ Even documentation updates need PRs

**Why this is actually good:**
- Git history stays clean and traceable
- Every change has context (issue link)
- Easy to revert if something breaks
- Professional workflow from day one

## Handling Different Scenarios

### Scenario 1: Quick Documentation Fix (2 minutes)

**Task**: Fix typo in README.md

```bash
# 1. Create branch (use descriptive name)
git checkout -b docs/fix-readme-typo

# 2. Make the change
echo "Fixed typo" >> README.md

# 3. Commit with clear message
git add README.md
git commit -m "Docs: Fix typo in installation section"

# 4. Push branch
git push origin docs/fix-readme-typo

# 5. Create PR (auto-fills from commit)
gh pr create --fill --body "Minor typo fix in README"

# 6. If you're solo developer, merge immediately
gh pr merge --squash --delete-branch

# Total time: ~2 minutes
```

**Even faster with alias:**
```bash
# Add to ~/.zshrc
alias quick-pr='git push origin HEAD && gh pr create --fill && gh pr merge --squash --auto --delete-branch'

# Then just:
git checkout -b docs/fix-typo
# ... make change ...
git add . && git commit -m "Docs: Fix typo"
quick-pr  # Done!
```

### Scenario 2: File Reorganization (5 minutes)

**Task**: Reorganize documentation files

```bash
# 1. Create issue first (for tracking)
gh issue create \
  --title "Docs: Reorganize documentation structure" \
  --body "Moving docs to better locations for clarity" \
  --label "documentation,low"
# Output: Created issue #24

# 2. Create branch linked to issue
git checkout -b docs/issue-24-reorganize-docs

# 3. Make changes
mkdir -p docs/guides docs/reference
mv docs/SOME_FILE.md docs/guides/
mv docs/ANOTHER_FILE.md docs/reference/

# 4. Commit with issue reference
git add .
git commit -m "Docs: Reorganize documentation structure (#24)

- Move guides to docs/guides/
- Move reference docs to docs/reference/
- Update links in README

Fixes #24"

# 5. Push and create PR
git push origin docs/issue-24-reorganize-docs
gh pr create --title "Docs: Reorganize documentation (#24)" \
  --body "Fixes #24"

# 6. Merge (auto-closes issue #24)
gh pr merge --squash --delete-branch

# Total time: ~5 minutes
```

### Scenario 3: Bug Fix with Testing (15 minutes)

**Task**: Fix a bug reported in issue #20

```bash
# 1. View the issue
gh issue view 20

# 2. Create branch
git checkout -b bugfix/issue-20-email-body-retrieval

# 3. Make code changes
# ... edit files ...

# 4. Test locally
./scripts/stop-all.sh
./scripts/start-all.sh
./scripts/status.sh
# ... verify fix works ...

# 5. Commit with details
git add .
git commit -m "Fix: Resolve email body retrieval issue (#20)

- Implement proper MIME multipart parsing
- Add support for HTML and text body extraction
- Handle various character encodings
- Add error handling for malformed emails

Tested with:
- HTML-only emails ✓
- Multipart emails ✓
- Text-only emails ✓

Fixes #20"

# 6. Push and create PR
git push origin bugfix/issue-20-email-body-retrieval
gh pr create --web  # Use template for detailed PR

# 7. Wait for validation, then merge
gh pr checks  # View status
gh pr merge --squash --delete-branch
```

### Scenario 4: Multiple Small Changes at Once

**Task**: Update several documentation files

**Option A: One PR for all changes** (Recommended for related changes)
```bash
git checkout -b docs/update-multiple-docs
# ... edit file1.md, file2.md, file3.md ...
git add .
git commit -m "Docs: Update installation and setup guides"
git push origin docs/update-multiple-docs
gh pr create --fill
gh pr merge --squash --delete-branch
```

**Option B: Separate PRs** (If unrelated changes)
```bash
# Change 1
git checkout -b docs/update-readme
# ... edit README ...
git add README.md && git commit -m "Docs: Update README"
git push origin docs/update-readme
gh pr create --fill

# Change 2 (start from main)
git checkout main && git pull
git checkout -b docs/update-contributing
# ... edit CONTRIBUTING ...
git add CONTRIBUTING.md && git commit -m "Docs: Update CONTRIBUTING"
git push origin docs/update-contributing
gh pr create --fill

# Merge both
gh pr list  # View PRs
gh pr merge 25 --squash --delete-branch
gh pr merge 26 --squash --delete-branch
```

## Claude Code Integration with GitHub

### How Claude Code Works with GitHub

**Claude Code can help you:**
1. ✅ Create issues programmatically
2. ✅ Draft commit messages
3. ✅ Create PRs with descriptions
4. ✅ Review code changes
5. ✅ Generate changelogs
6. ✅ Manage the workflow

**What Claude Code does via tools:**

```bash
# Claude Code uses the Bash tool to run gh commands
# You can ask Claude to:

"Create an issue for the bug I just described"
→ Claude runs: gh issue create --title "..." --body "..." --label "bug"

"Create a PR for my current branch"
→ Claude runs: gh pr create --title "..." --body "Fixes #..."

"Show me the status of issue #20"
→ Claude runs: gh issue view 20

"Generate a changelog from v1.0.0 to HEAD"
→ Claude runs: gh workflow run generate-changelog.yml
```

### Practical Examples with Claude Code

**Example 1: Finding and fixing a bug**
```
You: "I found a bug where the email body isn't retrieved. Create an issue for this."

Claude Code:
1. Runs: gh issue create --web (or uses create-issue-quick.js)
2. Guides you through template
3. Creates issue #27

You: "Now help me fix this bug"

Claude Code:
1. Creates branch: git checkout -b bugfix/issue-27-email-body
2. Suggests code fixes
3. Tests the changes
4. Commits: git commit -m "Fix: Email body retrieval (#27)"
5. Creates PR: gh pr create --web

You: "Merge the PR"

Claude Code:
1. Checks PR status: gh pr checks
2. Merges: gh pr merge --squash --delete-branch
3. Verifies issue #27 closed
```

**Example 2: Documentation update**
```
You: "Help me reorganize the docs directory"

Claude Code:
1. Creates issue: "Docs: Reorganize documentation structure"
2. Creates branch: docs/issue-28-reorganize
3. Moves files as discussed
4. Updates any broken links
5. Commits and creates PR
6. Merges after your approval
```

**Example 3: Managing multiple issues**
```
You: "Show me all open bugs"

Claude Code runs: gh issue list --label bug

You: "Let's fix issue #20"

Claude Code:
1. Views issue: gh issue view 20
2. Creates branch: bugfix/issue-20-description
3. Helps implement fix
4. Creates PR with proper linking
5. Manages merge after approval
```

## Solo Developer Workflow Optimization

If you're working alone, you can streamline the workflow:

### Option 1: Auto-merge PRs

```bash
# Create PR with auto-merge enabled
gh pr create --fill
gh pr merge --auto --squash --delete-branch

# PR merges automatically when checks pass
```

### Option 2: Require 0 Approvals

In branch protection settings:
- Set "Require approvals" to 0
- Keep "Require PR" enabled
- This gives you the benefits of PRs without waiting for approval

### Option 3: Use Aliases

Add to `~/.zshrc`:

```bash
# Quick commit and PR
alias qpr='git push origin HEAD && gh pr create --fill --body "Quick update" && gh pr merge --auto --squash --delete-branch'

# Quick doc fix
alias docfix='f() { git checkout -b "docs/$1" && git add . && git commit -m "Docs: $2" && qpr; }; f'

# Usage:
docfix fix-typo "Fix typo in README"
```

## Workflow Cheat Sheet

### Daily Workflow

```bash
# Morning: Update main
git checkout main && git pull

# Start work: Create branch
git checkout -b feature/issue-X-description

# Work: Make changes
# ... code ...

# Test: Verify changes
./scripts/stop-all.sh && ./scripts/start-all.sh

# Commit: Save work
git add . && git commit -m "Type: Description (#X)"

# Push: Upload to GitHub
git push origin feature/issue-X-description

# PR: Create pull request
gh pr create --web

# Review: Check status
gh pr checks

# Merge: Complete PR
gh pr merge --squash --delete-branch

# Cleanup: Back to main
git checkout main && git pull
```

### Emergency Hotfix

```bash
# Critical bug in production
git checkout main && git pull
git checkout -b hotfix/critical-issue

# Make minimal fix
# ... fix ...

git add . && git commit -m "Fix: Critical production issue"
git push origin hotfix/critical-issue

# Create PR with high priority
gh pr create --title "🚨 HOTFIX: Critical issue" \
  --label "critical" \
  --body "Emergency fix for production issue"

# Merge immediately (if admin and solo developer)
gh pr merge --admin --squash --delete-branch
```

### Bulk Updates

```bash
# Multiple related changes
git checkout -b chore/bulk-updates

# Make all changes
# ... edit multiple files ...

git add .
git commit -m "Chore: Bulk documentation updates

- Update README
- Fix typos in guides
- Reorganize examples"

git push origin chore/bulk-updates
gh pr create --fill
gh pr merge --squash --delete-branch
```

## Common Questions

**Q: Do I really need a PR for a one-line change?**
A: With branch protection, yes. But it's fast:
```bash
git checkout -b fix/one-line
# ... change one line ...
git add . && git commit -m "Fix: One line change"
git push origin fix/one-line
gh pr create --fill && gh pr merge --auto --squash --delete-branch
# Takes 30 seconds
```

**Q: Can I disable branch protection temporarily?**
A: Yes, but not recommended. Better to:
- Use admin bypass for emergencies
- Or adjust protection to require 0 approvals for solo work

**Q: What if I forget to create an issue first?**
A: That's okay! You can:
1. Create PR first
2. Create issue from PR: "Created issue #X from this PR"
3. Update PR description: "Fixes #X"

**Q: How do I handle work-in-progress changes?**
A: Use draft PRs:
```bash
gh pr create --draft --title "WIP: Feature in progress"
# Work on multiple commits
# When ready:
gh pr ready  # Converts to regular PR
```

## Next Steps

Now that you understand the workflow, let's practice:

1. **Practice Example 1**: Create a test documentation update
2. **Practice Example 2**: Create a test issue and fix it
3. **Set up your aliases** for quick workflow
4. **Configure branch protection** with 0 required approvals (if solo)

Want to walk through a real example together?
