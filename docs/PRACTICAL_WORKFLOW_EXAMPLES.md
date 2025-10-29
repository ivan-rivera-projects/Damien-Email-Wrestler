# Practical Workflow Examples - Real Sessions

This document captures real-world examples of the GitHub workflow in action, with actual commands and outcomes from our development sessions.

**Purpose**: Learn by seeing exactly how the workflow works in practice, with real commands, real outputs, and real results.

---

## Example 1: Committing the GitHub Workflow Setup

**Date**: October 28, 2025
**Task**: Commit all the GitHub workflow automation files we just created
**Complexity**: Medium (15 files, multiple directories)
**Time**: ~2 minutes

### Situation

We just created a complete GitHub workflow automation system:
- Issue templates (bug report, feature request)
- PR template with auto-population
- GitHub Actions workflows (auto-labeling, PR validation, changelog generation)
- Comprehensive documentation (CONTRIBUTING.md, guides, walkthroughs)
- Utility scripts (interactive issue creator, bulk operations)

**Total**: 15 new files, 3,841 lines of code/documentation

**Challenge**: How do we commit these changes properly using the PR workflow?

### The Workflow

#### Step 1: Check What We Have

```bash
$ git status
```

**Output**:
```
On branch main
Your branch is up to date with 'origin/main'.

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	.github/
	docs/BRANCH_PROTECTION_SETUP.md
	docs/GITHUB_SETUP_COMPLETE.md
	docs/GITHUB_WORKFLOW_GUIDE.md
	docs/WORKFLOW_WALKTHROUGH.md
	scripts/create-github-issues.js
	scripts/create-issue-quick.js
	scripts/create-labels.js

nothing added to commit but untracked files present
```

**Learning**: We have 15 untracked files ready to commit. Since branch protection isn't enabled yet, we COULD commit directly to main, but we're using the PR workflow to practice.

#### Step 2: Create Feature Branch

```bash
$ git checkout -b feature/github-workflow-automation
```

**Output**:
```
Switched to a new branch 'feature/github-workflow-automation'
```

**Learning**: Always create a descriptive branch name:
- `feature/` prefix for new features
- `bugfix/` prefix for bug fixes
- `docs/` prefix for documentation
- Include issue number if applicable: `feature/issue-25-description`

#### Step 3: Stage Files

```bash
$ git add .github/ docs/BRANCH_PROTECTION_SETUP.md docs/GITHUB_SETUP_COMPLETE.md \
  docs/GITHUB_WORKFLOW_GUIDE.md docs/WORKFLOW_WALKTHROUGH.md \
  scripts/create-github-issues.js scripts/create-labels.js scripts/create-issue-quick.js
```

**Alternative** (if all files are related):
```bash
$ git add .github/ docs/ scripts/
```

**Learning**: Be selective about what you stage. Don't `git add .` blindly - review what you're committing.

#### Step 4: Verify Staged Files

```bash
$ git status
```

**Output**:
```
On branch feature/github-workflow-automation
Changes to be committed:
	new file:   .github/CONTRIBUTING.md
	new file:   .github/ISSUE_TEMPLATE/bug_report.yml
	new file:   .github/ISSUE_TEMPLATE/config.yml
	new file:   .github/ISSUE_TEMPLATE/feature_request.yml
	new file:   .github/pull_request_template.md
	new file:   .github/workflows/auto-label-issues.yml
	new file:   .github/workflows/generate-changelog.yml
	new file:   .github/workflows/pr-validation.yml
	new file:   docs/BRANCH_PROTECTION_SETUP.md
	new file:   docs/GITHUB_SETUP_COMPLETE.md
	new file:   docs/GITHUB_WORKFLOW_GUIDE.md
	new file:   docs/WORKFLOW_WALKTHROUGH.md
	new file:   scripts/create-github-issues.js
	new file:   scripts/create-issue-quick.js
	new file:   scripts/create-labels.js
```

