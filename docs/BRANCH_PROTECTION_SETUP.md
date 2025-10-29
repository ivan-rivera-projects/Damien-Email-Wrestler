# Branch Protection Rules Setup

This guide explains how to set up branch protection rules for the Damien Email Wrestler repository to ensure code quality and enforce best practices.

## Why Branch Protection?

Branch protection rules help maintain code quality by:
- Preventing direct commits to main/production branches
- Requiring pull request reviews before merging
- Ensuring all tests pass before merging
- Preventing force pushes that could lose history
- Requiring issue linkage in PRs

## Recommended Protection Rules for `main` Branch

### Via GitHub Web UI

1. **Navigate to Settings**
   - Go to: https://github.com/ivan-rivera-projects/Damien-Email-Wrestler/settings/branches
   - Or: Repository → Settings → Branches

2. **Add Branch Protection Rule**
   - Click "Add branch protection rule"
   - Branch name pattern: `main`

3. **Configure Protection Settings**

   #### ✅ Required Settings

   **Require a pull request before merging**
   - [x] Require approvals: 1 (or more for team environments)
   - [x] Dismiss stale pull request approvals when new commits are pushed
   - [x] Require review from Code Owners (optional, if you create CODEOWNERS file)

   **Require status checks to pass before merging**
   - [x] Require branches to be up to date before merging
   - Select status checks (once Actions run):
     - [ ] PR Validation
     - [ ] Auto-label Issues (if applicable)

   **Require conversation resolution before merging**
   - [x] All conversations must be resolved before merging

   **Do not allow bypassing the above settings**
   - [x] Do not allow bypassing the above settings
     - Exception: Repository admins can bypass (optional)

   #### ⚠️ Important Protections

   **Restrict who can push to matching branches**
   - [x] Restrict pushes that create matching branches
   - Add exceptions: (only repository maintainers)

   **Rules applied to everyone including administrators**
   - [x] Include administrators
     - Ensures even admins follow the process

   **Other Settings**
   - [x] Require linear history (prevents merge commits)
   - [x] Require deployments to succeed before merging (optional)
   - [ ] Lock branch (only for production-ready releases)

4. **Save Changes**
   - Click "Create" or "Save changes"

### Via GitHub CLI

```bash
# Enable branch protection with basic rules
gh api repos/ivan-rivera-projects/Damien-Email-Wrestler/branches/main/protection \
  --method PUT \
  --header "Accept: application/vnd.github+json" \
  --field "required_status_checks[strict]=true" \
  --field "required_status_checks[contexts][]=PR Validation" \
  --field "enforce_admins=true" \
  --field "required_pull_request_reviews[required_approving_review_count]=1" \
  --field "required_pull_request_reviews[dismiss_stale_reviews]=true" \
  --field "required_conversation_resolution=true" \
  --field "restrictions=null"
```

## Protection Rules Summary

| Rule | Setting | Purpose |
|------|---------|---------|
| **Require PR** | ✅ Enabled | All changes go through review |
| **Require Approvals** | 1 reviewer | Code quality gate |
| **Status Checks** | PR Validation | Automated validation |
| **Conversation Resolution** | ✅ Required | All comments addressed |
| **Linear History** | ✅ Enabled | Clean git history |
| **Include Admins** | ✅ Enabled | Enforce for everyone |
| **Dismiss Stale Reviews** | ✅ Enabled | Re-review after changes |

## Additional Configurations

### 1. Create CODEOWNERS File (Optional)

Create `.github/CODEOWNERS` to automatically request reviews from specific people:

```
# CODEOWNERS file

# Default owners for everything
* @ivan-rivera-projects

# Specific component owners
/damien-cli/ @ivan-rivera-projects
/damien-mcp-server/ @ivan-rivera-projects
/docs/ @ivan-rivera-projects

# GitHub Actions and workflows
/.github/ @ivan-rivera-projects
```

### 2. Configure Required Reviewers

For team environments, configure required reviewers:

```bash
# Via gh CLI (requires additional permissions)
gh api repos/ivan-rivera-projects/Damien-Email-Wrestler/branches/main/protection/required_pull_request_reviews \
  --method PATCH \
  --field "required_approving_review_count=2" \
  --field "dismiss_stale_reviews=true" \
  --field "require_code_owner_reviews=true"
```

