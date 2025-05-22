from pathlib import Path

# Usually your project root is where pyproject.toml is
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"  # Path to your credentials.json
TOKEN_FILE = DATA_DIR / "token.json"  # Where we'll save the login token


# Make sure DATA_DIR exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# These are the 'permissions' Damien will ask for from Gmail.
# 'gmail.modify' allows reading, moving to trash, deleting, labeling.
# Start with 'gmail.readonly' if you want to be cautious first, then change later.
# Use the following scope for all permissions except explicit permanent deletion.
# SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
# Use the following scope for permanent deletion **WARNING** AND PROCEED WITH CAUTION.
SCOPES = ["https://mail.google.com/"]
RULES_FILE = DATA_DIR / "rules.json"