**Learning**: Always verify before committing. Make sure only intended files are staged.

#### Step 5: Commit with Descriptive Message

```bash
$ git commit -m "Add GitHub workflow automation (Phase 2 & 3)

- Add issue templates (bug report, feature request)
- Add PR template with auto-population and issue linking
- Add GitHub Actions workflows:
  * Auto-labeling for issues based on keywords
  * PR validation with automated requirement checks
  * Changelog generation from issues and PRs
- Add comprehensive documentation:
  * CONTRIBUTING.md - Development workflow guide
  * BRANCH_PROTECTION_SETUP.md - Branch protection setup
  * GITHUB_WORKFLOW_GUIDE.md - Complete workflow reference
  * WORKFLOW_WALKTHROUGH.md - Practical examples
  * GITHUB_SETUP_COMPLETE.md - Implementation summary
- Add utility scripts:
  * create-github-issues.js - Bulk issue creation
  * create-labels.js - GitHub label setup automation
  * create-issue-quick.js - Interactive issue creator CLI

This completes Phase 2 (ongoing workflow) and Phase 3 (advanced
integration) of the GitHub workflow strategy.

Features:
- Automated issue labeling based on content keywords
- PR validation ensures requirements are met before merge
- Changelog auto-generated from closed issues/PRs
- Professional templates for consistent documentation
- Quick CLI tools for rapid issue management"
```

**Output**:
```
[feature/github-workflow-automation c307ad1] Add GitHub workflow automation (Phase 2 & 3)
 15 files changed, 3841 insertions(+)
 create mode 100644 .github/CONTRIBUTING.md
 create mode 100644 .github/ISSUE_TEMPLATE/bug_report.yml
 ... (15 files total)
```

**Learning**: Commit messages should:
- Have a clear, concise first line (summary)
- Include detailed bullet points of what changed
- Explain WHY the changes were made
- Reference issues if applicable (`Fixes #123`)
- Use proper formatting (blank line after summary)

**Commit Message Structure**:
```
Type: Short summary (50 chars or less)

- Detailed change 1
- Detailed change 2
- Detailed change 3

Additional context or explanation.

Fixes #123
```

#### Step 6: Push Branch to GitHub

```bash
$ git push origin feature/github-workflow-automation
```

**Output**:
```
remote:
remote: Create a pull request for 'feature/github-workflow-automation' on GitHub by visiting:
remote:      https://github.com/ivan-rivera-projects/Damien-Email-Wrestler/pull/new/feature/github-workflow-automation
remote:
To https://github.com/ivan-rivera-projects/Damien-Email-Wrestler.git
 * [new branch]      feature/github-workflow-automation -> feature/github-workflow-automation
```

**Learning**: GitHub helpfully provides a direct link to create a PR. You can click this link or use the `gh` CLI.

#### Step 7: Create Pull Request

```bash
$ gh pr create --title "Add GitHub workflow automation (Phase 2 & 3)" \
  --body "## Description
This PR implements Phase 2 (second half) and Phase 3 of the GitHub workflow strategy.

## Related Issues
This work establishes the foundation for existing issues (#17-23).

## Type of Change
- [x] Documentation update
- [x] CI/CD changes

## Changes Made
- Created issue templates with structured forms
- Created PR template with auto-population
- Implemented 3 GitHub Actions workflows
- Added comprehensive documentation
- Created interactive CLI tools

## Testing Performed
- [x] All files created successfully
- [x] File structure follows best practices
- [x] Documentation reviewed for accuracy

## Pre-Deployment Checklist
- [x] Self-review completed
- [x] Documentation updated
- [x] No service changes required"
```

**Output**:
```
https://github.com/ivan-rivera-projects/Damien-Email-Wrestler/pull/24
```

**Learning**: The PR is now created as #24. You can also use `gh pr create --web` to open a browser with the PR template pre-filled.

#### Step 8: View the Pull Request

```bash
$ gh pr view 24
```

