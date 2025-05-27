RULE_GRAMMAR_PROMPT = """
You are an expert at parsing email management instructions. Convert natural language into structured email rules.

SUPPORTED FIELDS:
- from: Email sender (supports partial matching)
- to: Email recipient
- subject: Email subject line
- body: Email body content
- label: Gmail labels (e.g., INBOX, SPAM, IMPORTANT)
- age_days: Email age in days
- has_attachment: Whether email has attachments (true/false)
- size_mb: Email size in megabytes

SUPPORTED OPERATORS:
- contains: Field contains the value (case-insensitive)
- equals: Exact match
- not_contains: Field does not contain value
- greater_than: Numeric comparison (for age_days, size_mb)
- less_than: Numeric comparison
- matches_regex: Regular expression matching

SUPPORTED ACTIONS:
- archive: Move to archive
- label: Apply a Gmail label
- trash: Move to trash
- mark_read: Mark as read
- mark_unread: Mark as unread
- forward: Forward to email address

TIME EXPRESSIONS:
- "older than X days/weeks/months" -> age_days > X
- "newer than X days" -> age_days < X
- "from last week" -> age_days < 7
- "from this month" -> age_days < 30

COMMON PATTERNS:
- "newsletters" -> from contains "newsletter" OR subject contains "newsletter"
- "from my team" -> from contains "@mycompany.com"
- "important emails" -> label equals "IMPORTANT"
- "large attachments" -> has_attachment equals true AND size_mb > 10
"""

# Common email patterns for recognition
EMAIL_PATTERNS = {
    "newsletters": {
        "patterns": ["newsletter", "digest", "weekly update", "monthly roundup"],
        "fields": ["from", "subject"]
    },
    "notifications": {
        "patterns": ["notification", "alert", "reminder", "automated"],
        "fields": ["from", "subject"]
    },
    "receipts": {
        "patterns": ["receipt", "order", "invoice", "payment", "purchase"],
        "fields": ["subject", "body"]
    },
    "social": {
        "patterns": ["facebook", "twitter", "linkedin", "instagram"],
        "fields": ["from"]
    },
    "work": {
        "patterns": ["@company.com", "meeting", "project", "deadline"],
        "fields": ["from", "subject"]
    }
}