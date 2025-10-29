#!/usr/bin/env node

/**
 * GitHub Label Creator for Damien Platform
 * Creates all labels needed for issue categorization
 */

const { execSync } = require('child_process');

const REPO = 'ivan-rivera-projects/Damien-Email-Wrestler';

// Define labels to create
const LABELS = [
  // Severity labels
  { name: 'critical', color: 'ff0000', description: 'Critical severity - blocks workflow' },
  { name: 'high', color: 'ff6600', description: 'High severity - significant impact' },
  { name: 'medium', color: 'ffaa00', description: 'Medium severity - noticeable impact' },
  { name: 'low', color: 'ffff00', description: 'Low severity - minor impact' },
  
  // Type labels
  { name: 'type:documentation', color: '0066cc', description: 'Documentation related' },
  { name: 'type:logic', color: '0099ff', description: 'Logic/algorithm issue' },
  { name: 'type:tool-failure', color: 'cc0000', description: 'Tool execution failure' },
  { name: 'type:data-retrieval', color: 'ff0099', description: 'Data retrieval issue' },
  { name: 'type:metric', color: '9900ff', description: 'Metric calculation issue' },
  { name: 'type:output-quality', color: '00cc99', description: 'Output quality issue' },
  { name: 'type:docs', color: '0066cc', description: 'Documentation' },
  
  // Status labels
  { name: 'needs-investigation', color: 'ffd700', description: 'Needs investigation' },
  { name: 'data-integrity', color: 'ff00ff', description: 'Data integrity concern' }
];

function createLabel(label) {
  try {
    // Check if label exists first
    const checkCmd = `gh label list --repo ${REPO} --limit 1000 2>/dev/null | grep "^${label.name}[[:space:]]"`;
    
    try {
      execSync(checkCmd, { encoding: 'utf8', stdio: 'pipe' });
      console.log(`⏭️  Skipping "${label.name}" - already exists`);
      return true;
    } catch (e) {
      // Label doesn't exist, proceed to create
    }
    
    const cmd = `gh label create "${label.name}" --color "${label.color}" --description "${label.description}" --repo ${REPO}`;
    execSync(cmd, { encoding: 'utf8' });
    console.log(`✅ Created label: "${label.name}"`);
    return true;
  } catch (error) {
    console.error(`❌ Failed to create label "${label.name}": ${error.message}`);
    return false;
  }
}

async function main() {
  console.log('╔═══════════════════════════════════════════════════════════╗');
  console.log('║  GitHub Label Creator - Damien Platform                  ║');
  console.log('╚═══════════════════════════════════════════════════════════╝\n');
  
  console.log(`📚 Creating labels for: ${REPO}\n`);
  
  let created = 0;
  let failed = 0;
  
  for (const label of LABELS) {
    if (createLabel(label)) {
      created++;
    } else {
      failed++;
    }
  }
  
  console.log('\n╔═══════════════════════════════════════════════════════════╗');
  console.log('║  LABEL CREATION SUMMARY                                   ║');
  console.log('╚═══════════════════════════════════════════════════════════╝');
  console.log(`\n✅ Successful: ${created}/${LABELS.length}`);
  console.log(`❌ Failed: ${failed}/${LABELS.length}`);
  
  if (failed === 0) {
    console.log('\n🎉 All labels created successfully!');
    console.log(`\n👉 Next step: node scripts/create-github-issues.js`);
  } else {
    console.log('\n⚠️  Some labels failed. Check output above.');
    process.exit(1);
  }
}

main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
