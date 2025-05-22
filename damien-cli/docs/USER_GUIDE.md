# Damien-CLI User Guide

This guide provides instructions on how to use the Damien-CLI application.

## Installation & Setup

Please refer to the main `README.md` for installation and initial setup instructions, including Gmail API authentication.

## General Usage

All commands start with `poetry run damien`. You can get help for any command or subcommand by appending `--help`.

```bash
poetry run damien --help
poetry run damien emails --help
poetry run damien rules --help
```

## Global Options

* `--verbose` / `-v`: Enable verbose (DEBUG level) logging. Output will be more detailed, both to console and the log file.
* `--output-format json`: Many commands support this to output results in JSON format for programmatic use.

## Commands

### login

Authenticates Damien with your Gmail account. This will typically open a web browser for authorization.

```bash
poetry run damien login
```

### hello

A simple command to check if Damien is responsive.

```bash
poetry run damien hello
```

### emails

Group of commands for managing emails.

#### emails list

Lists emails from your Gmail account.

* `--query <TEXT>` or `-q <TEXT>`: Gmail search query (e.g., "is:unread", "from:boss@example.com subject:report").
* `--max-results <NUMBER>` or `-m <NUMBER>`: Maximum number of emails to retrieve (default: 10).
* `--page-token <TEXT>` or `-p <TEXT>`: Token for fetching the next page of results.
* `--output-format [human|json]`: Output format.

Example:
```bash
poetry run damien emails list --query "is:starred" --max-results 5
poetry run damien emails list --output-format json
```

#### emails get

Retrieves and displays details of a specific email.

* `--id <EMAIL_ID>`: The ID of the email (required).
* `--format [metadata|full|raw]`: The level of detail to retrieve (default: 'full').
* `--output-format [human|json]`: Output format.

Example:
```bash
poetry run damien emails get --id 196abc123def --format metadata
```

#### emails trash

Moves specified emails to the Trash folder.

* `--ids <ID1,ID2,...>`: Comma-separated list of email IDs (required).
* `--dry-run`: Show what would be done without making changes.
* `--yes` / `-y`: Automatically answer "yes" to confirmation prompts.
Example:
```bash
poetry run damien emails trash --ids 196abc123,197def456 --dry-run
poetry run damien emails trash --ids 198xyz789 # Will ask for confirmation
```

#### emails delete

PERMANENTLY deletes specified emails. This action is irreversible.

* `--ids <ID1,ID2,...>`: Comma-separated list of email IDs (required).
* `--dry-run`: Show what would be done without making changes.
* `--yes` / `-y`: Automatically answer "yes" to ALL confirmation prompts for permanent deletion. Use with extreme caution.
Example:
```bash
poetry run damien emails delete --ids 196abc123 --dry-run
# poetry run damien emails delete --ids 198xyz789 # Will require multiple confirmations
```

#### emails label

Adds or removes labels from specified emails.

* `--ids <ID1,ID2,...>`: Comma-separated list of email IDs (required).
* `--add-labels <LABEL_NAME1,LABEL_NAME2,...>`: Labels to add.
* `--remove-labels <LABEL_NAME1,LABEL_NAME2,...>`: Labels to remove.
* `--dry-run`: Show what would be done without making changes.

Example:
```bash
poetry run damien emails label --ids 196abc --add-labels MyLabel,Important
poetry run damien emails label --ids 197def --remove-labels OldLabel --dry-run
```

#### emails mark

Marks specified emails as read or unread.

* `--ids <ID1,ID2,...>`: Comma-separated list of email IDs (required).
* `--action [read|unread]`: Action to perform (required).
* `--dry-run`: Show what would be done without making changes.

Example:
```bash
poetry run damien emails mark --ids 196abc,197def --action read
poetry run damien emails mark --ids 198xyz --action unread --dry-run
```

### rules

Group of commands for managing filtering rules.

#### rules list

Lists all configured filtering rules.

* `--output-format [human|json]`: Output format.

Example:
```bash
poetry run damien rules list
poetry run damien rules list --output-format json
```

#### rules add

Adds a new filtering rule. Rule definition must be provided as a JSON string or a path to a JSON file.

* `--rule-json <JSON_STRING_OR_FILEPATH>`: The rule definition (required).

Example JSON structure:
```json
{
  "name": "Trash Old Promos",
  "description": "Moves promotional emails older than 90 days to trash",
  "is_enabled": true,
  "conditions": [
    {"field": "from", "operator": "contains", "value": "promo@example.com"},
    {"field": "label", "operator": "contains", "value": "CATEGORY_PROMOTIONS"}
    // "age_days_gt": 90 (Age condition not yet implemented in matching logic)
  ],
  "condition_conjunction": "AND",
  "actions": [
    {"type": "trash"}
  ]
}
```

Example usage (assuming my_rule.json contains the above):
```bash
poetry run damien rules add --rule-json my_rule.json
poetry run damien rules add --rule-json '{"name": "Quick Rule", "conditions": [...], "actions": [{"type": "mark_read"}]}'
```

#### rules delete

Deletes a rule by its ID or Name.

