#!/bin/bash

# Quick validation script for startup documentation
echo "🔍 Validating Damien Email Wrestler startup scripts..."

# Check if all required scripts exist and are executable
scripts=("setup.sh" "start.sh" "test.sh")
for script in "${scripts[@]}"; do
    if [ -x "scripts/$script" ]; then
        echo "✅ scripts/$script is executable"
    else
        echo "❌ scripts/$script is missing or not executable"
    fi
done

# Check if Docker Compose file exists
if [ -f "docker-compose.yml" ]; then
    echo "✅ docker-compose.yml exists"
else
    echo "❌ docker-compose.yml missing"
fi

# Check if environment template exists
if [ -f ".env.example" ]; then
    echo "✅ .env.example exists"
else
    echo "❌ .env.example missing"
fi

# Check basic script syntax
for script in "${scripts[@]}"; do
    if bash -n "scripts/$script" 2>/dev/null; then
        echo "✅ scripts/$script syntax is valid"
    else
        echo "❌ scripts/$script has syntax errors"
    fi
done

echo ""
echo "📋 Quick Start Command Test:"
echo "   git clone https://github.com/ivan-rivera-projects/Damien-Email-Wrestler.git"
echo "   cd Damien-Email-Wrestler"
echo "   ./scripts/start.sh"
echo ""
echo "✅ Validation complete!"
