import { DamienApiClient } from './damienApiClient.js';

// Define our own ToolDefinition interface
export interface ToolDefinition {
  name: string;
  description: string;
  inputSchema: any;
  outputSchema?: any;
}

interface DamienToolSchema {
  name: string;
  description: string;
  input_schema: any;
  output_schema?: any;
}

/**
 * Fetches tool definitions from Damien MCP Server and converts them to MCP SDK tool definitions
 */
export async function getDamienToolDefinitions(): Promise<ToolDefinition[]> {
  const client = new DamienApiClient();
  try {
    const damienTools = await client.listTools();
    
    if (!Array.isArray(damienTools)) {
      console.error("Failed to fetch or parse tool definitions from Damien MCP Server. Expected an array.", damienTools);
      throw new Error("Could not retrieve tool definitions from Damien MCP Server.");
    }
    
    return damienTools.map((tool: DamienToolSchema) => {
      if (!tool.name || !tool.description || !tool.input_schema) {
        console.warn("Skipping tool with missing essential fields:", tool);
        return null;
      }
      
      return {
        name: tool.name,
        description: tool.description,
        inputSchema: tool.input_schema
      };
    }).filter(tool => tool !== null) as ToolDefinition[];
  } catch (error) {
    console.error('Error fetching tool definitions from Damien MCP Server:', error);
    console.warn('Falling back to static tool definitions');
    return staticToolDefinitions;
  }
}

/**
 * Static tool definitions in case the Damien MCP Server is unavailable
 */
export const staticToolDefinitions: ToolDefinition[] = [
  {
    name: "damien_list_emails",
    description: "Lists email messages based on a query, with support for pagination. Provides summaries including ID, thread ID, subject, sender, snippet, date, attachment status, and labels.",
    inputSchema: {
      type: "object",
      properties: {
        query: {
          type: "string",
          description: "Optional Gmail search query string to filter emails (e.g., 'is:unread from:boss@example.com', 'subject:report older_than:7d'). If omitted, lists recent emails."
        },
        max_results: {
          type: "integer",
          description: "Optional. Maximum number of email summaries to return in this call. Default is 10. Must be > 0 and <= 100.",
          default: 10
        },
        page_token: {
          type: "string",
          description: "Optional. An opaque token received from a previous 'damien_list_emails' call to fetch the next page of results."
        }
      }
    }
  },
  {
    name: "damien_get_email_details",
    description: "Retrieves the full details of a specific email message, including headers, payload (body, parts), and raw content based on the specified format.",
    inputSchema: {
      type: "object",
      properties: {
        message_id: {
          type: "string",
          description: "The unique immutable ID of the email message to retrieve."
        },
        format: {
          type: "string",
          description: "Specifies the level of detail for the email. 'full' returns complete data including payload. 'metadata' returns headers and snippet. 'raw' returns the full email as a raw, RFC 2822 formatted string (base64url encoded).",
          default: "full"
        }
      },
      required: ["message_id"]
    }
  }
];