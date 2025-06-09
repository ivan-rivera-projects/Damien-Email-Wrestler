# 🔒 Damien Email Wrestler Security Checklist

## Before Committing Code

### ✅ Environment Variables
- [ ] All API keys are stored in `.env` file, not hardcoded
- [ ] `.env` file is listed in `.gitignore`
- [ ] Scripts load API keys from environment variables
- [ ] No sensitive data in commit messages

### ✅ Gmail Credentials
- [ ] `credentials.json` is NOT in version control
- [ ] `token.json` files are NOT in version control
- [ ] OAuth tokens are stored in ignored directories

### ✅ Scripts
- [ ] No hardcoded API keys in any shell scripts
- [ ] No hardcoded passwords or secrets
- [ ] Use environment variables for all sensitive data
- [ ] Template scripts use `.example` extension

### ✅ Configuration Files
- [ ] `.env.example` contains dummy values only
- [ ] No real API keys in example files
- [ ] Docker compose files don't contain secrets

## How to Check for Exposed Secrets

```bash
# Search for potential API keys in the codebase
grep -r "api_key\|API_KEY\|secret\|SECRET\|password\|PASSWORD" . \
  --exclude-dir=node_modules \
  --exclude-dir=.git \
  --exclude="*.log" \
  --exclude=".env*"

# Search for specific known API key patterns
grep -r "[a-f0-9]{64}" . \
  --exclude-dir=node_modules \
  --exclude-dir=.git \
  --exclude="*.log"

# Check git history for secrets (before pushing)
git log -p | grep -i "api_key\|secret\|password"
```

## If You Accidentally Commit Secrets

1. **DO NOT PUSH** the commit
2. Remove the file/secret from the commit:
   ```bash
   git rm --cached <file-with-secret>
   git commit --amend
   ```
3. If already pushed:
   - Immediately rotate/regenerate the exposed credentials
   - Use `git filter-branch` or BFG Repo-Cleaner to remove from history
   - Force push the cleaned history
   - Notify team members about the force push

## Best Practices

1. **Always use environment variables** for sensitive data
2. **Load from .env files** that are gitignored
3. **Use example files** (`.env.example`) with dummy values
4. **Review changes** before committing: `git diff --staged`
5. **Use secret scanning tools** like GitGuardian or GitHub secret scanning
6. **Rotate credentials regularly** as a precaution

## Files That Should NEVER Be Committed

- `.env` (and all variants)
- `credentials.json`
- `token.json`
- `*.key`
- `*.pem`
- Any file with real API keys or secrets
- AWS credentials
- Database connection strings with passwords
