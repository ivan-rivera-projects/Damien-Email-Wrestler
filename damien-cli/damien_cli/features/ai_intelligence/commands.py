import click
import asyncio
from typing import Optional
from collections import defaultdict
import json

# Lazy imports - these are imported inside functions to avoid loading heavy ML dependencies at CLI startup
# from damien_cli.core.cli_utils import format_output
# from damien_cli.features.rule_management.models import RuleModel
# from .natural_language.rule_parser import NaturalLanguageRuleParser
# from .llm_providers.openai_provider import OpenAIProvider
# from .categorization.categorizer import EmailCategorizer
# from .conversation.query_engine import ConversationalQueryEngine
# from .conversation.context_manager import ConversationContextManager

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
        # Local imports to avoid loading heavy dependencies at CLI startup
        from .llm_providers.openai_provider import OpenAIProvider
        from .natural_language.rule_parser import NaturalLanguageRuleParser
        
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

@ai_group.command(name="quick-test")
@click.option("--sample-size", type=int, default=50, help="Number of emails to test with")
@click.option("--days", type=int, default=7, help="Days back to look")
@click.pass_context
def quick_test(ctx, sample_size: int, days: int):
    """Quick test of Gmail integration and pattern detection"""
    
    try:
        import asyncio
        from .categorization.gmail_analyzer import GmailEmailAnalyzer
        
        click.echo("🧪 Running Gmail Integration Quick Test")
        click.echo(f"📧 Testing with {sample_size} emails from last {days} days")
        click.echo("")
        
        # Initialize analyzer
        analyzer = GmailEmailAnalyzer()
        
        # Run quick pattern check
        def run_test():
            return asyncio.run(analyzer.quick_pattern_check(
                sample_size=sample_size,
                days_back=days
            ))
        
        result = run_test()
        
        if result["status"] == "success":
            click.echo("✅ Gmail Integration Test: PASSED")
            click.echo(f"📊 Emails analyzed: {result['emails_analyzed']}")
            click.echo(f"👥 Unique senders: {result['unique_senders']}")
            click.echo(f"🔍 Potential patterns: {result['potential_patterns']}")
            
            if result['top_senders']:
                click.echo("\n📨 Top Senders:")
                for sender, count in result['top_senders']:
                    click.echo(f"   • {sender}: {count} emails")
            
            if result['common_keywords']:
                click.echo(f"\n🔤 Common Keywords: {', '.join(result['common_keywords'])}")
            
            click.echo(f"\n💡 Recommendation: {result['recommendation']}")
            
            if result['potential_patterns'] > 5:
                click.echo("\n🎉 Great! Your inbox has good pattern potential.")
                click.echo("   Run 'damien ai analyze' for full analysis.")
            
        elif result["status"] == "no_emails":
            click.echo("⚠️  No emails found matching criteria")
            click.echo("   Try increasing --days or adjusting your Gmail settings")
            
        else:
            click.echo(f"❌ Test failed: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        click.secho(f"❌ Quick test failed: {str(e)}", fg="red")
        click.echo("\nTroubleshooting tips:")
        click.echo("1. Ensure Gmail API is authenticated")
        click.echo("2. Check internet connection")
        click.echo("3. Verify Gmail permissions")
        return 1

@ai_group.command(name="suggest-rules")
@click.option("--limit", type=int, default=5, help="Number of suggestions")
@click.option("--min-confidence", type=float, default=0.7, help="Minimum confidence threshold")
@click.option("--days", type=int, default=14, help="Days back to analyze")
@click.option("--max-emails", type=int, default=200, help="Maximum emails for quick analysis")
@click.pass_context
def suggest_rules(ctx, limit: int, min_confidence: float, days: int, max_emails: int):
    """Quickly analyze emails and suggest rules (lighter version of full analysis)"""
    
    try:
        import asyncio
        from .categorization.gmail_analyzer import GmailEmailAnalyzer
        
        click.echo("💡 Generating rule suggestions from your emails...")
        click.echo(f"📧 Analyzing up to {max_emails} emails from last {days} days")
        click.echo("")
        
        # Initialize analyzer
        analyzer = GmailEmailAnalyzer()
        
        # Run focused analysis for suggestions
        def run_analysis():
            return asyncio.run(analyzer.analyze_inbox(
                max_emails=max_emails,
                days_back=days,
                min_confidence=min_confidence
            ))
        
        results = run_analysis()
        
        if not results.category_suggestions:
            click.echo("🤷 No rule suggestions found with the current criteria")
            click.echo("Try lowering --min-confidence or increasing --days/--max-emails")
            return 0
        
        click.echo(f"✅ Found {len(results.category_suggestions)} rule suggestions!")
        click.echo("")
        
        # Show top suggestions
        for i, suggestion in enumerate(results.category_suggestions[:limit], 1):
            click.echo(f"{i}. 📋 {suggestion.category_name}")
            click.echo(f"   📝 {suggestion.description}")
            click.echo(f"   📊 Impact: {suggestion.email_count} emails ({suggestion.affected_email_percentage:.1f}%)")
            click.echo(f"   🎯 Confidence: {suggestion.confidence:.0%}")
            
            if suggestion.rule_conditions:
                click.echo("   🔧 Rule logic:")
                for condition in suggestion.rule_conditions:
                    click.echo(f"      IF {condition.field} {condition.operator} '{condition.value}'")
            
            if suggestion.rule_actions:
                action = suggestion.rule_actions[0]
                if action.action_type.value == "label":
                    label_name = action.parameters.get("label_name", "New Label")
                    click.echo(f"      THEN apply label: {label_name}")
                elif action.action_type.value == "archive":
                    click.echo(f"      THEN archive email")
            
            click.echo("")
        
        # Summary
        total_impact = sum(s.email_count for s in results.category_suggestions[:limit])
        click.echo(f"📈 Total potential impact: {total_impact} emails could be automated")
        
        if results.summary_statistics:
            automation_rate = results.summary_statistics.get('automation_rate_percent', 0)
            time_savings = results.summary_statistics.get('estimated_time_savings_hours', 0)
            if automation_rate > 0:
                click.echo(f"⚡ Potential automation rate: {automation_rate:.1f}%")
            if time_savings > 0:
                click.echo(f"⏰ Estimated time savings: {time_savings:.1f} hours")
        
        # Offer next steps
        click.echo("\n🚀 Next steps:")
        click.echo("   • Run full analysis: damien ai analyze")
        click.echo("   • Create rules manually based on suggestions above")
        click.echo("   • Use: damien ai create-rule \"<natural language>\"")
        
    except Exception as e:
        click.secho(f"❌ Error generating suggestions: {str(e)}", fg="red")
        return 1
@ai_group.command(name="analyze")
@click.option("--days", type=int, default=30, help="Number of days to analyze")
@click.option("--max-emails", type=int, default=500, help="Maximum emails to analyze")
@click.option("--query", type=str, help="Custom Gmail query")
@click.option("--min-confidence", type=float, default=0.7, help="Minimum confidence threshold")
@click.option("--output-format", type=click.Choice(["human", "json"]), default="human", help="Output format")
@click.pass_context
def analyze_emails(ctx, days: int, max_emails: int, query: Optional[str], min_confidence: float, output_format: str):
    """Analyze Gmail emails and suggest intelligent categorization rules"""
    
    try:
        import asyncio
        from .categorization.gmail_analyzer import GmailEmailAnalyzer
        
        # Initialize the Gmail analyzer
        analyzer = GmailEmailAnalyzer()
        
        if output_format == "human":
            click.echo("🚀 Starting Gmail inbox analysis...")
            click.echo(f"📧 Analyzing up to {max_emails} emails from the last {days} days")
            if query:
                click.echo(f"🔍 Using custom query: {query}")
            click.echo("")
        
        # Run the analysis
        def run_analysis():
            return asyncio.run(analyzer.analyze_inbox(
                max_emails=max_emails,
                days_back=days,
                min_confidence=min_confidence,
                query_filter=query
            ))
        
        results = run_analysis()
        
        if output_format == "json":
            # Convert results to JSON-serializable format
            output = {
                "success": True,
                "analysis_summary": {
                    "emails_analyzed": results.total_emails_analyzed,
                    "patterns_detected": len(results.patterns_detected),
                    "suggestions_generated": len(results.category_suggestions)
                },
                "patterns": [
                    {
                        "type": pattern.pattern_type.value,
                        "name": pattern.pattern_name,
                        "email_count": pattern.email_count,
                        "confidence": pattern.confidence,
                        "description": pattern.description
                    }
                    for pattern in results.patterns_detected
                ],
                "suggestions": [
                    {
                        "category_name": suggestion.category_name,
                        "description": suggestion.description,
                        "email_count": suggestion.email_count,
                        "confidence": suggestion.confidence,
                        "business_impact": f"{suggestion.affected_email_percentage:.1f}% of emails"
                    }
                    for suggestion in results.category_suggestions
                ],
                "performance": {
                    "duration_seconds": results.processing_performance.duration_ms / 1000,
                    "items_processed": results.processing_performance.items_processed
                }
            }
            click.echo(json.dumps(output, indent=2))
            return 0
        
        # Human-readable output
        click.echo("✅ Analysis Complete!")
        click.echo(f"📊 Emails analyzed: {results.total_emails_analyzed}")
        click.echo(f"🔍 Patterns detected: {len(results.patterns_detected)}")
        click.echo(f"💡 Suggestions generated: {len(results.category_suggestions)}")
        click.echo(f"⏱️  Processing time: {results.processing_performance.duration_ms/1000:.1f}s")
        
        # Show detected patterns
        if results.patterns_detected:
            click.echo("\n🔍 Top Email Patterns Detected:")
            for i, pattern in enumerate(results.patterns_detected[:5], 1):
                click.echo(f"\n{i}. {pattern.pattern_name}")
                click.echo(f"   Type: {pattern.pattern_type.value.title()}")
                click.echo(f"   Emails: {pattern.email_count}")
                click.echo(f"   Confidence: {pattern.confidence:.0%}")
                click.echo(f"   Description: {pattern.description}")
        
        # Show rule suggestions
        if results.category_suggestions:
            click.echo("\n💡 Intelligent Rule Suggestions:")
            for i, suggestion in enumerate(results.category_suggestions[:5], 1):
                click.echo(f"\n{i}. {suggestion.category_name}")
                click.echo(f"   Description: {suggestion.description}")
                click.echo(f"   Impact: {suggestion.email_count} emails ({suggestion.affected_email_percentage:.1f}%)")
                click.echo(f"   Confidence: {suggestion.confidence:.0%}")
                
                # Show the rule logic
                if suggestion.rule_conditions:
                    click.echo("   Rule logic:")
                    for condition in suggestion.rule_conditions:
                        click.echo(f"     • {condition.field} {condition.operator} '{condition.value}'")
                
                if suggestion.rule_actions:
                    action = suggestion.rule_actions[0]
                    if action.action_type.value == "label":
                        label_name = action.parameters.get("label_name", "New Label")
                        click.echo(f"     → Apply label: {label_name}")
                    elif action.action_type.value == "archive":
                        click.echo(f"     → Archive email")
                    else:
                        click.echo(f"     → Action: {action.action_type.value}")
        
        # Summary statistics
        if results.summary_statistics:
            stats = results.summary_statistics
            click.echo(f"\n📈 Summary Statistics:")
            click.echo(f"   • Unique senders: {stats.get('unique_senders', 'N/A')}")
            click.echo(f"   • High confidence patterns: {stats.get('high_confidence_patterns', 'N/A')}")
            click.echo(f"   • Potential automation rate: {stats.get('automation_rate_percent', 0):.1f}%")
            click.echo(f"   • Estimated time savings: {stats.get('estimated_time_savings_hours', 0):.1f} hours")
        
        # Offer to create rules
        if results.category_suggestions and click.confirm("\n🤔 Would you like to create rules from these suggestions?"):
            click.echo("\n🚧 Rule creation workflow coming soon!")
            click.echo("For now, you can use the suggestions above to manually create rules.")
        
        return 0
        
    except Exception as e:
        if output_format == "json":
            output = {"success": False, "error": str(e)}
            click.echo(json.dumps(output, indent=2))
        else:
            click.secho(f"❌ Error during analysis: {str(e)}", fg="red")
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
    
    # Local imports
    from .llm_providers.openai_provider import OpenAIProvider
    from .conversation.query_engine import ConversationalQueryEngine
    
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
        # Local imports
        from .llm_providers.openai_provider import OpenAIProvider
        from .conversation.query_engine import ConversationalQueryEngine
        
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
    
    # Local import
    from .conversation.context_manager import ConversationContextManager
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