**Output** (truncated):
```
title:	Add GitHub workflow automation (Phase 2 & 3)
state:	OPEN
author:	ivan-rivera-projects
number:	24
url:	https://github.com/ivan-rivera-projects/Damien-Email-Wrestler/pull/24
additions:	3841
deletions:	0

## Description
This PR implements Phase 2 (second half) and Phase 3 of the GitHub
workflow strategy, adding professional-grade automation and templates.
...
```

**Learning**: You can review the PR in the terminal or open it in browser with `gh pr view 24 --web`.

#### Step 9: Merge the Pull Request

```bash
$ gh pr merge 24 --squash --delete-branch
```

**Output**:
```
Updating 79c8aa4..12f583e
Fast-forward
 .github/CONTRIBUTING.md                    | 418 +++++++++++++++++++++++
 .github/ISSUE_TEMPLATE/bug_report.yml      | 121 +++++++
 ... (15 files)
 15 files changed, 3841 insertions(+)

From https://github.com/ivan-rivera-projects/Damien-Email-Wrestler
 * branch            main       -> FETCH_HEAD
   79c8aa4..12f583e  main       -> origin/main
```

**Learning**: Merge options:
- `--squash`: Combines all commits into one clean commit (recommended for features)
- `--merge`: Keeps all individual commits (preserves detailed history)
- `--rebase`: Rebases commits onto main (linear history)
- `--delete-branch`: Automatically deletes feature branch after merge

#### Step 10: Verify You're Back on Main

```bash
$ git branch
```

**Output**:
```
* main
```

**Learning**: The merge command automatically switched us back to `main` and pulled the latest changes. The feature branch is deleted on GitHub and locally.

### Results

**What Was Accomplished**:
- ✅ 15 files committed and merged
- ✅ 3,841 lines of code/documentation added
- ✅ Professional PR workflow practiced
- ✅ Clean git history maintained
- ✅ Feature branch cleaned up automatically

**What's Now Active on GitHub**:
- ✅ Issue templates: https://github.com/ivan-rivera-projects/Damien-Email-Wrestler/issues/new/choose
- ✅ PR template: Will auto-populate on next PR
- ✅ GitHub Actions: Auto-labeling, PR validation, changelog generation
- ✅ Documentation: Complete workflow guides

**Time Breakdown**:
- Create branch: 5 seconds
- Stage files: 10 seconds
- Write commit message: 30 seconds
- Push branch: 10 seconds
- Create PR: 30 seconds
- Review and merge: 20 seconds
- **Total: ~2 minutes**

### Key Takeaways

1. **Branch Naming Matters**: Use descriptive names with prefixes (`feature/`, `bugfix/`, `docs/`)

2. **Commit Messages Are Documentation**: Future you (and others) will thank you for detailed commit messages

3. **PR Workflow Is Fast**: Even with 15 files, the entire process took ~2 minutes

4. **Squash Merge Keeps History Clean**: One commit per feature makes history readable

5. **Automation Helps**: `gh pr merge --squash --delete-branch` handles cleanup automatically

6. **This Workflow Scales**: Same process works for 1 file or 100 files

### Commands Cheat Sheet (From This Example)

```bash
# Quick PR workflow
git checkout -b feature/description
git add <files>
git commit -m "Type: Summary

- Details"
git push origin feature/description
gh pr create --fill
gh pr merge --squash --delete-branch

# Even faster (if commit message is short)
git checkout -b feature/description
git add <files> && git commit -m "Short message"
git push origin HEAD && gh pr create --fill && gh pr merge --auto --squash --delete-branch
```

---

## Example 2: Create and Fix an Issue from Backlog

**Date**: _To be completed in session_
**Task**: Select an existing issue from #17-23, create branch, fix it, create PR, and merge
**Complexity**: Medium-High (involves actual code or documentation changes)
**Time**: ~10-15 minutes
**Status**: 🔄 Ready to complete

### Objectives