### 3. Set Up Status Checks

Once GitHub Actions run at least once, you can require specific checks:

1. Go to branch protection settings
2. Under "Require status checks to pass before merging"
3. Search and select:
   - `PR Validation`
   - Any other workflow checks

### 4. Configure Deployment Protections (Optional)

For production deployments:

1. Go to Settings → Environments
2. Create environment: `production`
3. Configure environment protection rules:
   - Required reviewers
   - Wait timer
   - Deployment branches (only `main`)

## Workflow After Protection Rules

### Creating Changes

```bash
# 1. Create feature branch
git checkout -b feature/issue-25-new-feature

# 2. Make changes and commit
git add .
git commit -m "Feature: Add new feature (#25)"

# 3. Push to GitHub
git push origin feature/issue-25-new-feature

# 4. Create PR (will auto-populate with template)
gh pr create --web
```

### Merging Changes

1. **Create PR**: Push branch and create pull request
2. **Automated Checks**: PR Validation workflow runs
3. **Code Review**: Reviewer approves changes
4. **Status Checks**: All checks must pass
5. **Merge**: Squash and merge (recommended) or merge commit

### Emergency Fixes

For critical production issues:

```bash
# 1. Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/issue-30-critical-fix

# 2. Make minimal fix
git add .
git commit -m "Fix: Critical issue (#30)"

# 3. Create PR with high priority label
gh pr create --title "Fix: Critical issue (#30)" --label "critical"

# 4. Request immediate review
# 5. Merge after approval (even admins must follow process)
```

## Bypassing Protection Rules (Emergency Only)

If you absolutely must bypass protection rules (repository admin only):

```bash
# NOT RECOMMENDED - Use only for emergencies

# 1. Temporarily disable protection
gh api repos/ivan-rivera-projects/Damien-Email-Wrestler/branches/main/protection \
  --method DELETE

# 2. Make critical fix
git push origin main

# 3. Re-enable protection immediately
# (Use the CLI command from earlier to re-enable)
```

**⚠️ Warning**: Document any bypass in an issue immediately and explain why it was necessary.

## Verifying Protection Rules

### Via Web UI

1. Go to: https://github.com/ivan-rivera-projects/Damien-Email-Wrestler/settings/branches
2. Verify `main` branch has protection rules

### Via CLI

```bash
# Check current protection status
gh api repos/ivan-rivera-projects/Damien-Email-Wrestler/branches/main/protection

# List all protected branches
gh api repos/ivan-rivera-projects/Damien-Email-Wrestler/branches --jq '.[] | select(.protected == true) | .name'
```

### Testing Protection

Try to push directly to main (should fail):

```bash
git checkout main
git commit --allow-empty -m "Test: Protection rules"
git push origin main
# Should see: "refusing to allow an OAuth App to create or update workflow"
```

## Troubleshooting

### Issue: Can't merge PR even though approved

**Solution**:
- Ensure all status checks passed
- Ensure all conversations resolved
- Ensure branch is up to date with main

### Issue: Status checks not appearing

**Solution**:
- Run workflows at least once
- Check workflow names match exactly
- Verify workflows have correct permissions

### Issue: Admin can't merge without approval

**Solution**:
- This is by design if "Include administrators" is enabled
- Either get approval or temporarily adjust settings

## Best Practices

1. **Never disable protection permanently**
2. **Document any emergency bypasses**
3. **Require reviews for all changes**
4. **Keep status checks lightweight and fast**
5. **Review protection rules quarterly**
6. **Train all contributors on the process**

## Additional Resources

- [GitHub Branch Protection Docs](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [CODEOWNERS Documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [GitHub Actions & Branch Protection](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)

## Next Steps

1. ✅ Set up branch protection rules (this guide)
2. ✅ Create CODEOWNERS file (optional)
3. ✅ Test the workflow by creating a test PR
4. ✅ Train team members on the new process
5. ✅ Monitor and adjust rules as needed

---

**Need Help?** Create an issue with label `type:documentation` if you need assistance with branch protection setup.
