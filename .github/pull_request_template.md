## Description
<!-- Provide a clear and concise description of what this PR does -->


## Related Issues
<!-- Link related issues using keywords: Fixes #123, Closes #456, Relates to #789 -->
<!-- Using "Fixes" or "Closes" will automatically close the issue when PR is merged -->

- Fixes #
- Relates to #


## Type of Change
<!-- Mark the relevant option(s) with an [x] -->

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring
- [ ] Testing improvements
- [ ] CI/CD changes


## Changes Made
<!-- Provide a bullet-point list of changes -->

-
-
-


## Testing Performed
<!-- Describe the testing you performed to verify your changes -->

### Manual Testing
- [ ] Tested locally with `./scripts/start-all.sh`
- [ ] Verified MCP server functionality
- [ ] Tested affected tools/commands:
  -

### Automated Testing
- [ ] All existing tests pass
- [ ] Added new tests for new functionality
- [ ] Test coverage: ___% (if applicable)


## Pre-Deployment Checklist
<!-- Ensure these steps are completed before merging -->

- [ ] Code follows project style guidelines
- [ ] Self-review of code performed
- [ ] Comments added for complex logic
- [ ] Documentation updated (if applicable)
  - [ ] README.md
  - [ ] CLAUDE.md
  - [ ] API documentation
  - [ ] MCP_TOOL_USAGE_GUIDE.md
- [ ] No console warnings or errors
- [ ] Services restart cleanly after changes


## Deployment Notes
<!-- Any special instructions for deployment or configuration changes? -->

### Configuration Changes
<!-- List any environment variables, config files, or settings that changed -->


### Migration Required
<!-- Does this PR require any data migration or manual steps? -->

- [ ] No migration required
- [ ] Migration steps documented below:


### Service Restart Required
<!-- Which services need to be restarted? -->

- [ ] MCP Server (port 8892)
- [ ] Minimal Adapter (port 8893)
- [ ] Smithery Adapter (port 8081)
- [ ] All services (`./scripts/stop-all.sh && ./scripts/start-all.sh`)


## Screenshots/Examples
<!-- Add screenshots or example output if applicable -->


## Performance Impact
<!-- Describe any performance implications of these changes -->

- [ ] No performance impact
- [ ] Performance improved
- [ ] Performance considerations documented below:


## Security Considerations
<!-- Highlight any security implications or considerations -->

- [ ] No security implications
- [ ] Security review completed
- [ ] Sensitive data handling addressed


## Rollback Plan
<!-- In case something goes wrong, how do we rollback? -->


## Additional Notes
<!-- Any other information reviewers should know -->


---
## Reviewer Checklist
<!-- For code reviewers -->

- [ ] Code changes reviewed and approved
- [ ] Tests are adequate and passing
- [ ] Documentation is clear and complete
- [ ] Security considerations addressed
- [ ] Performance implications acceptable
- [ ] Breaking changes clearly communicated
