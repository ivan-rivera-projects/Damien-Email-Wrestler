#!/usr/bin/env node

/**
 * This is a workaround script for running the Damien Smithery Adapter
 * It avoids the TypeScript ESM import issues by running the compiled JavaScript
 */

// First build the project
import { execSync } from 'child_process';

console.log('Building the project...');
try {
  execSync('npm run build', { stdio: 'inherit' });
  console.log('Build successful!');
} catch (error) {
  console.error('Build failed:', error);
  process.exit(1);
}

console.log('Starting the server...');
try {
  // Run the compiled JavaScript with the --experimental-specifier-resolution=node flag
  execSync('node --experimental-specifier-resolution=node dist/index.js', { stdio: 'inherit' });
} catch (error) {
  console.error('Server execution failed:', error);
  process.exit(1);
}
