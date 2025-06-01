#!/bin/bash
# File: consolidate_docs.sh

echo "📚 Starting documentation consolidation..."

# Create archive structure
mkdir -p docs/archive/{historical,implementation,architecture,deprecated}

# Move historical documents
echo "Moving historical documents..."
mv PHASE_*.md docs/archive/historical/ 2>/dev/null || true
mv phase_*.md docs/archive/historical/ 2>/dev/null || true
mv *_SUMMARY.md docs/archive/historical/ 2>/dev/null || true
mv *_STATUS.md docs/archive/historical/ 2>/dev/null || true
mv CHANGELOG.md docs/archive/historical/ 2>/dev/null || true

# Move implementation details
echo "Moving implementation documents..."
mv AI_INTELLIGENCE_*.md docs/archive/implementation/ 2>/dev/null || true
mv RAGENGINE_*.md docs/archive/implementation/ 2>/dev/null || true
mv INTELLIGENCE_*.md docs/archive/implementation/ 2>/dev/null || true
mv *processor*.py docs/archive/implementation/ 2>/dev/null || true

# Move architecture documents  
echo "Moving architecture documents..."
mv *Architecture*.md docs/archive/architecture/ 2>/dev/null || true
mv *.tiff docs/archive/architecture/ 2>/dev/null || true
mv OPUS-*.md docs/archive/architecture/ 2>/dev/null || true

# Move deprecated files
echo "Moving deprecated documents..."
mv DOCUMENTATION_*.md docs/archive/deprecated/ 2>/dev/null || true
mv Damien*Platform*.md docs/archive/deprecated/ 2>/dev/null || true

# Create archive index
cat > docs/archive/README.md << 'EOF'
# Archived Documentation

This directory contains historical documentation from the Damien Platform development process.

## Structure
- `/historical/` - Phase documentation and status reports
- `/implementation/` - Technical implementation details
- `/architecture/` - Design documents and diagrams
- `/deprecated/` - Obsolete documentation

## Note
These documents are preserved for historical reference but are not maintained for current usage. Refer to the main documentation for current information.
EOF

echo "✅ Documentation consolidation complete!"
echo "📊 Check docs/ directory for new structure"
echo "🗂️ Archived files moved to docs/archive/"
