# Damien-CLI Developer Guide

This guide is for developers looking to contribute to or understand the internals of Damien-CLI.

## Project Structure

Refer to `docs/ARCHITECTURE.md` for a detailed overview of the project structure.

Key directories:
* `damien_cli/`: Main application package.
  * `core/`: Shared components.
  * `features/`: Feature-sliced modules (e.g., `email_management`, `rule_management`).
  * `integrations/`: Wrappers for external APIs (e.g., `gmail_integration.py`).
* `tests/`: Automated tests, mirroring the `damien_cli` structure.
* `data/`: Runtime data (tokens, rules, logs) - ignored by Git.

## Setup for Development

1. **Prerequisites:** Python 3.13+, Poetry.
2. **Clone:** `git clone <repository_url>`
3. **Navigate:** `cd damien-cli`
4. **Install Dependencies (including dev dependencies):** `poetry install`
5. **Activate Virtual Environment:** `poetry shell` (This allows you to run `damien` directly instead of `poetry run damien`).
6. **Set up `credentials.json`:** Follow `docs/GMAIL_API_SETUP.md`.
7. **Initial Login:** Run `damien login` (or `poetry run damien login` if not in poetry shell).

## Running the CLI during Development

* Using Poetry: `poetry run damien <command> [options]`
* If inside Poetry shell: `damien <command> [options]`

## Running Tests

Pytest is used for testing.

* Run all tests:
```bash
poetry run pytest
```
* Run with verbose output:
```bash
poetry run pytest -v
```
* Run a specific test file:
```bash
poetry run pytest -v tests/features/email_management/test_commands.py
```
* Run a specific test function:
```bash
poetry run pytest -v tests/features/email_management/test_commands.py::test_emails_list_human_output
```
* Run tests and generate a coverage report:
```bash
poetry run pytest --cov=damien_cli
```
This will show test coverage for the `damien_cli` package. An HTML report can often be generated in `htmlcov/`.