* `--id <RULE_ID_OR_NAME>`: The ID or name of the rule to delete (required).
* `--yes` / `-y`: Automatically answer "yes" to confirmation prompts.
Example:
```bash
poetry run damien rules delete --id "Trash Old Promos" # Will ask for confirmation
poetry run damien rules delete --id "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" # Using rule ID
```

#### rules apply

Applies configured (or specified) active rules to emails in your Gmail account. This command allows for powerful, automated email processing.

*   `--query <TEXT>` or `-q <TEXT>`: Optional Gmail query to further filter emails *before* rules are applied (e.g., "in:inbox"). This is combined with rule-specific queries.
*   `--rule-ids <ID1,ID2,...>`: Comma-separated list of specific rule IDs or Names to apply. If not set, all enabled rules are considered.
*   `--scan-limit <NUMBER>`: Maximum number of emails to scan across all rules. This helps limit the scope of a run. Default is no limit (processes all matched emails per rule, up to an internal maximum per rule if not otherwise limited).
*   `--date-after <YYYY/MM/DD>`: Process emails received after this date.
*   `--date-before <YYYY/MM/DD>`: Process emails received before this date.
*   `--all-mail`: Process all mail without any default date restrictions. By default (if no date options are specified), Damien processes emails from the last 30 days. Using `--all-mail` overrides this default.
*   `--dry-run`: Simulate rule application without making any actual changes to your emails. Shows what actions would be taken. Highly recommended for testing new rules.
*   `--confirm`: Require user confirmation before applying actions (if not in `dry-run` mode). This prompt can be bypassed if `--yes` is also used.
*   `--yes` / `-y`: Automatically answer "yes" to the `--confirm` prompt if it's active.
*   `--output-format [human|json]`: Output format for the summary.
**Understanding Date Filtering:**
*   If neither `--date-after`, `--date-before`, nor `--all-mail` is specified, `rules apply` defaults to processing emails from the last 30 days.
*   `--date-after` and `--date-before` can be used together to define a specific date range.
*   `--all-mail` processes the entire mailbox subject to other filters like `--query` or rule conditions. If `--all-mail` is used with `--date-after` or `--date-before`, the explicit date options take precedence for that boundary.

**Execution Flow:**
1.  Damien loads active rules (or the subset specified by `--rule-ids`).
2.  For each rule, it constructs a Gmail query. This query combines:
    *   The global filter from `--query` (if any).
    *   The date filters (`--date-after`, `--date-before`, or the 30-day default unless `--all-mail` is used).
    *   Conditions from the rule itself that can be translated into Gmail search terms (e.g., `from:`, `subject:`, `label:`).
3.  Damien fetches emails matching this combined query.
4.  If a rule has conditions that *cannot* be translated into a Gmail query (e.g., body content checks, complex OR logic), Damien fetches the full details for the candidate emails and performs client-side matching.
5.  Actions for matched emails are aggregated.
6.  If not a `--dry-run`, the actions are executed.

**Interpreting the Summary & Performance Tips:**
*   **`Total Emails Scanned`**: This metric in the summary represents the sum of candidate emails fetched for *each rule* based on its specific combined query (global filters + rule's own server-filterable conditions). If an email is a candidate for multiple rules, it will be counted towards this total for each of those rules. This number can be higher than the unique number of emails in your initial scope if there's overlap in rule candidacy.
*   **`Emails Matching Any Rule`**: This is the count of *unique* email IDs that matched at least one rule after all server-side and client-side processing. This is a more direct measure of how many individual emails were ultimately affected or would be affected.
*   **Performance with Broad Conditions**: Rules with conditions that cannot be efficiently filtered by Gmail's server-side search (e.g., conditions on `body_snippet` or complex regular expressions if they were supported) might cause Damien to fetch a large number of initial candidate emails, especially if your global `--query` or date range is broad. Damien will then perform client-side matching on these candidates.
    *   **Recommendation**: For such rules, or when running `rules apply` on a very large mailbox or broad date range for the first time, it's highly recommended to:
        *   Use the `--dry-run` flag first to see how many candidates are being fetched and what actions would be taken.
        *   Utilize the `--scan-limit <NUMBER>` option to cap the total number of emails processed. This helps prevent excessive API calls and long run times.
        *   Employ more specific global `--query` options or tighter date ranges (`--date-after`, `--date-before`) to narrow down the initial set of emails considered.

**Example Usage:**

Apply all enabled rules to emails from the last 7 days, in dry-run mode:
```bash
poetry run damien rules apply --date-after $(date -v-7d +%Y/%m/%d) --dry-run
# Note: date command might vary by OS. For macOS, the above works.
# For GNU date (Linux), it might be: date --date="7 days ago" +%Y/%m/%d
```

Apply a specific rule named "Archive Newsletters" to unread emails, with confirmation:
```bash
poetry run damien rules apply --rule-ids "Archive Newsletters" --query "is:unread" --confirm
```

Apply rules to all emails older than 2023/01/01, limited to scanning 500 emails in total:
```bash
poetry run damien rules apply --date-before 2023/01/01 --scan-limit 500
```

Output a JSON summary of a dry run for all rules against all mail:
```bash
poetry run damien rules apply --all-mail --dry-run --output-format json
```
