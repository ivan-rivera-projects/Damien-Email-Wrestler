import { startServer } from './basicServer.js';

console.error('Damien Smithery MCP Server starting...');

startServer().catch(error => {
  console.error('Failed to start server:', error);
  process.exit(1);
});