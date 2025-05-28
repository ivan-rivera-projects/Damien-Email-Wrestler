import click
import asyncio
from typing import Optional
from collections import defaultdict
from damien_cli.core.cli_utils import format_output
from damien_cli.features.rule_management.models import RuleModel
from .natural_language.rule_parser import NaturalLanguageRuleParser
from .llm_providers.openai_provider import OpenAIProvider
from .categorization.categorizer import EmailCategorizer
from .conversation.query_engine import ConversationalQueryEngine
from .conversation.context_manager import ConversationContextManager
import json

@click.group(name="ai")
def ai_group():
    """AI-powered email management commands"""
    pass

@ai_group.command(name="create-rule")
@click.argument("instruction", type=str)
@click.option("--dry-run", is_flag=True, help="Preview rule without saving")
@click.option("--output-format", type=click.Choice(["human", "json"]), default="human")
@click.pass_context
def create_rule_from_nl(ctx, instruction: str, dry_run: bool, output_format: str):
    """Create an email rule from natural language instruction"""
    
    async def _create_rule():
        # Initialize components
        llm_provider = OpenAIProvider()
        parser = NaturalLanguageRuleParser(llm_provider)
        
        try:
            # Parse instruction
            click.echo(f"Parsing instruction: '{instruction}'...")
            rule, intent = await parser.parse_instruction(instruction)
            
            if output_format == "json":
                output = {
                    "success": True,
                    "rule": rule.dict(),
                    "intent": intent.dict(),
                    "instruction": instruction
                }
                click.echo(json.dumps(output, indent=2))
            else:
                # Human-readable output
                click.echo("\n✅ Successfully parsed instruction!")
                click.echo(f"\nRule Name: {rule.name}")
                click.echo(f"Description: {rule.description}")
                click.echo(f"Confidence: {intent.confidence:.0%}")
                
                click.echo("\nConditions:")
                for i, cond in enumerate(rule.conditions, 1):
                    click.echo(f"  {i}. {cond.field} {cond.operator} '{cond.value}'")
                
                click.echo(f"\nAction: {rule.actions[0].type}")
                if rule.actions[0].type == "label":
                    click.echo(f"  Label: {rule.actions[0].label_name}")
                
                if not dry_run:
                    # Save the rule
                    from damien_cli.core_api.rules_api_service import add_rule
                    saved_rule = add_rule(rule.dict())
                    click.echo(f"\n✅ Rule saved with ID: {saved_rule['id']}")
                else:
                    click.echo("\n🔍 Dry run mode - rule not saved")
                    
        except Exception as e:
            if output_format == "json":
                output = {
                    "success": False,
                    "error": str(e),
                    "instruction": instruction
                }
                click.echo(json.dumps(output, indent=2))
            else:
                click.secho(f"\n❌ Error: {str(e)}", fg="red")
    
    # Run async function
    asyncio.run(_create_rule())

@ai_group.command(name="suggest-rules")
@click.option("--limit", type=int, default=5, help="Number of suggestions")
@click.option("--min-confidence", type=float, default=0.7, help="Minimum confidence threshold")
@click.pass_context
def suggest_rules(ctx, limit: int, min_confidence: float):
    """Analyze emails and suggest rules"""
    
    # This will be implemented in Phase 2
    click.echo("Email analysis and rule suggestions coming in Phase 2!")
