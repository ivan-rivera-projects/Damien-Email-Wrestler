#!/usr/bin/env node
/**
 * Damien MCP Server - Claude Local Integration Helper
 * 
 * This script provides instructions on how to integrate your local
 * Damien Smithery adapter with Claude for testing purposes.
 */

import fs from 'fs';
import chalk from 'chalk';
import { CONFIG } from './src/config.js';
import fetch from 'node-fetch';

// Constants
const TOOLS_CONFIG_PATH = './claude_tools_config.json';
const LOCAL_SERVER_URL = `http://localhost:${CONFIG.SERVER_PORT}`;

/**
 * Check if the adapter server is running
 */
async function checkServerStatus() {
  try {
    const response = await fetch(`${LOCAL_SERVER_URL}/health`);
    
    if (response.ok) {
      const data = await response.json();
      return { running: true, data };
    }
    
    return { running: false, error: `Server returned status: ${response.status}` };
  } catch (error) {
    return { running: false, error: error.message };
  }
}

/**
 * Check if the tools configuration file exists
 */
function checkToolsConfig() {
  try {
    if (fs.existsSync(TOOLS_CONFIG_PATH)) {
      return { exists: true };
    }
    return { exists: false, error: `Tools configuration file not found at: ${TOOLS_CONFIG_PATH}` };
  } catch (error) {
    return { exists: false, error: error.message };
  }
}

/**
 * Main function
 */
async function main() {
  console.log(chalk.blue('\n==============================================='));
  console.log(chalk.blue('  DAMIEN SMITHERY ADAPTER - CLAUDE INTEGRATION'));
  console.log(chalk.blue('===============================================\n'));
  
  // Check server status
  console.log(chalk.yellow('Step 1: Checking if Damien Smithery Adapter is running...'));
  const serverStatus = await checkServerStatus();
  
  if (!serverStatus.running) {
    console.log(chalk.red(`❌ The adapter server is not running. Error: ${serverStatus.error}`));
    console.log(chalk.yellow('\nPlease start the server in another terminal with:'));
    console.log(chalk.white('  npm start'));
    process.exit(1);
  }
  
  console.log(chalk.green('✅ The adapter server is running!'));
  
  // Check tools configuration
  console.log(chalk.yellow('\nStep 2: Checking if Claude tools configuration exists...'));
  const configStatus = checkToolsConfig();
  
  if (!configStatus.exists) {
    console.log(chalk.red(`❌ ${configStatus.error}`));
    process.exit(1);
  }
  
  console.log(chalk.green('✅ Claude tools configuration found!'));
  
  // Display integration instructions
  console.log(chalk.yellow('\nStep 3: Follow these steps to integrate with Claude:'));
  console.log(chalk.white('\n1. Go to Claude in your web browser'));
  console.log(chalk.white('2. Click on the Tools icon in the bottom-left corner'));
  console.log(chalk.white('3. Click "Add new tool"'));
  console.log(chalk.white('4. Select "Upload a File" and choose the following file:'));
  console.log(chalk.cyan(`   ${TOOLS_CONFIG_PATH}`));
  console.log(chalk.white('5. Click "Add" to add the tools to Claude'));
  console.log(chalk.white('6. Claude should now have access to the Damien email management tools'));
  
  console.log(chalk.yellow('\nStep 4: Test the integration with some prompts:'));
  console.log(chalk.white('\nExample prompts to try:'));
  console.log(chalk.cyan(' - "List my unread emails"'));
  console.log(chalk.cyan(' - "Show me details of this email: [ID from the list]"'));
  console.log(chalk.cyan(' - "Mark these emails as read: [IDs from the list]"'));
  console.log(chalk.cyan(' - "Add a label called TEST to this email: [ID]"'));
  console.log(chalk.cyan(' - "List all my email filtering rules"'));
  console.log(chalk.cyan(' - "Move this email to trash: [ID]"'));
  
  console.log(chalk.yellow('\nImportant Notes:'));
  console.log(chalk.white('• Keep both the Damien MCP Server and Smithery Adapter running'));
  console.log(chalk.white('• Each Claude conversation uses a unique session ID'));
  console.log(chalk.white('• Tool execution is logged in the adapter console'));
  
  console.log(chalk.blue('\n==============================================='));
  console.log(chalk.green('Ready for Claude integration testing!'));
  console.log(chalk.blue('===============================================\n'));
}

// Run the script
main().catch(error => {
  console.error(chalk.red('Error:'), error);
  process.exit(1);
});
