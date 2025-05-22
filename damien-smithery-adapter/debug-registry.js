// Simple script to debug the Smithery Registry API
const { SmitheryRegistry } = require("@smithery/registry");

// Make sure you have SMITHERY_BEARER_AUTH in your environment variables
const smitheryRegistry = new SmitheryRegistry({
  bearerAuth: process.env.SMITHERY_BEARER_AUTH || "your-token-here"
});

// Log the available methods
console.log("SmitheryRegistry instance:", Object.keys(smitheryRegistry));
console.log("SmitheryRegistry.servers:", Object.keys(smitheryRegistry.servers));

// Log the complete prototype chain
function logPrototypeChain(obj, name) {
  let proto = Object.getPrototypeOf(obj);
  let level = 0;
  
  while (proto) {
    console.log(`${name} prototype level ${level}:`, Object.getOwnPropertyNames(proto));
    proto = Object.getPrototypeOf(proto);
    level++;
  }
}

logPrototypeChain(smitheryRegistry.servers, "servers");

console.log("Try to see class definition:");
console.log(smitheryRegistry.servers.constructor.toString().substring(0, 500));