By the end of this example, you will:
- Practice viewing and selecting issues from your backlog
- Create a branch linked to a specific issue
- Make actual changes to fix the issue
- Test the changes locally
- Create a PR that auto-closes the issue when merged
- Experience the full development lifecycle

### Prerequisites

- Issues #17-23 already created in GitHub
- Local repository up to date with main
- Services running for testing (if needed)

### The Workflow

#### Step 1: View Available Issues

```bash
# List all open issues
$ gh issue list

# View specific issue
$ gh issue view 20

# Search for issues by keyword
$ gh issue list --search "email body"
```

**What to look for**:
- Issue number and title
- Issue description and context
- Labels (severity, type)
- Any comments or discussion

#### Step 2: Choose an Issue to Fix

**Recommendation**: Start with a documentation issue (easier) or a medium-complexity bug.

Good candidates from your backlog:
- **Issue #17**: Script naming documentation (docs update - easy)
- **Issue #20**: Email body retrieval (code fix - medium)
- **Issue #21**: Pattern coverage metric (code/logic - medium)
- **Issue #22**: Redundant API messages (code cleanup - easy)
- **Issue #23**: MCP documentation (docs update - medium)

**For this example, we'll use**: _[To be determined in session]_

#### Step 3: Create Branch Linked to Issue

```bash
# Update main first
$ git checkout main && git pull

# Create branch with issue number
$ git checkout -b bugfix/issue-20-email-body-retrieval
# or
$ git checkout -b docs/issue-17-script-naming
```

**Branch naming pattern**:
- `bugfix/issue-##-short-description` for bugs
- `feature/issue-##-short-description` for features
- `docs/issue-##-short-description` for documentation

#### Step 4: Make the Changes

_[Actual changes will be documented during session]_

**Example structure**:
```bash
# For documentation fix
$ nano docs/SOME_FILE.md
# ... make edits ...

# For code fix
$ nano damien-cli/some_module.py
# ... implement fix ...
```

#### Step 5: Test the Changes

```bash
# For service changes
$ ./scripts/stop-all.sh
$ ./scripts/start-all.sh
$ ./scripts/status.sh

# For documentation
$ # Preview markdown rendering
$ # Verify links aren't broken
```

#### Step 6: Commit with Issue Reference

```bash
$ git add <changed-files>
$ git commit -m "Fix: Resolve email body retrieval issue (#20)

- Implement proper MIME multipart parsing
- Add support for HTML and text body extraction
- Handle various character encodings
- Add error handling for malformed emails

Tested with:
- HTML-only emails ✓
- Multipart emails ✓
- Text-only emails ✓

Fixes #20"
```

**Key**: Use `Fixes #20` to auto-close issue when PR merges

#### Step 7: Push and Create PR

```bash
$ git push origin bugfix/issue-20-email-body-retrieval

$ gh pr create --web
# Or with CLI:
$ gh pr create --title "Fix: Resolve email body retrieval (#20)" \
  --body "Fixes #20

## Changes
- Implemented MIME parsing
- Added body extraction
- Added error handling

## Testing
- Tested with various email formats
- All tests passing"
```

#### Step 8: Review and Merge

```bash
# View PR
$ gh pr view 25

# Check status
$ gh pr checks 25

# Merge
$ gh pr merge 25 --squash --delete-branch
```

#### Step 9: Verify Issue Closed

```bash
# Check issue status (should be closed)
$ gh issue view 20
```

### Expected Outcomes

- ✅ Issue selected from backlog
- ✅ Branch created with proper naming
- ✅ Changes made and tested
- ✅ PR created with issue link
- ✅ PR merged successfully
- ✅ Issue automatically closed
- ✅ Clean git history maintained

### Key Learnings

1. **Issue-Driven Development**: Always link PRs to issues
2. **Testing Matters**: Test before creating PR
3. **Auto-Close Magic**: `Fixes #20` automatically closes issue
4. **Branch Naming**: Include issue number for traceability
5. **Complete Cycle**: Issue → Branch → Fix → PR → Merge → Close

