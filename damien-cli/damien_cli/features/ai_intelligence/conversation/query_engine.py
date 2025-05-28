import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from ..llm_providers.base import BaseLLMProvider
from ..models import ConversationContext
from .context_manager import ConversationContextManager
from damien_cli.core_api import gmail_api_service

class ConversationalQueryEngine:
    """Processes natural language queries about emails"""
    
    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider
        self.context_manager = ConversationContextManager()
        
    async def process_query(self, 
                          query: str, 
                          session_id: str,
                          context: Optional[ConversationContext] = None) -> Dict:
        """Process a natural language query"""
        
        # Load or create context
        if not context:
            context = self.context_manager.get_or_create_context(session_id)
        
        # Add query to context
        context.messages.append({"role": "user", "content": query})
        
        # Determine query intent
        intent = await self._analyze_query_intent(query, context)
        
        # Execute based on intent
        result = await self._execute_intent(intent, context)
        
        # Update context with result
        context.messages.append({"role": "assistant", "content": result["response"]})
        if "email_refs" in result:
            context.email_refs.extend(result["email_refs"])
        
        # Save context
        self.context_manager.save_context(context)
        
        return result
    
    async def _analyze_query_intent(self, query: str, context: ConversationContext) -> Dict:
        """Analyze what the user is asking for"""
        
        prompt = f"""
You are an AI assistant for the Damien Email Wrestler CLI. Your task is to understand user queries about their emails and translate them into structured intents for the system to process.

Analyze the following user query, taking into account the previous conversation history for context.

User Query: "{query}"

Conversation History:
{self._format_context(context, last_n=5)}

Based on the query and history, determine the user's intent and extract any relevant parameters.

Intent Types:
- search: The user wants to find or list emails based on criteria.
- summarize: The user wants a summary of emails matching certain criteria.
- action: The user wants to perform an action on emails (e.g., archive, trash, label).
- question: The user is asking a general question about their emails or the system (that doesn't fit the above).

Email Criteria (for search, summarize, action):
- from: Sender email address or name (e.g., "john@example.com", "John Doe")
- to: Recipient email address or name
- subject: Keywords or phrases in the subject line
- body: Keywords or phrases in the email body
- time_range: Relative time frame (e.g., "today", "this_week", "last_month", "past 7 days")
- has_attachment: Whether the email has attachments (true/false)
- is_unread: Whether the email is unread (true/false)
- is_starred: Whether the email is starred (true/false)
- labels: Specific Gmail labels (e.g., "INBOX", "SPAM", "IMPORTANT", user-defined labels)

Actions (for action intent):
- archive: Move emails to archive.
- trash: Move emails to trash.
- label: Apply a specific label. Requires 'label_name' parameter.
- remove_label: Remove a specific label. Requires 'label_name' parameter.
- mark_read: Mark emails as read.
- mark_unread: Mark emails as unread.
- forward: Forward emails. Requires 'forward_to' parameter (email address).
- reply: Indicate intent to reply (requires identifying specific email(s)).

Parameters (for actions):
- label_name: The name of the label (for 'label' or 'remove_label' actions).
- forward_to: The email address to forward to (for 'forward' action).

Output Format:
Respond with a JSON object containing the following keys:
{{
    "intent_type": "search" | "summarize" | "action" | "question",
    "criteria": {{
        "from": "string | null",
        "to": "string | null",
        "subject": "string | null",
        "body": "string | null",
        "time_range": "string | null",
        "has_attachment": "boolean | null",
        "is_unread": "boolean | null",
        "is_starred": "boolean | null",
        "labels": "List[string] | null"
    }},
    "action": "archive" | "trash" | "label" | "remove_label" | "mark_read" | "mark_unread" | "forward" | "reply" | null,
    "action_params": {{
        "label_name": "string | null",
        "forward_to": "string | null"
    }} | null,
    "limit": "integer | null" # Maximum number of emails to consider (default 10 for search/summarize, higher for actions)
}}

Examples:
- "Find all unread emails from 'newsletter@example.com' from last week."
  -> {{ "intent_type": "search", "criteria": {{ "from": "newsletter@example.com", "is_unread": true, "time_range": "last_week" }}, "action": null, "action_params": null, "limit": 10 }}
- "Summarize the emails from today about 'project update'."
  -> {{ "intent_type": "summarize", "criteria": {{ "time_range": "today", "subject": "project update" }}, "action": null, "action_params": null, "limit": 10 }}
- "Archive all emails from 'spam@bad.com'."
  -> {{ "intent_type": "action", "criteria": {{ "from": "spam@bad.com" }}, "action": "archive", "action_params": null, "limit": 1000 }}
- "Label the last email from John as 'Important'."
  -> {{ "intent_type": "action", "criteria": {{ "from": "John", "time_range": "latest" }}, "action": "label", "action_params": {{ "label_name": "Important" }}, "limit": 1 }}
- "How many emails did I get yesterday?"
  -> {{ "intent_type": "question", "criteria": {{ "time_range": "yesterday" }}, "action": null, "action_params": null, "limit": null }}
- "What can you do?"
  -> {{ "intent_type": "question", "criteria": {{}}, "action": null, "action_params": null, "limit": null }}
"""
        
        response = await self.llm.complete(prompt, temperature=0.2)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback to simple search
            return {
                "intent_type": "search",
                "criteria": {"body": query},
                "limit": 10
            }
    
    async def _execute_intent(self, intent: Dict, context: ConversationContext) -> Dict:
        """Execute the analyzed intent"""
        
        intent_type = intent.get("intent_type", "search")
        
        if intent_type == "search":
            return await self._execute_search(intent, context)
        elif intent_type == "summarize":
            return await self._execute_summarize(intent, context)
        elif intent_type == "action":
            return await self._execute_action(intent, context)
        elif intent_type == "question":
            return await self._execute_question(intent, context)
        else:
            return {
                "response": "I'm not sure how to help with that. Could you rephrase your request?",
                "success": False
            }
    
    async def _execute_search(self, intent: Dict, context: ConversationContext) -> Dict:
        """Execute email search based on intent"""

        criteria = intent.get("criteria", {})
        limit = intent.get("limit", 10)

        # Build Gmail query from criteria
        gmail_query = self._build_gmail_query(criteria)

        # Search emails using Gmail API
        service = self._get_gmail_service()
        try:
            results = gmail_api_service.list_messages(
                gmail_service=service,
                query_string=gmail_query,
                max_results=limit
            )
            emails = results.get("messages", [])
        except Exception as e:
            return {
                "response": f"An error occurred while searching for emails: {str(e)}",
                "success": False,
                "emails": []
            }


        if not emails:
            return {
                "response": "I couldn't find any emails matching your criteria.",
                "success": True,
                "emails": []
            }

        # Format response with key details
        response_text = f"I found {len(emails)} email(s) matching your search:\n\n"

        email_refs = []
        for i, email in enumerate(emails[:min(5, len(emails))]):  # Show up to 5 examples
            response_text += f"{i+1}. From: {email.get('from_sender', 'N/A')}\n"
            response_text += f"   Subject: {email.get('subject', 'N/A')}\n"
            response_text += f"   Date: {email.get('date', 'N/A')}\n"
            response_text += f"   Preview: {email.get('snippet', 'No snippet available')[:100]}...\n\n"
            email_refs.append(email['id'])

        if len(emails) > 5:
            response_text += f"... and {len(emails) - 5} more email(s).\n"

        response_text += "\nWhat would you like to do with these emails?"

        return {
            "response": response_text,
            "success": True,
            "emails": emails,
            "email_refs": email_refs # Store email IDs for potential follow-up actions
        }

    async def _execute_summarize(self, intent: Dict, context: ConversationContext) -> Dict:
        """Summarize emails based on criteria"""

        # First search for emails based on intent or context
        criteria = intent.get("criteria", {})
        email_ids_from_context = context.email_refs # Use emails from previous turn if available

        if email_ids_from_context and not criteria:
             # Summarize emails from the previous turn if no new criteria
             emails_to_summarize = []
             service = self._get_gmail_service()
             for email_id in email_ids_from_context[:10]: # Limit to 10 for summarization
                 try:
                     details = gmail_api_service.get_message_details(
                         gmail_service=service,
                         message_id=email_id,
                         format_option='full' # Get full content for better summary
                     )
                     emails_to_summarize.append(details)
                 except Exception as e:
                     print(f"Error fetching email details for summarization: {e}") # Log error
                     pass # Skip if fetching fails
        else:
            # Perform a new search if new criteria are provided or no context emails
            search_intent = {"criteria": criteria, "limit": 10} # Limit search for summarization
            search_result = await self._execute_search(search_intent, context)
            emails_to_summarize = search_result.get("emails", [])
            # Fetch full details for summarization
            service = self._get_gmail_service()
            detailed_emails = []
            for email in emails_to_summarize:
                 try:
                     details = gmail_api_service.get_message_details(
                         gmail_service=service,
                         message_id=email['id'],
                         format_option='full'
                     )
                     detailed_emails.append(details)
                 except Exception as e:
                     print(f"Error fetching email details for summarization: {e}") # Log error
                     pass # Skip if fetching fails
            emails_to_summarize = detailed_emails


        if not emails_to_summarize:
            return {
                "response": "I couldn't find any emails to summarize.",
                "success": True,
                "emails": []
            }

        # Prepare text for summarization prompt
        email_texts = []
        for email in emails_to_summarize:
             body = email.get('body', 'No body content.')
             # Simple text extraction, could be improved for HTML emails
             import re
             text_content = re.sub(r'<.*?>', '', body) # Remove HTML tags
             email_texts.append(f"Subject: {email.get('subject', 'N/A')}\nFrom: {email.get('from_sender', 'N/A')}\nDate: {email.get('date', 'N/A')}\n\n{text_content[:500]}...") # Limit body content


        # Generate summary using LLM
        summary_prompt_lines = [
            "Summarize the following emails concisely. Provide an overall summary, key themes, any urgent items, and suggested actions.",
            "",
            "Emails:",
            '-' * 20,
            "\n".join(email_texts),
            '-' * 20,
            "",
            "Summary format:",
            "Overall Summary: ...",
            "Key Themes: ...",
            "Urgent Items: ...",
            "Suggested Actions: ..."
        ]
        summary_prompt = "\n".join(summary_prompt_lines)
        
        try:
            summary = await self.llm.complete(summary_prompt, temperature=0.3, max_tokens=500) # Limit summary length
            response_text = f"Summary of {len(emails_to_summarize)} email(s):\n\n{summary}"
            success = True
        except Exception as e:
            response_text = f"An error occurred while generating the summary: {str(e)}"
            success = False
            summary = None # Ensure summary is None on failure


        return {
            "response": response_text,
            "success": success,
            "emails": emails_to_summarize, # Return detailed emails
            "email_refs": [e['id'] for e in emails_to_summarize] if success else []
        }


    async def _execute_action(self, intent: Dict, context: ConversationContext) -> Dict:
        """Execute an action on emails"""

        action = intent.get("action")
        criteria = intent.get("criteria", {})
        action_params = intent.get("action_params", {})

        # Determine which emails to act on: from criteria or from context
        email_ids_to_act_on = []
        if criteria:
            # Find emails based on criteria
            search_intent = {"criteria": criteria, "limit": 1000} # Higher limit for actions
            search_result = await self._execute_search(search_intent, context)
            email_ids_to_act_on = [e['id'] for e in search_result.get("emails", [])]
            if not email_ids_to_act_on:
                 return {
                     "response": "I couldn't find any emails matching your criteria to perform that action on.",
                     "success": False
                 }
        elif context.email_refs:
            # Use emails from the previous turn if no new criteria
            email_ids_to_act_on = context.email_refs[:100] # Limit action to recent context emails
            if not email_ids_to_act_on:
                 return {
                     "response": "No emails referenced in the previous conversation to perform that action on.",
                     "success": False
                 }
        else:
             return {
                 "response": "Please specify which emails you'd like to perform this action on.",
                 "success": False
             }


        if not email_ids_to_act_on:
             return {
                 "response": "No emails found to perform the action.",
                 "success": False
             }

        # Confirm action with the user (in a real interactive CLI)
        # For this implementation, we will proceed directly but log the action
        import click # Assuming click is available in this context or passed in

        response_text = f"Attempting to perform '{action}' on {len(email_ids_to_act_on)} email(s)."

        # Perform the action using Gmail API
        service = self._get_gmail_service()
        try:
            if action == "archive":
                gmail_api_service.batch_modify_messages(
                    gmail_service=service,
                    message_ids=email_ids_to_act_on,
                    remove_label_ids=['INBOX'] # Archive by removing INBOX label
                )
                response_text += "\n✅ Emails archived."
                success = True
            elif action == "trash":
                 gmail_api_service.batch_modify_messages(
                     gmail_service=service,
                     message_ids=email_ids_to_act_on,
                     add_label_ids=['TRASH'] # Move to trash
                 )
                 response_text += "\n✅ Emails moved to trash."
                 success = True
            elif action == "mark_read":
                 gmail_api_service.batch_modify_messages(
                     gmail_service=service,
                     message_ids=email_ids_to_act_on,
                     remove_label_ids=['UNREAD'] # Mark as read
                 )
                 response_text += "\n✅ Emails marked as read."
                 success = True
            elif action == "mark_unread":
                 gmail_api_service.batch_modify_messages(
                     gmail_service=service,
                     message_ids=email_ids_to_act_on,
                     add_label_ids=['UNREAD'] # Mark as unread
                 )
                 response_text += "\n✅ Emails marked as unread."
                 success = True
            elif action == "label" and action_params.get("label_name"):
                 label_name = action_params["label_name"]
                 # Need to get label ID from name - requires another API call or caching labels
                 # For simplicity, assuming label_name can be used directly or is a known ID
                 # In a real app, you'd fetch label ID: service.users().labels().list(...).execute()
                 # For now, a placeholder or direct use if API supports name
                 # Assuming label_name is the actual label ID for this example
                 try:
                     # Attempt to get label ID by name (requires fetching all labels)
                     labels_response = service.users().labels().list(userId='me').execute()
                     labels = labels_response.get('labels', [])
                     label_id = None
                     for label in labels:
                         if label['name'].lower() == label_name.lower():
                             label_id = label['id']
                             break

                     if label_id:
                         gmail_api_service.batch_modify_messages(
                             gmail_service=service,
                             message_ids=email_ids_to_act_on,
                             add_label_ids=[label_id]
                         )
                         response_text += f"\n✅ Label '{label_name}' applied to emails."
                         success = True
                     else:
                         response_text += f"\n❌ Error: Label '{label_name}' not found."
                         success = False
                 except Exception as e:
                     response_text += f"\n❌ Error applying label: {str(e)}"
                     success = False

            elif action == "remove_label" and action_params.get("label_name"):
                 label_name = action_params["label_name"]
                 try:
                     # Attempt to get label ID by name
                     labels_response = service.users().labels().list(userId='me').execute()
                     labels = labels_response.get('labels', [])
                     label_id = None
                     for label in labels:
                         if label['name'].lower() == label_name.lower():
                             label_id = label['id']
                             break

                     if label_id:
                         gmail_api_service.batch_modify_messages(
                             gmail_service=service,
                             message_ids=email_ids_to_act_on,
                             remove_label_ids=[label_id]
                         )
                         response_text += f"\n✅ Label '{label_name}' removed from emails."
                         success = True
                     else:
                         response_text += f"\n❌ Error: Label '{label_name}' not found."
                         success = False
                 except Exception as e:
                     response_text += f"\n❌ Error removing label: {str(e)}"
                     success = False

            elif action == "forward" and action_params.get("forward_to"):
                 forward_to_email = action_params["forward_to"]
                 # Forwarding requires fetching individual email content and sending a new email
                 # This is a more complex operation and will be a placeholder for now
                 response_text += f"\n➡️ Simulating forwarding {len(email_ids_to_act_on)} email(s) to {forward_to_email}."
                 response_text += "\nForwarding logic needs to be fully implemented."
                 success = True # Simulate success for now

            elif action == "reply":
                 # Replying requires fetching individual email content and composing a reply
                 # This is a more complex operation and will be a placeholder for now
                 response_text += f"\n↩️ Simulating replying to {len(email_ids_to_act_on)} email(s)."
                 response_text += "\nReplying logic needs to be fully implemented."
                 success = True # Simulate success for now

            else:
                response_text = f"Unsupported action: {action}"
                success = False

        except Exception as e:
            response_text = f"An error occurred while performing the action: {str(e)}"
            success = False

        return {
            "response": response_text,
            "success": success,
            "action_result": {
                "action": action,
                "email_count": len(email_ids_to_act_on),
                "email_ids": email_ids_to_act_on[:10], # First 10 for reference
                "status": "completed" if success else "failed"
            },
            "email_refs": email_ids_to_act_on if success else [] # Return email IDs if action was successful
        }


    async def _execute_question(self, intent: Dict, context: ConversationContext) -> Dict:
        """Answer questions about emails or the system"""

        query = context.messages[-1]["content"] # Get the latest user query
        criteria = intent.get("criteria", {})

        # Basic question answering based on criteria or context
        if criteria:
            # If criteria are provided, try to answer based on email count
            gmail_query = self._build_gmail_query(criteria)
            service = self._get_gmail_service()
            try:
                # Use list_messages with max_results=1 to check if any emails match
                results = gmail_api_service.list_messages(
                    gmail_service=service,
                    query_string=gmail_query,
                    max_results=1
                )
                count_estimate = results.get("result_size_estimate", 0) # Use estimate if available
                if count_estimate > 0:
                    response_text = f"Based on your criteria, it looks like you have around {count_estimate} matching email(s)."
                else:
                    response_text = "I couldn't find any emails matching your criteria."
                success = True
            except Exception as e:
                response_text = f"An error occurred while trying to count emails: {str(e)}"
                success = False

        elif "what can you do" in query.lower() or "help" in query.lower():
             response_text = "I can help you search, summarize, and perform actions like archiving, trashing, labeling, marking as read/unread, forwarding, and replying to your emails using natural language. Just tell me what you'd like to do!"
             success = True

        elif context.email_refs and ("what about these" in query.lower() or "tell me about them" in query.lower()):
             # If user asks about emails from previous turn
             return await self._execute_summarize({"criteria": {}}, context) # Summarize the context emails

        else:
            response_text = "I can help you with email-related questions, searches, summaries, and actions. What would you like to know or do?"
            success = True


        return {
            "response": response_text,
            "success": success,
            "emails": [], # No specific emails returned for general questions
            "email_refs": []
        }


    def _build_gmail_query(self, criteria: Dict) -> str:
        """Convert criteria dict to Gmail query string"""

        query_parts = []

        if criteria.get("from"):
            query_parts.append(f'from:{criteria["from"]}')

        if criteria.get("to"):
            query_parts.append(f'to:{criteria["to"]}')

        if criteria.get("subject"):
            # Use .format() instead of f-string to avoid potential backslash issues
            query_parts.append('subject:("{}")'.format(criteria["subject"])) # Quote subject for exact phrase matching

        if criteria.get("body"):
            # Use .format() instead of f-string
            query_parts.append('body:("{}")'.format(criteria["body"])) # Quote body for exact phrase matching

        if criteria.get("is_unread") is not None: # Check explicitly for None as value can be True/False
            if criteria["is_unread"]:
                query_parts.append("is:unread")
            else:
                query_parts.append("is:read")

        if criteria.get("is_starred") is not None:
             if criteria["is_starred"]:
                 query_parts.append("is:starred")
             else:
                 query_parts.append("-is:starred") # Exclude starred

        if criteria.get("has_attachment") is not None:
            if criteria["has_attachment"]:
                query_parts.append("has:attachment")
            else:
                query_parts.append("-has:attachment") # Exclude emails with attachments


        if criteria.get("labels"):
            for label in criteria["labels"]:
                query_parts.append(f'label:{label}')

        # Time range
        time_range = criteria.get("time_range")
        if time_range == "today":
            query_parts.append(f'after:{datetime.now().strftime("%Y/%m/%d")}')
        elif time_range == "this_week":
            week_ago = datetime.now() - timedelta(days=7)
            query_parts.append(f'after:{week_ago.strftime("%Y/%m/%d")}')
        elif time_range == "last_week":
            two_weeks = datetime.now() - timedelta(days=14)
            one_week = datetime.now() - timedelta(days=7)
            query_parts.append(f'after:{two_weeks.strftime("%Y/%m/%d")}')
            query_parts.append(f'before:{one_week.strftime("%Y/%m/%d")}')
        elif time_range == "last_month":
             month_ago = datetime.now() - timedelta(days=30)
             query_parts.append(f'after:{month_ago.strftime("%Y/%m/%d")}')
        elif time_range and "past" in time_range and "days" in time_range:
             try:
                 days = int(time_range.split(" ")[1])
                 past_date = datetime.now() - timedelta(days=days)
                 query_parts.append(f'after:{past_date.strftime("%Y/%m/%d")}')
             except ValueError:
                 pass # Ignore if days cannot be parsed
        elif time_range == "latest":
             # No specific time query needed, rely on limit and default Gmail sorting
             pass # Handled by limit in execute_search

        # Add support for custom date ranges if needed

        return " ".join(query_parts)

    def _format_context(self, context: ConversationContext, last_n: int = 5) -> str:
        """Format conversation context for prompt"""

        if not context.messages:
            return "No previous messages."

        formatted = []
        for msg in context.messages[-last_n:]:
            role = msg["role"].capitalize()
            content = msg["content"]
            # Truncate long messages for context
            if len(content) > 150: # Shorter truncation for context
                content = content[:150] + "..."
            formatted.append(f"{role}: {content}")

        return "\n".join(formatted)

    def _get_gmail_service(self):
        """Get Gmail service"""
        from damien_cli.core_api.gmail_api_service import get_authenticated_service
        return get_authenticated_service()