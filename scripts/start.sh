#!/bin/bash

# 🤼‍♂️ Damien Email Wrestler - Quick Start Script
set -e

echo "🤼‍♂️ Starting Damien Email Wrestler..."
echo "====================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }

# Check for Docker
if ! command -v docker >/dev/null 2>&1; then
    print_error "Docker not found. Please install Docker."
    exit 1
fi

# Check for Docker Compose (try both old and new syntax)
DOCKER_COMPOSE_CMD=""
if command -v docker-compose >/dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    print_error "Docker Compose not found. Please install Docker Compose."
    exit 1
fi

print_success "Docker and Docker Compose are available ($DOCKER_COMPOSE_CMD)"

# Check for required files
if [ ! -f "credentials.json" ]; then
    print_error "credentials.json not found. Please follow Gmail API setup guide."
    exit 1
fi

if [ ! -f ".env" ]; then
    print_warning "Creating .env from template..."
    cp .env.example .env
    print_warning "Please edit .env file with your API key and restart"
    exit 1
fi

# Check for Gmail token
if [ ! -f "damien-cli/data/token.json" ]; then
    print_warning "Gmail authentication required..."
    cd damien-cli
    poetry install >/dev/null 2>&1
    poetry run damien login
    cd ..
    print_success "Gmail authentication completed"
fi

# Start services
echo "Starting all services..."
$DOCKER_COMPOSE_CMD up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10
# Check health
if curl -s http://localhost:8892/health | grep -q "ok"; then
    print_success "Damien MCP Server is ready"
else
    print_error "Damien MCP Server failed to start"
fi

if curl -s http://localhost:8081/health | grep -q "ok"; then
    print_success "Smithery Adapter is ready"
else
    print_error "Smithery Adapter failed to start"
fi

echo ""
echo "🎉 Damien Email Wrestler is ready!"
echo ""
echo "🔗 Service URLs:"
echo "  MCP Server: http://localhost:8892"
echo "  Adapter: http://localhost:8081"
echo ""
echo "📚 Next steps:"
echo "  1. Test: ./scripts/test.sh"
echo "  2. Configure Claude Desktop (see README.md)"
echo "  3. Try: 'Show me my unread emails'"
echo ""
echo "To stop: docker-compose down"
echo "Logs: docker-compose logs -f"