### Real Session Notes

_[To be filled during actual session with:]_
- Issue chosen
- Challenges encountered
- Solutions found
- Actual commands executed
- Time taken
- Lessons learned

---

## Example 3: Interactive Issue Creation with CLI Tool

**Date**: _To be completed in session_
**Task**: Use the interactive issue creator script we built
**Complexity**: Low (testing our own tool)
**Time**: ~5 minutes
**Status**: 🔄 Ready to complete

### Objectives

By the end of this example, you will:
- Use the `create-issue-quick.js` tool interactively
- Experience the guided issue creation process
- See how the tool automates label assignment
- Create an issue without leaving the terminal
- Immediately work on the created issue

### Prerequisites

- Script executable: `chmod +x scripts/create-issue-quick.js`
- GitHub CLI authenticated
- You have an idea for an issue to create

### The Workflow

#### Step 1: Run the Interactive Tool

```bash
$ node scripts/create-issue-quick.js
```

**Expected Output**:
```
╔═══════════════════════════════════════════════════════════╗
║  Quick Issue Creator - Damien Platform                   ║
╚═══════════════════════════════════════════════════════════╝

📝 Create a new GitHub issue

Issue Type:
1. Bug Report
2. Feature Request
3. Documentation
4. Other

Select type (1-4):
```

#### Step 2: Select Issue Type

**Example interaction**:
```
Select type (1-4): 1

Issue Title: Email parsing fails with special characters

Severity:
1. Critical (blocks workflow)
2. High (significant impact)
3. Medium (noticeable impact)
4. Low (minor impact)

Select severity (1-4): 2

Description (press Enter twice when done):
When processing emails with special characters like émails or 日本語,
the parser fails with encoding error.

Steps to reproduce:
1. Send email with unicode characters
2. Run damien_get_email_details
3. Observe error

Additional labels (comma-separated, or press Enter to skip):
type:data-retrieval

Assign to (@username or press Enter to skip):
@me
```

#### Step 3: Review and Confirm

**Tool shows preview**:
```
╔═══════════════════════════════════════════════════════════╗
║  Issue Preview                                            ║
╚═══════════════════════════════════════════════════════════╝

Title: Email parsing fails with special characters
Type: Bug
Labels: bug, high, type:data-retrieval
Assignee: @me

Description:
When processing emails with special characters like émails or 日本語,
the parser fails with encoding error.

Steps to reproduce:
1. Send email with unicode characters
2. Run damien_get_email_details
3. Observe error

Create this issue? (y/n): y
```

#### Step 4: Issue Created

**Output**:
```
📤 Creating issue...

✅ Issue created successfully!
https://github.com/ivan-rivera-projects/Damien-Email-Wrestler/issues/25

🔗 Issue #25
   View: https://github.com/ivan-rivera-projects/Damien-Email-Wrestler/issues/25
```

#### Step 5: Immediately Work on the Issue (Optional)

```bash
# Create branch for the new issue
$ git checkout -b bugfix/issue-25-email-parsing

# Make changes
# ... fix the bug ...

# Follow standard PR workflow
$ git add . && git commit -m "Fix: Handle unicode in email parsing (#25)"
$ git push origin bugfix/issue-25-email-parsing
$ gh pr create --title "Fix: Handle unicode in email parsing (#25)" --body "Fixes #25"
$ gh pr merge --squash --delete-branch
```

### Expected Outcomes

- ✅ Interactive tool provides guided experience
- ✅ Issue created without opening browser
- ✅ Proper labels assigned automatically
- ✅ Issue assigned to you
- ✅ Ready to work on issue immediately

### Tool Features Demonstrated

1. **Guided Creation**: Step-by-step prompts
2. **Smart Defaults**: Auto-assigns labels based on type
3. **Preview**: Review before creating
4. **Fast**: Entire process in ~2 minutes
5. **Terminal-Based**: No context switching

