import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from ..llm_providers.base import BaseLLMProvider
from ..models import ConversationContext
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
Analyze this email-related query and determine the intent.

Query: "{query}"

Previous context:
{self._format_context(context, last_n=3)}

Determine:
1. Intent type: search, summarize, action, or question
2. Email criteria (if searching)
3. Action to perform (if action)
4. Time range (if applicable)

Respond in JSON:
{{
    "intent_type": "search|summarize|action|question",
    "criteria": {{
        "from": "sender if specified",
        "to": "recipient if specified", 
        "subject": "subject keywords",
        "body": "body keywords",
        "time_range": "today|this_week|last_week|custom",
        "has_attachment": true/false,
        "is_unread": true/false,
        "labels": ["label1", "label2"]
    }},
    "action": "archive|trash|label|mark_read|forward|reply",
    "action_params": {{}},
    "limit": 10
}}

Examples:
- "Show me unread emails from John" -> intent_type: "search", criteria: {{from: "John", is_unread: true}}
- "Summarize emails from today" -> intent_type: "summarize", criteria: {{time_range: "today"}}
- "Archive all newsletters" -> intent_type: "action", action: "archive", criteria: {{subject: "newsletter"}}
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
        
        # Build Gmail query from criteria
        gmail_query = self._build_gmail_query(intent.get("criteria", {}))
        
        # Search emails
        service = self._get_gmail_service()
        results = gmail_api_service.list_messages(
            gmail_service=service,
            query=gmail_query,
            max_results=intent.get("limit", 10)
        )
        
        emails = results.get("messages", [])
        
        if not emails:
            return {
                "response": "I couldn't find any emails matching your criteria.",
                "success": True,
                "emails": []
            }
        
        # Format response
        response_text = f"I found {len(emails)} email(s) matching your search:\n\n"
        
        email_refs = []
        for i, email in enumerate(emails[:5], 1):  # Show first 5
            response_text += f"{i}. From: {email['from_sender']}\n"
            response_text += f"   Subject: {email['subject']}\n"
            response_text += f"   Date: {email['date']}\n"
            response_text += f"   Preview: {email['snippet'][:100]}...\n\n"
            email_refs.append(email['id'])
        
        if len(emails) > 5:
            response_text += f"... and {len(emails) - 5} more email(s).\n"
        
        response_text += "\nWhat would you like to do with these emails?"
        
        return {
            "response": response_text,
            "success": True,
            "emails": emails,
            "email_refs": email_refs
        }
    
    async def _execute_summarize(self, intent: Dict, context: ConversationContext) -> Dict:
        """Summarize emails based on criteria"""
        
        # First search for emails
        search_result = await self._execute_search(intent, context)
        
        if not search_result["emails"]:
            return search_result
        
        # Get email details for summarization
        emails = search_result["emails"][:10]  # Limit to 10 for API costs
        
        email_contents = []
        for email in emails:
            details = gmail_api_service.get_message_details(
                gmail_service=self._get_gmail_service(),
                message_id=email['id'],
                format_option='metadata'
            )
            email_contents.append({
                "from": email['from_sender'],
                "subject": email['subject'],
                "snippet": email['snippet'],
                "date": email['date']
            })
        
        # Generate summary
        summary_prompt = f"""
Summarize these emails concisely:

{json.dumps(email_contents, indent=2)}

Provide:
1. Overall summary (2-3 sentences)
2. Key themes or topics
3. Any urgent items
4. Suggested actions
"""
        
        summary = await self.llm.complete(summary_prompt, temperature=0.3)
        
        return {
            "response": f"Summary of {len(emails)} email(s):\n\n{summary}",
            "success": True,
            "emails": emails,
            "email_refs": [e['id'] for e in emails]
        }
    
    async def _execute_action(self, intent: Dict, context: ConversationContext) -> Dict:
        """Execute an action on emails"""
        
        action = intent.get("action")
        criteria = intent.get("criteria", {})
        
        # First find the emails
        search_intent = {"criteria": criteria, "limit": 1000}  # Higher limit for actions
        search_result = await self._execute_search(search_intent, context)
        
        if not search_result["emails"]:
            return {
                "response": "I couldn't find any emails to perform that action on.",
                "success": False
            }
        
        email_ids = [e['id'] for e in search_result["emails"]]
        
        # Confirm action
        response = f"I found {len(email_ids)} email(s) to {action}. "
        
        # For destructive actions, list some examples
        if action in ["trash", "archive"] and len(email_ids) > 3:
            response += "Here are a few examples:\n"
            for email in search_result["emails"][:3]:
                response += f"- {email['subject']} (from {email['from_sender']})\n"
            response += f"... and {len(email_ids) - 3} more.\n\n"
        
        response += f"This action will be simulated (dry-run). In production, you would confirm before executing."
        
        # Simulate the action (in production, this would actually execute)
        action_result = {
            "action": action,
            "email_count": len(email_ids),
            "email_ids": email_ids[:10],  # First 10 for reference
            "dry_run": True
        }
        
        return {
            "response": response,
            "success": True,
            "action_result": action_result,
            "email_refs": email_ids
        }
    
    async def _execute_question(self, intent: Dict, context: ConversationContext) -> Dict:
        """Answer questions about emails or the system"""
        
        # This would handle questions like:
        # - "How many emails do I have from Amazon?"
        # - "What's my most frequent sender?"
        # - "When was the last email from John?"
        
        # For now, return a placeholder
        return {
            "response": "I can help you search, summarize, and manage your emails. Try asking me to find specific emails or summarize your inbox!",
            "success": True
        }
    
    def _build_gmail_query(self, criteria: Dict) -> str:
        """Convert criteria dict to Gmail query string"""
        
        query_parts = []
        
        if criteria.get("from"):
            query_parts.append(f'from:{criteria["from"]}')
        
        if criteria.get("to"):
            query_parts.append(f'to:{criteria["to"]}')
            
        if criteria.get("subject"):
            query_parts.append(f'subject:{criteria["subject"]}')
            
        if criteria.get("body"):
            query_parts.append(f'{criteria["body"]}')
            
        if criteria.get("is_unread"):
            query_parts.append("is:unread")
            
        if criteria.get("has_attachment"):
            query_parts.append("has:attachment")
            
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
        
        return " ".join(query_parts)
    
    def _format_context(self, context: ConversationContext, last_n: int = 5) -> str:
        """Format conversation context for prompt"""
        
        if not context.messages:
            return "No previous messages."
        
        formatted = []
        for msg in context.messages[-last_n:]:
            role = msg["role"].capitalize()
            content = msg["content"]
            if len(content) > 200:
                content = content[:200] + "..."
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)
    
    def _get_gmail_service(self):
        """Get Gmail service"""
        from damien_cli.core_api.gmail_api_service import get_authenticated_service
        return get_authenticated_service()