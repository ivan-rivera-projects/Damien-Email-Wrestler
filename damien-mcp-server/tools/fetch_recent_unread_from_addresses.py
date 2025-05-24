import sys
import os
import asyncio

# Add the parent directory of damien-mcp-server to sys.path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.damien_adapter import DamienAdapter

async def fetch_recent_unread_from_addresses():
    adapter = DamienAdapter()
    # Fetch 5 most recent unread emails with "From" header included
    list_result = await adapter.list_emails_tool(
        query="is:unread",
        max_results=5,
        include_headers=["From"]
    )
    if not list_result.get("success"):
        print(f"Failed to list emails: {list_result.get('error_message')}")
        return

    email_summaries = list_result["data"]["email_summaries"]
    from_addresses = []

    for email in email_summaries:
        # If "From" header is included in summary, use it directly
        from_header = email.get("From")
        if from_header:
            from_addresses.append(from_header)
        else:
            # Otherwise, fetch email details to get "From" header
            details_result = await adapter.get_email_details_tool(
                message_id=email["id"],
                include_headers=["From"]
            )
            if details_result.get("success"):
                headers = details_result["data"].get("payload", {}).get("headers", [])
                from_value = next((h["value"] for h in headers if h["name"].lower() == "from"), None)
                if from_value:
                    from_addresses.append(from_value)
                else:
                    from_addresses.append("(No From header found)")
            else:
                from_addresses.append(f"(Failed to get details: {details_result.get('error_message')})")

    print("From addresses of 5 most recent unread emails:")
    for addr in from_addresses:
        print(addr)

if __name__ == "__main__":
    asyncio.run(fetch_recent_unread_from_addresses())