### Comparison: Manual vs Tool

**Manual (Web UI)**:
1. Go to GitHub in browser
2. Navigate to Issues → New Issue
3. Select template
4. Fill out form fields
5. Remember to add labels
6. Submit
**Time**: ~5 minutes with context switching

**Quick Issue Tool**:
1. Run `node scripts/create-issue-quick.js`
2. Answer prompts
3. Confirm
**Time**: ~2 minutes, no context switching

### Real Session Notes

_[To be filled during actual session with:]_
- Issue created
- Labels assigned
- Time taken
- User experience observations
- Any improvements needed for the tool

---

## Example 4: Quick Documentation Fix (Speed Run)

**Date**: _To be completed in session_
**Task**: Make a small documentation update and complete PR in under 1 minute
**Complexity**: Low (single file, minor change)
**Time**: ~30-60 seconds
**Status**: 🔄 Ready to complete

### Objectives

By the end of this example, you will:
- Experience how fast the workflow can be for routine changes
- Practice the "muscle memory" workflow
- See that branch protection doesn't slow you down
- Learn speed optimization techniques
- Build confidence for quick updates

### Prerequisites

- Aliases set up (optional but recommended)
- Familiarity with basic git commands
- A small documentation change to make

### Example Changes to Make

Pick ONE of these quick fixes:
- Fix a typo in README.md
- Add a missing link in documentation
- Update a version number or date
- Clarify a confusing sentence
- Add a tip or note to a guide

**For this example**: _[To be chosen in session]_

### The Workflow (Speed Optimized)

#### Version A: With Aliases (Fastest)

**Setup aliases first** (add to `~/.zshrc`):
```bash
alias qpr='git push origin HEAD && gh pr create --fill && gh pr merge --auto --squash --delete-branch'
```

**Then**:
```bash
$ git checkout -b docs/fix-typo-readme
$ nano README.md  # Make change
$ git add README.md && git commit -m "Docs: Fix typo in README"
$ qpr
# Done! (~30 seconds)
```

#### Version B: Without Aliases (Still Fast)

```bash
# One-liner branch creation and switch
$ git checkout -b docs/quick-fix

# Make change
$ nano docs/SOME_FILE.md

# One-liner add, commit, push
$ git add . && git commit -m "Docs: Update installation guide" && git push origin docs/quick-fix

# One-liner PR create and merge
$ gh pr create --fill && gh pr merge --auto --squash --delete-branch

# Done! (~60 seconds)
```

#### Step-by-Step Breakdown

```bash
# 1. Create branch (5 seconds)
$ git checkout -b docs/fix-readme-typo

# 2. Make change (10 seconds)
$ nano README.md
# Fix typo, save, exit

# 3. Commit (5 seconds)
$ git add README.md && git commit -m "Docs: Fix typo"

# 4. Push (5 seconds)
$ git push origin docs/fix-readme-typo

# 5. Create & merge PR (10 seconds)
$ gh pr create --fill && gh pr merge --auto --squash --delete-branch

# 6. Switch back to main (5 seconds)
$ git checkout main && git pull

# Total: ~40 seconds
```

### Speed Optimization Tips

1. **Use `HEAD` instead of branch name**:
   ```bash
   git push origin HEAD  # Pushes current branch
   ```

2. **Chain commands with `&&`**:
   ```bash
   git add . && git commit -m "Message" && git push origin HEAD
   ```

3. **Use `--fill` for quick PRs**:
   ```bash
   gh pr create --fill  # Uses commit message
   ```

4. **Auto-merge when no review needed**:
   ```bash
   gh pr merge --auto --squash --delete-branch
   ```

5. **Set up tab completion** (zsh):
   ```bash
   # In ~/.zshrc
   autoload -Uz compinit && compinit
   ```

### Expected Outcomes

- ✅ Documentation fix completed in under 1 minute
- ✅ Proper git workflow maintained
- ✅ Clean git history
- ✅ No shortcuts taken (full PR process)
- ✅ Confidence in fast workflow

