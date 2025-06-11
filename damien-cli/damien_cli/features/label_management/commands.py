"""
Label Management Commands
"""

import click
import json
from typing import Dict, Any, Optional
from ...core_api.labels_api_service import get_labels_service
from ...core_api.gmail_api_service import GmailApiError


@click.group()
def labels():
    """Label management commands."""
    pass


@labels.command()
@click.argument('name')
@click.option('--color-background', help='Background color hex (e.g., #42d692)')
@click.option('--color-text', help='Text color hex (e.g., #094228)')
@click.option('--visibility', type=click.Choice(['show', 'showIfUnread', 'hide']), 
              default='show', help='Label visibility setting')
def create(name: str, color_background: Optional[str], color_text: Optional[str], 
           visibility: str):
    """Create a new Gmail label."""
    try:
        labels_service = get_labels_service()
        
        # Build color dict if colors provided
        color = None
        if color_background or color_text:
            color = {}
            if color_background:
                color["background"] = color_background
            if color_text:
                color["text"] = color_text
        
        result = labels_service.create_label(name, visibility, color)
        
        if result["success"]:
            if result.get("already_exists"):
                click.echo(f"Label '{name}' already exists")
            else:
                click.echo(f"Created label '{name}' with ID: {result['label_id']}")
        else:
            click.echo(f"Error: {result.get('error', 'Unknown error')}")
            
    except GmailApiError as e:
        click.echo(f"Gmail API Error: {str(e)}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")


@labels.command()
@click.argument('name')
def delete(name: str):
    """Delete a Gmail label."""
    try:
        labels_service = get_labels_service()
        result = labels_service.delete_label(name)
        
        if result["success"]:
            click.echo(f"Deleted label '{name}'")
        else:
            click.echo(f"Error: {result.get('error', 'Unknown error')}")
            
    except GmailApiError as e:
        click.echo(f"Gmail API Error: {str(e)}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")


@labels.command()
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), 
              default='table', help='Output format')
def list(output_format: str):
    """List all Gmail labels."""
    try:
        labels_service = get_labels_service()
        labels_list = labels_service.list_labels()
        
        if output_format == 'json':
            click.echo(json.dumps(labels_list, indent=2))
        else:
            # Table format
            click.echo("Labels:")
            click.echo("-" * 60)
            for label in labels_list:
                label_type = "System" if label['type'] == 'system' else "User"
                click.echo(f"{label['name']:<30} {label_type:<10} {label['id']}")
                
    except GmailApiError as e:
        click.echo(f"Gmail API Error: {str(e)}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")


@labels.command()
@click.argument('name')
@click.option('--new-name', help='New name for the label')
@click.option('--color-background', help='New background color hex')
@click.option('--color-text', help='New text color hex')
@click.option('--visibility', type=click.Choice(['show', 'showIfUnread', 'hide']), 
              help='New visibility setting')
def update(name: str, new_name: Optional[str], color_background: Optional[str], 
           color_text: Optional[str], visibility: Optional[str]):
    """Update an existing label."""
    try:
        labels_service = get_labels_service()
        
        # Build updates dict
        updates = {}
        if new_name:
            updates["new_name"] = new_name
        if visibility:
            updates["visibility"] = visibility
        if color_background or color_text:
            updates["color"] = {}
            if color_background:
                updates["color"]["background"] = color_background
            if color_text:
                updates["color"]["text"] = color_text
        
        if not updates:
            click.echo("No updates specified")
            return
        
        result = labels_service.update_label(name, updates)
        
        if result["success"]:
            click.echo(f"Updated label '{name}'")
        else:
            click.echo(f"Error: {result.get('error', 'Unknown error')}")
            
    except GmailApiError as e:
        click.echo(f"Gmail API Error: {str(e)}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")


@labels.command()
@click.argument('name')
def details(name: str):
    """Get detailed information about a label."""
    try:
        labels_service = get_labels_service()
        result = labels_service.get_label_details(name)
        
        click.echo(json.dumps(result, indent=2))
        
    except GmailApiError as e:
        click.echo(f"Gmail API Error: {str(e)}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")


# Tool functions for MCP integration
def create_label_tool(name: str, color: Optional[Dict[str, str]] = None, 
                     visibility: str = "show") -> Dict[str, Any]:
    """Tool function for creating labels via MCP."""
    try:
        labels_service = get_labels_service()
        result = labels_service.create_label(name, visibility, color)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        return {
            "success": False,
            "error_message": str(e)
        }


def delete_label_tool(name: str) -> Dict[str, Any]:
    """Tool function for deleting labels via MCP."""
    try:
        labels_service = get_labels_service()
        result = labels_service.delete_label(name)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        return {
            "success": False,
            "error_message": str(e)
        }


def list_labels_tool() -> Dict[str, Any]:
    """Tool function for listing labels via MCP."""
    try:
        labels_service = get_labels_service()
        labels_list = labels_service.list_labels()
        return {
            "success": True,
            "data": {
                "labels": labels_list,
                "count": len(labels_list)
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error_message": str(e)
        }