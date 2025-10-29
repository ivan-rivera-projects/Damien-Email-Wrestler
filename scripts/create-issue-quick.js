#!/usr/bin/env node

/**
 * Quick Issue Creator for Damien Platform
 * Interactive CLI for creating GitHub issues quickly
 */

const readline = require('readline');
const { execSync } = require('child_process');

const REPO = 'ivan-rivera-projects/Damien-Email-Wrestler';

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

function question(prompt) {
  return new Promise((resolve) => {
    rl.question(prompt, resolve);
  });
}

function runCommand(command) {
  try {
    const output = execSync(command, { encoding: 'utf8' });
    return { success: true, output };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

async function main() {
  console.log('╔═══════════════════════════════════════════════════════════╗');
  console.log('║  Quick Issue Creator - Damien Platform                   ║');
  console.log('╚═══════════════════════════════════════════════════════════╝\n');

  // Check gh authentication
  const ghCheck = runCommand('gh auth status');
  if (!ghCheck.success) {
    console.error('❌ Error: GitHub CLI not authenticated');
    console.error('Run: gh auth login');
    process.exit(1);
  }

  console.log('📝 Create a new GitHub issue\n');

  // Issue type
  console.log('Issue Type:');
  console.log('1. Bug Report');
  console.log('2. Feature Request');
  console.log('3. Documentation');
  console.log('4. Other\n');

  const typeChoice = await question('Select type (1-4): ');

  let issueType, labels;
  switch (typeChoice.trim()) {
    case '1':
      issueType = 'Bug';
      labels = ['bug', 'needs-investigation'];
      break;
    case '2':
      issueType = 'Feature';
      labels = ['enhancement'];
      break;
    case '3':
      issueType = 'Documentation';
      labels = ['documentation'];
      break;
    default:
      issueType = 'Other';
      labels = [];
  }

  // Title
  const title = await question('\nIssue Title: ');
  if (!title.trim()) {
    console.error('❌ Title is required');
    rl.close();
    process.exit(1);
  }

  // Severity (for bugs)
  let severity = '';
  if (issueType === 'Bug') {
    console.log('\nSeverity:');
    console.log('1. Critical (blocks workflow)');
    console.log('2. High (significant impact)');
    console.log('3. Medium (noticeable impact)');
    console.log('4. Low (minor impact)\n');

    const severityChoice = await question('Select severity (1-4): ');
    switch (severityChoice.trim()) {
      case '1':
        severity = 'critical';
        break;
      case '2':
        severity = 'high';
        break;
      case '3':
        severity = 'medium';
        break;
      case '4':
        severity = 'low';
        break;
    }

    if (severity) {
      labels.push(severity);
    }
  }

  // Priority (for features)
  let priority = '';
  if (issueType === 'Feature') {
    console.log('\nPriority:');
    console.log('1. Critical');
    console.log('2. High');
    console.log('3. Medium');
    console.log('4. Low\n');

    const priorityChoice = await question('Select priority (1-4): ');
    switch (priorityChoice.trim()) {
      case '1':
        priority = 'critical';
        break;
      case '2':
        priority = 'high';
        break;
      case '3':
        priority = 'medium';
        break;
      case '4':
        priority = 'low';
        break;
    }

    if (priority) {
      labels.push(priority);
    }
  }

  // Description
  console.log('\nDescription (press Enter twice when done):');
  const descriptionLines = [];
  while (true) {
    const line = await question('');
    if (!line && descriptionLines.length > 0 && !descriptionLines[descriptionLines.length - 1]) {
      descriptionLines.pop(); // Remove last empty line
      break;
    }
    descriptionLines.push(line);
  }
  const description = descriptionLines.join('\n').trim();

  if (!description) {
    console.error('❌ Description is required');
    rl.close();
    process.exit(1);
  }

  // Additional labels
  const additionalLabels = await question('\nAdditional labels (comma-separated, or press Enter to skip): ');
  if (additionalLabels.trim()) {
    additionalLabels.split(',').forEach(label => {
      const trimmed = label.trim();
      if (trimmed) {
        labels.push(trimmed);
      }
    });
  }

  // Assignee
  const assignee = await question('\nAssign to (@username or press Enter to skip): ');

  // Confirm
  console.log('\n╔═══════════════════════════════════════════════════════════╗');
  console.log('║  Issue Preview                                            ║');
  console.log('╚═══════════════════════════════════════════════════════════╝');
  console.log(`\nTitle: ${title}`);
  console.log(`Type: ${issueType}`);
  console.log(`Labels: ${labels.join(', ')}`);
  if (assignee.trim()) {
    console.log(`Assignee: ${assignee}`);
  }
  console.log(`\nDescription:\n${description}\n`);

  const confirm = await question('Create this issue? (y/n): ');
  if (confirm.toLowerCase() !== 'y') {
    console.log('❌ Cancelled');
    rl.close();
    process.exit(0);
  }

  // Create issue
  console.log('\n📤 Creating issue...');

  const labelFlags = labels.map(l => `--label "${l}"`).join(' ');
  const assigneeFlag = assignee.trim() ? `--assignee "${assignee.trim()}"` : '';

  const command = `gh issue create --repo ${REPO} --title "${title.replace(/"/g, '\\"')}" --body "${description.replace(/"/g, '\\"')}" ${labelFlags} ${assigneeFlag}`;

  const result = runCommand(command);

  if (result.success) {
    console.log('\n✅ Issue created successfully!');
    console.log(result.output);

    // Extract issue number
    const urlMatch = result.output.match(/\/issues\/(\d+)/);
    if (urlMatch) {
      const issueNumber = urlMatch[1];
      console.log(`\n🔗 Issue #${issueNumber}`);
      console.log(`   View: https://github.com/${REPO}/issues/${issueNumber}`);
    }
  } else {
    console.error('\n❌ Failed to create issue');
    console.error(result.error);
    rl.close();
    process.exit(1);
  }

  rl.close();
}

main().catch(error => {
  console.error('Fatal error:', error);
  rl.close();
  process.exit(1);
});