### The Point

**Branch protection doesn't slow you down for routine work**. With practice and proper tools, even small changes flow through the PR process quickly and maintain quality standards.

### Real Session Notes

_[To be filled during actual session with:]_
- Change made
- Actual time taken
- Commands used
- Optimization tricks discovered
- Before/after confidence level

---

## Example 5: Test GitHub Actions Workflows (Automation in Action)

**Date**: _To be completed in session_
**Task**: Create test issue and PR to see our automation workflows in action
**Complexity**: Low (just testing what we built)
**Time**: ~5 minutes
**Status**: 🔄 Ready to complete

### Objectives

By the end of this example, you will:
- See auto-labeling workflow trigger and run
- Experience PR validation in real-time
- Understand how GitHub Actions enhance workflow
- Verify our automation is working correctly
- Learn to debug workflow issues if needed

### Prerequisites

- GitHub Actions enabled in repository
- Workflows merged from PR #24
- At least one workflow run completed (our initial merge)

### Part A: Test Auto-Labeling Workflow

#### Step 1: Create Test Issue with Keywords

```bash
$ gh issue create \
  --title "Tool fails with timeout error during bulk operations" \
  --body "The damien_ai_bulk_operations tool fails when processing more than 1000 emails.

Steps to reproduce:
1. Call damien_ai_bulk_operations with max_emails=1500
2. Wait for analysis to complete
3. Tool times out with no error message

This needs investigation to determine root cause."
```

#### Step 2: View the Issue

```bash
$ gh issue view <issue-number> --web
```

#### Step 3: Observe Auto-Labeling

**What to look for**:
- Workflow runs in Actions tab
- Labels automatically added:
  - `bug` (from "fails" keyword)
  - `type:tool-failure` (from "tool fails" keyword)
  - `needs-investigation` (from "needs investigation" keyword)
- Comment posted by bot explaining label choices

**Check workflow run**:
```bash
$ gh run list --workflow=auto-label-issues.yml
$ gh run view <run-id>
```

### Part B: Test PR Validation Workflow

#### Step 1: Create Test PR (Intentionally Incomplete)

```bash
# Create test branch
$ git checkout -b test/pr-validation

# Make a trivial change
$ echo "# Test PR" > TEST_PR.md
$ git add TEST_PR.md
$ git commit -m "Test: PR validation"
$ git push origin test/pr-validation

# Create PR without issue link (intentionally incomplete)
$ gh pr create --title "Test PR validation" \
  --body "This is a test PR to see validation in action.

No issue links included intentionally."
```

#### Step 2: Watch Validation Run

```bash
$ gh pr view <pr-number> --web
```

**What to observe**:
- PR validation workflow triggers
- Comment posted with validation report
- Should show: ❌ Missing Issue Link
- Should show: ⚠️ Title Convention warning
- Should show: ⚠️ Description warning

#### Step 3: Fix PR to Pass Validation

```bash
# Update PR description
$ gh pr edit <pr-number> --body "This is a test PR to see validation.

Relates to #17

## Testing
- [x] Validation tested"
```

**Observe**:
- Validation re-runs automatically
- New comment posted with updated status
- Should show: ✅ Issue Links Found
- Should show: Improved validation status

#### Step 4: Clean Up Test PR

```bash
$ gh pr close <pr-number> --delete-branch
$ rm TEST_PR.md
$ git checkout main
```

### Part C: Examine Workflow Logs

#### View All Workflow Runs

```bash
# List all recent runs
$ gh run list

# Filter by workflow
$ gh run list --workflow=auto-label-issues.yml
$ gh run list --workflow=pr-validation.yml

# View specific run details
$ gh run view <run-id>

# View logs
$ gh run view <run-id> --log
```

### Expected Outcomes

- ✅ Auto-labeling workflow triggers and adds labels
- ✅ PR validation workflow checks requirements
- ✅ Bot comments posted with helpful information
- ✅ Workflows run automatically on events
- ✅ Logs available for debugging

