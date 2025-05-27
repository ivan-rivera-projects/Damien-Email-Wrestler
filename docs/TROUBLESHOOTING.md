# Damien Platform Troubleshooting Guide

## Common Issues

### Gmail Authentication Errors

**Error**: "Gmail authentication failed"
**Solutions**:
- Ensure `credentials.json` is in the correct location
- Run `poetry run damien login` to re-authenticate
- Verify Gmail API is enabled in Google Cloud Console
- Check OAuth consent screen configuration

### Service Connection Issues

**Error**: "Connection refused" on ports 8081 or 8892
**Solutions**:
- Verify services are running: `./scripts/start-all.sh`
- Check port conflicts: `lsof -i :8081,8892`
- Review service logs in `logs/` directory

### DynamoDB Configuration Issues

**Error**: "Unable to locate credentials"
**Solutions**:
- Configure AWS credentials: `aws configure`
- Verify DynamoDB table exists
- Check IAM permissions for DynamoDB access

### Import/Module Errors

**Error**: "ModuleNotFoundError" or import issues
**Solutions**:
- Reinstall dependencies: `poetry install`
- Activate virtual environment: `poetry shell`
- Verify Python version: `python --version` (should be 3.13+)

### Test Failures

**Error**: Tests failing during setup
**Solutions**:
- Ensure both services are running before tests
- Check authentication status
- Run individual component tests to isolate issues

## Diagnostic Commands

```bash
# Check service health
curl http://localhost:8892/health  # MCP Server
curl http://localhost:8081/health  # Smithery Adapter

# View service logs
tail -f logs/mcp-server.log
tail -f logs/smithery-adapter.log

# Test Gmail authentication
cd damien-cli && poetry run damien hello

# List available tools
curl http://localhost:8081/tools
```

## Getting Help

1. Check service logs for detailed error messages
2. Verify all prerequisites are installed
3. Test components individually
4. Review configuration files for typos
5. Open GitHub issues with detailed error information

## Performance Issues

- **Slow email operations**: Check Gmail API quotas
- **High memory usage**: Monitor service resource consumption
- **Timeout errors**: Increase timeout values in configuration
