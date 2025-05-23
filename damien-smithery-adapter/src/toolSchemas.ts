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
          description: "Optional Gmail search query string to filter emails (e.g., 'is:unread from:boss@example.com', 'subject:report older_than:7d'). If omitted, lists recent emails. See Gmail search operators: https://support.google.com/mail/answer/7190"
        },
        max_results: {
          type: "integer",
          description: "Optional. Maximum number of email summaries to return in this call. Default is 100. Must be > 0 and <= 100.",
          default: 100
        },
        page_token: {
          type: "string",
          description: "Optional. An opaque token received from a previous 'damien_list_emails' call to fetch the next page of results."
        },
        include_headers: {
          type: "array",
          items: {
            type: "string"
          },
          description: "Optional list of header names (e.g., 'From', 'Subject', 'Date', 'To', 'Cc', 'Reply-To', 'Message-ID') to include in each email summary. Requesting specific headers is more efficient than fetching full details later. If omitted, basic summaries (ID, threadId, and potentially a snippet) are returned. Consult EmailSummary model for fields populated by common headers."
        }
      },
      // No required fields for list_emails, all are optional
    }
  },
  {
    name: "damien_get_email_details",
    description: "Retrieves details of a specific email message. Can fetch specific headers for efficiency.",
    inputSchema: {
      type: "object",
      properties: {
        message_id: {
          type: "string",
          description: "The unique immutable ID of the email message to retrieve."
        },
        format: {
          type: "string",
          description: "Specifies the level of detail. 'full' (all data), 'metadata' (headers & snippet), 'raw' (RFC 2822). Default is 'metadata'. If 'include_headers' is used, format is effectively 'metadata'.",
          default: "metadata"
        },
        include_headers: {
          type: "array",
          items: {
            type: "string"
          },
          description: "Optional. If 'format' is 'metadata' (or if this field is provided), this specifies a list of header names to retrieve (e.g., 'From', 'Subject'). Fetches only these headers. More efficient if only specific headers are needed. Common headers: 'From', 'To', 'Cc', 'Bcc', 'Subject', 'Date', 'Reply-To', 'Message-ID'."
        }
      },
      required: ["message_id"]
    }
  },
  // Adding static definition for damien_apply_rules
  {
    name: "damien_apply_rules",
    description: "Applies filtering rules to emails in your Gmail account based on various criteria. Can be run in dry-run mode. Returns a detailed summary of actions taken or that would be taken.",
    inputSchema: {
      type: "object",
      properties: {
        gmail_query_filter: {
          type: "string",
          description: "Optional. Base Gmail query string to narrow down messages for rule application. See Gmail search operators: https://support.google.com/mail/answer/7190"
        },
        rule_ids_to_apply: {
          type: "array",
          items: { type: "string" },
          description: "Optional. A list of specific rule IDs to apply. If omitted, all enabled rules are considered."
        },
        dry_run: {
          type: "boolean",
          default: false,
          description: "If True, simulates rule application and returns a summary of actions that would be taken, without making actual changes."
        },
        scan_limit: {
          type: "integer",
          description: "Optional. Limits the number of messages scanned from the Gmail query results for rule application."
        },
        date_after: {
          type: "string",
          description: "Optional. Apply rules only to emails received after this date. Format: YYYY/MM/DD."
        },
        date_before: {
          type: "string",
          description: "Optional. Apply rules only to emails received before this date. Format: YYYY/MM/DD."
        },
        all_mail: {
          type: "boolean",
          default: false,
          description: "Optional. If True, ignores all other query filters and attempts to apply rules to all mail. Use with caution."
        },
        include_detailed_ids: {
          type: "boolean",
          default: false,
          description: "Optional. If True, the 'actions_planned_or_taken' in the summary will include lists of affected email IDs. Otherwise (default False), it will contain counts. Set to True if you need to know exactly which emails were affected by each action."
        }
      }
      // No specific required fields, all are optional with defaults or handled by server logic
    }
    // outputSchema could also be defined here if needed for the static fallback
  },
  {
    name: "damien_list_rules",
    description: "Lists filtering rules in Damien. Can return summaries or full definitions.",
    inputSchema: {
      type: "object",
      properties: {
        summary_view: {
          type: "boolean",
          default: true,
          description: "If True (default), returns a summary of each rule (ID, name, description, enabled status). If False, returns the full definition of each rule."
        }
      }
    }
    // Output schema varies, client should ideally get this from dynamic endpoint
  },
  {
    name: "damien_get_rule_details",
    description: "Retrieves the full definition of a specific filtering rule by its ID or name.",
    inputSchema: {
      type: "object",
      properties: {
        rule_id_or_name: {
          type: "string",
          description: "The unique ID or exact name of the rule to retrieve."
        }
      },
      required: ["rule_id_or_name"]
    }
    // Output schema is complex (full RuleModelOutput), client should ideally get from dynamic endpoint
  }
  // ... other static tool definitions would go here
];