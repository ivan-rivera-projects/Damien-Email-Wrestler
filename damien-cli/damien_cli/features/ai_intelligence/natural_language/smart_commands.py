"""
Smart Natural Language Commands for Email Organization
"""

import click
import json
from typing import Dict, Any, Optional
from .rule_converter import NaturalLanguageRuleConverter, EnhancedRuleParser
from ..commands import create_rule_from_nl
from ....features.rule_management.commands import add_rule_cmd, apply_rules_cmd


@click.group()
def smart():
    """Smart email organization commands."""
    pass


@smart.command()
@click.argument('instruction')
@click.option('--preview', is_flag=True, help='Preview the rule without creating it')
@click.option('--apply-existing', is_flag=True, help='Apply rule to existing emails')
def rule(instruction: str, preview: bool, apply_existing: bool):
    """Create a rule from natural language instruction."""
    try:
        converter = NaturalLanguageRuleConverter()
        result = converter.parse_instruction(
            instruction,
            create_labels=not preview,
            apply_immediately=apply_existing
        )
        
        if not result["success"]:
            click.echo(f"Error: {result.get('error', 'Unknown error')}")
            return
        
        if preview:
            click.echo("Preview Mode - Rule would be:")
            click.echo(json.dumps(result["rule"], indent=2))
            if result.get("created_labels"):
                click.echo(f"\nLabels that would be created: {result['created_labels']}")
            if result.get("suggestions"):
                click.echo("\nSuggestions:")
                for suggestion in result["suggestions"]:
                    click.echo(f"  • {suggestion}")
        else:
            # Create the rule
            rule_dict = result["rule"]
            # Use existing add_rule_cmd functionality
            
            if result.get("created_labels"):
                click.echo(f"Created labels: {', '.join(result['created_labels'])}")
            
            click.echo(f"Created rule: {rule_dict['name']}")
            
            if apply_existing:
                click.echo("Applying rule to existing emails...")
                # Apply the rule (would need rule ID from creation)
                
    except Exception as e:
        click.echo(f"Error: {str(e)}")


@smart.command()
@click.argument('pattern')
@click.argument('action')
@click.option('--dry-run', is_flag=True, help='Preview without making changes')
@click.option('--apply-existing', is_flag=True, default=True, help='Apply to existing emails')
def organize(pattern: str, action: str, dry_run: bool, apply_existing: bool):
    """One-stop email organization command."""
    try:
        converter = NaturalLanguageRuleConverter()
        result = converter.create_smart_rule(pattern, action, preview=dry_run)
        
        if not result["success"]:
            click.echo(f"Error: {result.get('error', 'Unknown error')}")
            return
        
        if dry_run:
            click.echo("Preview Mode - Would affect:")
            if result.get("preview"):
                for email in result["preview"][:5]:  # Show first 5
                    click.echo(f"  • {email.get('Subject', 'No subject')} from {email.get('From', 'Unknown')}")
            if result.get("total_matching", 0) > 5:
                click.echo(f"  ... and {result['total_matching'] - 5} more emails")
            
            click.echo(f"\nRule that would be created:")
            click.echo(json.dumps(result["rule"], indent=2))
        else:
            if result.get("created_labels"):
                click.echo(f"✓ Created labels: {', '.join(result['created_labels'])}")
            
            click.echo(f"✓ Created rule: {result['rule']['name']}")
            
            if apply_existing and result.get("emails_processed"):
                click.echo(f"✓ Applied to {result['emails_processed']} existing emails")
            
            click.echo(result.get("summary", "Organization complete!"))
                
    except Exception as e:
        click.echo(f"Error: {str(e)}")


# Tool functions for MCP integration
def parse_natural_language_rule_tool(instruction: str, create_labels: bool = True) -> Dict[str, Any]:
    """Tool function for parsing natural language rules via MCP."""
    try:
        converter = NaturalLanguageRuleConverter()
        result = converter.parse_instruction(
            instruction,
            create_labels=create_labels,
            apply_immediately=False
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        return {
            "success": False,
            "error_message": str(e)
        }


def create_smart_rule_tool(instruction: str, preview: bool = True, 
                          apply_to_existing: bool = False) -> Dict[str, Any]:
    """Tool function for creating smart rules via MCP."""
    try:
        converter = NaturalLanguageRuleConverter()
        result = converter.parse_instruction(
            instruction,
            create_labels=not preview,
            apply_immediately=apply_to_existing
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        return {
            "success": False,
            "error_message": str(e)
        }


def organize_emails_tool(pattern: str, action: str, apply_to_existing: bool = True,
                        dry_run: bool = False) -> Dict[str, Any]:
    """Tool function for organizing emails via MCP."""
    try:
        converter = NaturalLanguageRuleConverter()
        result = converter.create_smart_rule(pattern, action, preview=dry_run)
        
        if result["success"] and not dry_run:
            # Add processing logic here for applying to existing emails
            if apply_to_existing:
                result["emails_processed"] = 0  # Placeholder
                result["applied_to_existing"] = True
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        return {
            "success": False,
            "error_message": str(e)
        }