### Testing Commands with Confirmation and API Interactions
When testing CLI command functions (e.g., in `features/.../commands.py`) that involve user confirmation or interact with the `core_api` layer:
*   **Mocking `core_api` Services**: Functions from `gmail_api_service.py` or `rules_api_service.py` that are called by your command should be mocked (e.g., using `@patch('damien_cli.core_api.some_service.some_function')`). This isolates your command logic for testing.
*   **Mocking Shared `_confirm_action`**: For commands that use the confirmation prompt:
    *   Patch the shared utility: `@patch('damien_cli.features.your_feature.commands._confirm_action')` (patch where it's *used* by the command module).
    *   Test different return values from the mock to simulate user confirming `(True, "optional_message")`, user aborting `(False, "Abort message")`, or the `--yes` flag being active (by asserting `_confirm_action` is called with `yes_flag=True` and returns `(True, "Bypass message")`).
*   **Testing `--yes` Flag**:
    *   Ensure tests cover scenarios where the `--yes` flag is passed to the command.
    *   Verify that `_confirm_action` is called with `yes_flag=True`.
    *   Verify that the command proceeds without interactive prompting and that the appropriate "Confirmation bypassed..." message (now typically echoed by the command function itself after getting it from `_confirm_action`) is present in the output.
*   **Context Object (`ctx.obj`)**: Remember that `runner.invoke(cli_entry.damien, [...], obj={...})` can be used to set up `ctx.obj` with necessary mocks (like a mock `gmail_service` or `logger`) for your command tests.
*   **Mocking `gmail_api_service` (for `rules_api_service.py` tests)**: When unit testing functions within `damien_cli/core_api/rules_api_service.py` itself (like `apply_rules_to_mailbox`), you'll mock methods from `gmail_api_service.py` (e.g., `list_messages`, `get_message_details`, batch action methods).
*   **`list_messages` Side Effect**: To accurately test rule matching and scan limits, use a `side_effect` for the `list_messages` mock. This side effect should:
    *   Inspect the `query_string` argument to simulate how Gmail would filter messages based on the rule's translated query (and any global query filter).
    *   Respect the `max_results` argument to simulate batching and `scan_limit` behavior.
*   **`does_email_match_rule` and `transform_gmail_message_to_matchable_data`**: These may also need to be mocked or have their behavior simulated depending on whether you're testing the server-side query path or the client-side detailed matching path within `apply_rules_to_mailbox`.
*   **Testing Scenarios**: Ensure tests cover cases like:
    *   Rules that can be fully evaluated server-side (no need for `get_message_details`).
    *   Rules requiring client-side evaluation (due to complex conditions or OR conjunctions).
    *   Dry run vs. actual execution.
    *   Correct application of `scan_limit`.
    *   Correct aggregation of actions.

## Coding Conventions

* **Formatting:** Black is used for code formatting. Consider setting up your IDE to format with Black on save.
```bash
poetry run black .
```
* **Linting:** Flake8 is used for linting.
```bash
poetry run flake8 damien_cli tests
```
* **Type Hinting:** Use Python type hints for all function signatures and important variables.
* **Docstrings:** Add docstrings to modules, classes, and functions (e.g., Google style or reStructuredText).

## Adding a New CLI Command

1. **Identify the Feature Slice:** Determine if the command fits into an existing feature (e.g., `email_management`) or needs a new one under `damien_cli/features/`.
2. **Shared Utilities**: If your command requires confirmation, use the shared `_confirm_action` function from `damien_cli.core.cli_utils`. Consider adding a `--yes` option to your command for consistency if it involves confirmations.
3. **Create/Update `commands.py`:** In the relevant feature slice, add your new Click command function(s).
2. **Create/Update `commands.py`:** In the relevant feature slice, add your new Click command function(s).
4. **Implement Logic:** Add business logic to the feature's `service.py` (if applicable) or directly call `core_api` services. Interaction with external APIs should primarily go through the `core_api` layer.
5. **Register Command:** If it's a new command group or a top-level command, register it in `damien_cli/cli_entry.py`.
5. **Add Models:** If your command handles new data structures, define Pydantic models in the feature's `models.py`.
6. **Write Unit Tests:** Create corresponding tests in the `tests/` directory.
7. **Update Documentation:** Add the new command to `docs/USER_GUIDE.md` and update `docs/ARCHITECTURE.md` if significant architectural changes are made.

## Understanding Rule Application (`apply_rules_to_mailbox`)

The `apply_rules_to_mailbox` function in `damien_cli/core_api/rules_api_service.py` is central to how Damien processes emails. It's called by the `damien rules apply` CLI command. Here's a simplified flow:
1.  **Load Rules**: Active, enabled rules are loaded. If `rule_ids_to_apply` is specified, rules are filtered accordingly.
2.  **Iterate Per Rule**: The system processes emails for each rule individually to leverage server-side filtering.
3.  **Query Generation**:
    *   `translate_rule_to_gmail_query()`: Attempts to convert the rule's conditions into an efficient Gmail query string.
    *   This rule-specific query is combined with any global `gmail_query_filter` (e.g., from user's `--query` or date options).
4.  **Fetch Candidates**: `gmail_api_service.list_messages()` is called with the combined query to get candidate email stubs. This respects `scan_limit` through batching.
5.  **Detailed Matching (if needed)**:
    *   `needs_full_message_details()`: Determines if the rule requires fetching the full email content (e.g., for body checks or complex OR conditions not perfectly translatable to a Gmail query).
    *   If not needed (rule is server-side evaluable), emails from `list_messages` are considered direct matches for that rule's query part.
    *   If details are needed, `gmail_api_service.get_message_details()` is called.
    *   `transform_gmail_message_to_matchable_data()` converts the Gmail object.
    *   `does_email_match_rule()` performs the final client-side check.
6.  **Action Aggregation**: Actions for matched emails are collected.
7.  **Execute Actions**: If not a `dry_run`, the aggregated actions (e.g., trash, add/remove label) are performed in batches using `gmail_api_service` functions.

*Note on Performance*: Be mindful that rules with conditions not translatable to efficient server-side Gmail queries (e.g., `body_snippet` checks) can lead to fetching many candidate emails if the global query filter is broad. The `scan_limit` parameter in `apply_rules_to_mailbox` (and exposed via the CLI) is crucial for managing this during development, testing, and for user control, as it limits the total number of candidates processed across all rules in a run.

## Git Workflow (Example)

* Work on feature branches (e.g., `feature/add-rule-application`).
* Make small, atomic commits.
* Open Pull Requests for review (if collaborating).
* Ensure tests pass before merging.