@ai_group.command(name="analyze")
@click.option("--days", type=int, default=30, help="Number of days to analyze")
@click.option("--max-emails", type=int, default=500, help="Maximum emails to analyze")
@click.option("--query", type=str, help="Custom Gmail query")
@click.pass_context
def analyze_emails(ctx, days: int, max_emails: int, query: Optional[str]):
    """Analyze emails and suggest categorization rules"""
    
    try:
        import asyncio
        categorizer = EmailCategorizer()
        
        import click
        with click.progressbar(length=100, label="Analyzing emails") as bar:
            # Simulate progress
            bar.update(10)
            
            # Create a synchronous wrapper for the async function
            def run_analyze():
                return asyncio.run(categorizer.analyze_emails(
                    query=query,
                    max_emails=max_emails,
                    days_back=days
                ))
            
            results = run_analyze()
            
            bar.update(90)
        
        # Display results
        click.echo(f"\n📊 Analysis Complete!")
        click.echo(f"Emails analyzed: {results['emails_analyzed']}")
        click.echo(f"Patterns found: {results['patterns_found']}")
        click.echo(f"Categories identified: {results['categories_identified']}")
        
        # Show top categories
        click.echo("\n📁 Top Email Categories:")
        for i, category in enumerate(results['categories'][:5], 1):
            click.echo(f"\n{i}. {category['name']}")
            click.echo(f"   Description: {category['description']}")
            click.echo(f"   Confidence: {category['confidence']:.0%}")
            
            if category['suggested_rules']:
                click.echo("   Suggested rule:")
                rule = category['suggested_rules'][0]
                click.echo(f"     - {rule}")
        
        # Show top suggestions
        click.echo("\n💡 Top Rule Suggestions:")
        for i, suggestion in enumerate(results['top_suggestions'][:5], 1):
            click.echo(f"\n{i}. {suggestion['description']}")
            click.echo(f"   Impact: {suggestion['impact']} emails")
            click.echo(f"   Type: {suggestion['type']}")
        
        # Offer to create rules
        if results['top_suggestions']:
            if click.confirm("\nWould you like to create rules from these suggestions?"):
                # Implementation for rule creation workflow
                click.echo("Rule creation workflow to be implemented...")
    except Exception as e:
        click.secho(f"Error during analysis: {str(e)}", fg="red")
        return 1

@ai_group.command(name="learn")
@click.option("--feedback-file", type=str, help="File with user feedback")
@click.option("--output-format", type=click.Choice(["human", "json"]), default="human", help="Output format for the response")
@click.pass_context
def learn_from_feedback(ctx, feedback_file: Optional[str], output_format: str):
    """Learn from user feedback to improve categorization"""
    
    import click
    import os
    
    if not feedback_file:
        if output_format == "json":
            output = {"success": False, "error": "Please provide a feedback file using the --feedback-file option."}
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo("Please provide a feedback file using the --feedback-file option.")
        return

    try:
        # Check if file exists (this will use mocked os.path.exists in tests)
        if not os.path.exists(feedback_file):
            if output_format == "json":
                output = {"success": False, "error": f"File '{feedback_file}' does not exist."}
                click.echo(json.dumps(output, indent=2))
            else:
                click.echo(f"File '{feedback_file}' does not exist.")
            return 1

        # Try to read the file (this will use mocked file operations in tests)
        with open(feedback_file, 'rb') as f:  # Open in binary mode
            feedback_data = f.readlines()
            feedback_data = [line.strip().decode('utf-8') for line in feedback_data if line.strip()]
        
        if not feedback_data:
            if output_format == "json":
                output = {"success": False, "error": "Feedback file is empty."}
                click.echo(json.dumps(output, indent=2))
            else:
                click.echo("Feedback file is empty.")
            return

        if output_format == "human":
            click.echo(f"Processing feedback from {feedback_file}...")
        
        # Process feedback data (simplified for test purposes)
        
        if output_format == "json":
            output = {
                "success": True,
                "feedback_file": feedback_file,
                "processed_entries": len(feedback_data),
                "message": "Feedback learning logic needs to be fully implemented."
            }
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo(f"Successfully processed {len(feedback_data)} feedback entries.")
            click.echo("Feedback learning logic needs to be fully implemented.")

    except Exception as e:
        if output_format == "json":
            output = {"success": False, "error": f"Error processing feedback file: {str(e)}"}
            click.echo(json.dumps(output, indent=2))
        else:
            click.secho(f"Error processing feedback file: {str(e)}", fg="red")
        return 1

