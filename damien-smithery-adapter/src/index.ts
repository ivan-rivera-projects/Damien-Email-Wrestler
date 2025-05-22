import { startServer } from './basicServer.js';

console.log('Damien Smithery Adapter starting...');

// Start the server
startServer().catch(error => {
  console.error('Failed to start server:', error);
  process.exit(1);
});