### Understanding the Workflows

**Auto-Labeling Workflow**:
- **Triggers**: Issue creation or edit
- **Actions**: Scans title/body for keywords
- **Output**: Adds labels, posts comment
- **Time**: ~10-20 seconds

**PR Validation Workflow**:
- **Triggers**: PR creation, edit, or sync
- **Actions**: Checks issue links, title, description
- **Output**: Posts validation report
- **Time**: ~15-30 seconds

**Changelog Generation**:
- **Triggers**: Manual or release creation
- **Actions**: Scans commits, generates CHANGELOG.md
- **Output**: Updated changelog file
- **Time**: ~30-60 seconds

### Troubleshooting Workflows

**If workflows don't run**:
```bash
# Check if Actions are enabled
# Go to: Settings → Actions → General

# Check workflow syntax
$ gh workflow list

# View failed runs
$ gh run list --status=failure

# Re-run failed workflow
$ gh run rerun <run-id>
```

**Common issues**:
1. Actions disabled in repo settings
2. Workflow file syntax error
3. Missing permissions in workflow
4. Rate limiting (rare for small repos)

### Real Session Notes

_[To be filled during actual session with:]_
- Issues/PRs created for testing
- Workflows triggered
- Labels auto-assigned
- Validation results
- Any workflow issues encountered
- Solutions found

---

## Tips from Real Experience

### When Things Go Wrong

**Scenario**: You committed to the wrong branch
```bash
# Undo last commit but keep changes
git reset --soft HEAD~1

# Switch to correct branch
git checkout correct-branch

# Commit again
git add . && git commit -m "Your message"
```

**Scenario**: You need to update your PR after feedback
```bash
# Make changes on your feature branch
git checkout feature/your-branch

# Make fixes
# ... edit files ...

# Commit and push
git add . && git commit -m "Address review feedback"
git push origin feature/your-branch

# PR automatically updates!
```

**Scenario**: You forgot to create a branch
```bash
# If you haven't committed yet
git stash
git checkout -b feature/proper-branch
git stash pop
git add . && git commit -m "Message"

# If you already committed to main (before push)
git branch feature/proper-branch
git reset --hard origin/main
git checkout feature/proper-branch
```

### Pro Tips

1. **Use `git status` Frequently**: Check what's staged before committing

2. **Review Diffs Before Committing**:
   ```bash
   git diff          # Unstaged changes
   git diff --staged # Staged changes
   ```

3. **Commit Early, Commit Often**: Small, focused commits are better than large ones

4. **Use Draft PRs for Work in Progress**:
   ```bash
   gh pr create --draft
   # When ready:
   gh pr ready
   ```

5. **Set Up Aliases** (add to `~/.zshrc`):
   ```bash
   alias gs='git status'
   alias gco='git checkout'
   alias gp='git push origin HEAD'
   alias gpr='gh pr create --fill'
   ```

---

## FAQ from Real Sessions

**Q: What if I make a mistake in the PR?**
A: Just push more commits to the same branch. The PR updates automatically.

**Q: Can I delete a PR?**
A: Yes: `gh pr close 24 --delete-branch` (closes without merging)

**Q: How do I update my branch with latest main?**
A:
```bash
git checkout feature/your-branch
git fetch origin
git merge origin/main  # or: git rebase origin/main
```

**Q: What if the PR has merge conflicts?**
A:
```bash
git checkout feature/your-branch
git fetch origin
git merge origin/main
# Fix conflicts in editor
git add .
git commit -m "Resolve merge conflicts"
git push origin feature/your-branch
```

---

## Document Updates

This document grows as we complete more real-world examples together. Each example captures:
- The actual situation and context
- Real commands executed
- Actual outputs received
- Problems encountered and solutions
- Time taken and lessons learned

**Last Updated**: October 28, 2025
**Examples Completed**: 1
**Next Example**: TBD