@ai_group.command(name="chat")
@click.option("--session-id", type=str, help="Continue existing session")
@click.option("--new-session", is_flag=True, help="Start fresh session")
@click.pass_context
def chat_interface(ctx, session_id: Optional[str], new_session: bool):
    """Start an interactive chat session for email management"""
    
    from datetime import datetime
    import click
    import asyncio
    
    # Generate session ID if needed
    if not session_id or new_session:
        session_id = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    click.echo(f"Starting chat session: {session_id}")
    click.echo("Type 'exit' or 'quit' to end the session.\n")
    
    # Initialize components
    llm_provider = OpenAIProvider()
    query_engine = ConversationalQueryEngine(llm_provider)
    
    try:
        # Load context if continuing session
        context = None
        if not new_session and session_id:
            context = query_engine.context_manager.get_or_create_context(session_id)
            if context and hasattr(context, 'messages') and context.messages:
                click.echo("Resuming previous conversation...\n")
        else:
            # For new sessions, ensure we create fresh context
            context = query_engine.context_manager.get_or_create_context(session_id)
        
        # Interactive loop
        while True:
            try:
                # Get user input
                user_input = click.prompt("You", type=str)
                
                if user_input.lower() in ["exit", "quit"]:
                    click.echo("Ending chat session. Goodbye!")
                    break
                
                # Process query
                click.echo("Assistant: Thinking...")
                
                # Create a synchronous wrapper for the async function
                def run_process():
                    return asyncio.run(query_engine.process_query(user_input, session_id, context))
                
                result = run_process()
                
                # Display response
                click.echo(f"\nAssistant: {result['response']}\n")
                
                # Update context for next iteration
                context = query_engine.context_manager.get_or_create_context(session_id)
                
            except KeyboardInterrupt:
                click.echo("\n\nChat interrupted. Goodbye!")
                break
            except Exception as e:
                click.echo(f"\nError: {str(e)}\n")
                continue
        
        return 0
    except Exception as e:
        click.secho(f"Error starting chat: {str(e)}", fg="red")
        return 1

@ai_group.command(name="ask")
@click.argument("question", type=str)
@click.option("--session-id", type=str, help="Use specific session")
@click.pass_context
def ask_question(ctx, question: str, session_id: Optional[str]):
    """Ask a one-off question about your emails"""
    
    from datetime import datetime
    import click
    import asyncio
    
    if not session_id:
        session_id = f"oneoff_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        llm_provider = OpenAIProvider()
        query_engine = ConversationalQueryEngine(llm_provider)
        
        click.echo("Processing your question...")
        
        # Create a synchronous wrapper for the async function
        def run_process():
            return asyncio.run(query_engine.process_query(question, session_id))
        
        result = run_process()
        
        click.echo(f"\n{result['response']}")
        
        if result.get("emails"):
            click.echo(f"\nFound {len(result['emails'])} relevant email(s).")
            
        return 0
    except Exception as e:
        click.secho(f"Error processing question: {str(e)}", fg="red")
        return 1

@ai_group.command(name="sessions")
@click.option("--clear", type=str, help="Clear specific session")
@click.option("--clear-all", is_flag=True, help="Clear all sessions")
@click.pass_context  
def manage_sessions(ctx, clear: Optional[str], clear_all: bool):
    """Manage chat sessions"""
    
    import click
    from datetime import datetime
    context_manager = ConversationContextManager()
    
    if clear_all:
        if click.confirm("Are you sure you want to clear all chat sessions?"):
            for session in context_manager.list_sessions():
                context_manager.clear_context(session["session_id"])
            click.echo("All sessions cleared.")
        return
    
    if clear:
        context_manager.clear_context(clear)
        click.echo(f"Session {clear} cleared.")
        return
    
    # List sessions
    sessions = context_manager.list_sessions()
    
    if not sessions:
        click.echo("No chat sessions found.")
        return
    
    click.echo("Chat Sessions:")
    for session in sessions:
        last_updated = datetime.fromtimestamp(session["last_updated"])
        click.echo(f"- {session['session_id']}: {session['message_count']} messages, "
                  f"last used {last_updated.strftime('%Y-%m-%d %H:%M')}")