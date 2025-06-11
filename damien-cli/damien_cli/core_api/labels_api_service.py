"""
Labels API Service - Handles all Gmail label operations.
"""

import logging
from typing import Dict, List, Any, Optional
from .gmail_api_service import (
    get_authenticated_service, 
    create_label, 
    delete_label,
    get_label_id,
    GmailApiError
)

logger = logging.getLogger(__name__)


class LabelsAPIService:
    """Service class for Gmail label operations."""
    
    def __init__(self):
        """Initialize the Labels API Service."""
        self.service = None
        
    def _ensure_service(self):
        """Ensure Gmail service is authenticated."""
        if not self.service:
            self.service = get_authenticated_service()
            
    def create_label(self, 
                    name: str, 
                    visibility: str = "show",
                    color: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Create a new Gmail label.
        
        Args:
            name: Name of the label to create
            visibility: Label visibility ("show", "showIfUnread", "hide")
            color: Optional dict with "background" and "text" hex colors
            
        Returns:
            Dict containing label creation result
        """
        self._ensure_service()
        
        # Map simple visibility to Gmail API parameters
        visibility_map = {
            "show": ("labelShow", "show"),
            "showIfUnread": ("labelShowIfUnread", "show"),
            "hide": ("labelHide", "hide")
        }
        
        label_vis, msg_vis = visibility_map.get(visibility, ("labelShow", "show"))
        
        # Extract colors if provided
        bg_color = color.get("background") if color else None
        text_color = color.get("text") if color else None
        
        return create_label(
            self.service,
            name,
            label_vis,
            msg_vis,
            bg_color,
            text_color
        )
    
    def delete_label(self, name: str) -> Dict[str, Any]:
        """
        Delete a Gmail label.
        
        Args:
            name: Name or ID of the label to delete
            
        Returns:
            Dict containing deletion result
        """
        self._ensure_service()
        return delete_label(self.service, name)
    
    def update_label(self, name: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing label (name, color, visibility).
        
        Args:
            name: Current name or ID of the label
            updates: Dict containing updates (new_name, color, visibility)
            
        Returns:
            Dict containing update result
        """
        self._ensure_service()
        
        # Get label ID
        label_id = get_label_id(self.service, name)
        if not label_id:
            raise GmailApiError(f"Label '{name}' not found")
        
        # Build update body
        label_body = {}
        
        if "new_name" in updates:
            label_body["name"] = updates["new_name"]
            
        if "visibility" in updates:
            visibility_map = {
                "show": ("labelShow", "show"),
                "showIfUnread": ("labelShowIfUnread", "show"),
                "hide": ("labelHide", "hide")
            }
            label_vis, msg_vis = visibility_map.get(updates["visibility"], ("labelShow", "show"))
            label_body["labelListVisibility"] = label_vis
            label_body["messageListVisibility"] = msg_vis
            
        if "color" in updates:
            label_body["color"] = {}
            if "background" in updates["color"]:
                label_body["color"]["backgroundColor"] = updates["color"]["background"]
            if "text" in updates["color"]:
                label_body["color"]["textColor"] = updates["color"]["text"]
        
        try:
            result = self.service.users().labels().update(
                userId='me',
                id=label_id,
                body=label_body
            ).execute()
            
            logger.info(f"Updated label '{name}' (ID: {label_id})")
            
            return {
                "success": True,
                "label_id": result['id'],
                "label_name": result['name'],
                "updated": True,
                "message": f"Successfully updated label"
            }
            
        except Exception as e:
            raise GmailApiError(f"Failed to update label: {str(e)}")
    
    def list_labels(self) -> List[Dict[str, Any]]:
        """
        List all Gmail labels.
        
        Returns:
            List of label dictionaries
        """
        self._ensure_service()
        
        try:
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            # Sort labels: system labels first, then user labels alphabetically
            system_labels = ["INBOX", "SPAM", "TRASH", "UNREAD", "IMPORTANT", "STARRED", 
                           "SENT", "DRAFT", "CATEGORY_PERSONAL", "CATEGORY_SOCIAL", 
                           "CATEGORY_PROMOTIONS", "CATEGORY_UPDATES", "CATEGORY_FORUMS"]
            
            system = []
            user = []
            
            for label in labels:
                if label['id'] in system_labels:
                    system.append(label)
                else:
                    user.append(label)
            
            # Sort each group
            system.sort(key=lambda x: x['name'])
            user.sort(key=lambda x: x['name'].lower())
            
            return system + user
            
        except Exception as e:
            raise GmailApiError(f"Failed to list labels: {str(e)}")
    
    def get_label_details(self, name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific label.
        
        Args:
            name: Name or ID of the label
            
        Returns:
            Dict containing label details
        """
        self._ensure_service()
        
        label_id = get_label_id(self.service, name)
        if not label_id:
            raise GmailApiError(f"Label '{name}' not found")
        
        try:
            result = self.service.users().labels().get(
                userId='me',
                id=label_id
            ).execute()
            
            return result
            
        except Exception as e:
            raise GmailApiError(f"Failed to get label details: {str(e)}")


# Singleton instance
_labels_service = LabelsAPIService()


def get_labels_service() -> LabelsAPIService:
    """Get the singleton Labels API Service instance."""
    return _labels_service