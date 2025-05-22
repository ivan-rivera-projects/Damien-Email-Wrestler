**Project Title:** Damien-CLI (Damien)

**Project Vision:** To create a best-in-class, Python-based CLI email management tool for Gmail, designed for extensibility and seamless integration with Large Language Models (LLMs). IMA will empower users to efficiently manage, clean, and automate actions on their email, leveraging both predefined rules and dynamic, LLM-driven intelligence.

---

**Document 1: Specification Sheet (Functional & Non-Functional Requirements)**

**1. Introduction & Purpose:**
This document outlines the specifications for IntelliMail Assistant (IMA), a command-line tool for managing Gmail accounts. It is designed to be used directly by users and programmatically by LLM-driven orchestrators.

**2. Scope:**
*   **In Scope:**
    *   Secure Gmail authentication (OAuth 2.0).
    *   Listing and retrieving email metadata and (optionally) content.
    *   Filtering emails based on user-defined criteria (sender, recipient, subject, date, labels, content snippets).
    *   Actions on emails: move to trash, delete permanently, add/remove labels, mark as read/unread.
    *   Management of persistent filtering rules.
    *   "Dry run" mode for all destructive operations.
    *   Structured (JSON) output for programmatic consumption.
    *   Human-readable output for direct CLI use.
    *   Basic unsubscribe assistance (identifying List-Unsubscribe headers, composing `mailto:` unsubs).
    *   Session logging of actions performed.
    *   Handling of large email volumes through pagination and batching.
    *   Support for dynamic rule creation/interpretation as suggested by an LLM (via structured input).
*   **Out of Scope (Initially, can be future enhancements):**
    *   Directly interacting with `http/https` unsubscribe links (security/complexity).
    *   Full GUI.
    *   Support for email providers other than Gmail.
    *   Real-time, continuous monitoring (initially event-driven/scheduled).
    *   Complex AI-driven email categorization beyond LLM-provided rules.

**3. Functional Requirements:**

*   **FR1: Authentication:**
    *   FR1.1: Securely authenticate with Gmail using OAuth 2.0.
    *   FR1.2: Store and refresh access/refresh tokens securely.
    *   FR1.3: Allow re-authentication if tokens are invalid.
*   **FR2: Email Retrieval & Listing:**
    *   FR2.1: List emails matching specified criteria (sender, subject, date range, labels, read/unread status, keywords in body snippet).
    *   FR2.2: Retrieve full details of a specific email (headers, body).
    *   FR2.3: Support pagination for large result sets.
    *   FR2.4: Display results in human-readable and JSON formats.
*   **FR3: Email Actions:**
    *   FR3.1: Move specified emails to Trash.
    *   FR3.2: Permanently delete specified emails (with strong warnings/confirmation).
    *   FR3.3: Mark emails as read/unread.
    *   FR3.4: Add/remove labels to/from emails.
    *   FR3.5: Support batch operations for actions on multiple emails.
*   **FR4: Rule Management:**
    *   FR4.1: Define rules based on email attributes (sender, subject, body content, etc.) and desired actions (trash, label, etc.).
    *   FR4.2: Store rules persistently (e.g., JSON file).
    *   FR4.3: List, add, modify, delete rules.
    *   FR4.4: Apply stored rules to emails.
    *   FR4.5: Support interpretation of dynamically generated rules (in a predefined JSON schema) provided by an LLM.
*   **FR5: Unsubscribe Assistance:**
    *   FR5.1: Identify `List-Unsubscribe` headers in emails.
    *   FR5.2: For `mailto:` unsubscribe links, offer to generate/send an unsubscribe email.
    *   FR5.3: (Optional) Log unsubscribe attempts.
*   **FR6: LLM Interaction Support:**
    *   FR6.1: All core functionalities accessible via clearly defined CLI subcommands and arguments.
    *   FR6.2: All CLI output available in a well-structured JSON format, including success/error status and data.
    *   FR6.3: Accept complex rule definitions in a structured format (e.g., JSON) that an LLM can generate.
*   **FR7: Operational:**
    *   FR7.1: Implement a "dry run" mode for all actions that modify or delete data, showing what would happen.
    *   FR7.2: Log all significant actions (e.g., emails deleted, rules applied) with timestamps to a local log file.
    *   FR7.3: Provide clear error messages for both human and programmatic consumption.

**4. Non-Functional Requirements:**

*   **NFR1: Performance:**
    *   NFR1.1: Respond to simple CLI commands within 2 seconds (excluding network latency to Google).
    *   NFR1.2: Process batches of up to 100 emails for deletion/modification within an acceptable timeframe (e.g., < 30 seconds, subject to Gmail API limits).
    *   NFR1.3: Efficiently handle mailboxes with 100,000+ emails when filtering using Gmail API's `q` parameter.
*   **NFR2: Security:**
    *   NFR2.1: OAuth tokens must be stored securely with appropriate file permissions.
    *   NFR2.2: No hardcoded credentials.
    *   NFR2.3: Input validation, especially for rule definitions from any source. Avoid `eval()` of arbitrary code.
*   **NFR3: Usability (CLI):**
    *   NFR3.1: Consistent command structure.
    *   NFR3.2: Clear help messages (`--help`).
    *   NFR3.3: Informative progress indicators for long-running operations.
*   **NFR4: Reliability & Robustness:**
    *   NFR4.1: Graceful handling of Gmail API errors and rate limits (e.g., implement exponential backoff).
    *   NFR4.2: Idempotent operations where possible (e.g., re-trashing an already trashed email should not cause an error).
*   **NFR5: Extensibility & Maintainability:**
    *   NFR5.1: Modular code design with clear separation of concerns.
    *   NFR5.2: Code well-commented and adhering to Python best practices (PEP 8).
    *   NFR5.3: Easy to add new commands, rule conditions, or actions.
*   **NFR6: Data Handling (Large Datasets & In-Memory):**
    *   NFR6.1: Leverage Gmail API's server-side filtering (`q` parameter) to minimize data transfer.
    *   NFR6.2: Use pagination (`nextPageToken`) for fetching large lists of emails.
    *   NFR6.3: For session-specific complex processing (e.g., cross-referencing data from multiple LLM-suggested queries before actioning), utilize in-memory SQLite (`:memory:`) or efficient Python data structures (dictionaries, sets) to handle temporary datasets. This avoids writing large temporary files to disk unnecessarily. The choice depends on the complexity of operations needed on the temporary data (SQLite for relational, Python dicts/lists for simpler lookups/iterations).

---

**Document 2: Design Document**

**1. Introduction:**
This document describes the architectural and detailed design of IntelliMail Assistant (IMA).

**2. System Architecture:**

*   **Core Application Type:** Python Command-Line Interface (CLI).
*   **Primary Interaction Model:**
    1.  Direct user via terminal.
    2.  Programmatic via an LLM Orchestrator (separate process/application) that invokes the IMA CLI and parses its JSON output.
*   **Key Modules (Python files/packages):**
    *   `ima_cli.py`: Main entry point, argument parsing (`argparse`, `Click`, or `Typer`), command dispatching, output formatting (human/JSON).
    *   `gmail_service.py`: All Gmail API interactions (authentication, fetching, modifying emails, batching, error handling, rate limit management).
    *   `rules_engine.py`: Loading, saving, validating, and applying filtering rules. Interprets both static rules from config and dynamic rules (JSON schema) from LLM.
    *   `config_manager.py`: Manages application configuration (API keys paths, rule file paths, logging settings).
    *   `unsubscribe_handler.py`: Logic for identifying and processing unsubscribe requests.
    *   `logger.py` (or use built-in `logging` configured in `ima_cli.py`): Handles structured logging of operations.
    *   `(Optional) session_data_handler.py`: If complex in-memory processing is needed for a session, this module would manage an in-memory SQLite DB or advanced Python data structures for temporary email data.

*   **Data Storage:**
    *   `credentials.json`: Google Cloud client secrets (user-provided).
    *   `token.json`: OAuth 2.0 user tokens (generated, stored securely).
    *   `rules.json` (or similar): User-defined persistent rules.
    *   `ima_session.log`: Session activity log.

*   **Data Flow (LLM Interaction Example - Deleting emails based on LLM suggestion):**
    1.  User (to LLM Orchestrator): "Delete all emails from 'spam@example.com' received last week."
    2.  LLM Orchestrator -> LLM: User query + IMA tool definitions.
    3.  LLM -> LLM Orchestrator: "Call IMA `emails list` with `sender='spam@example.com'`, `date_after='YYYY-MM-DD'`, `date_before='YYYY-MM-DD'`, `output_format='json'`."
    4.  LLM Orchestrator: Executes `python ima_cli.py emails list --sender "spam@example.com" ... --output_format json`.
    5.  IMA CLI: `ima_cli.py` parses args, calls `gmail_service.py` to fetch emails.
    6.  `gmail_service.py`: Interacts with Gmail API, returns data.
    7.  IMA CLI: Formats result as JSON, prints to `stdout`.
    8.  LLM Orchestrator: Parses JSON, sends email list to LLM.
    9.  LLM -> LLM Orchestrator: "Confirm with user. If yes, call IMA `emails trash` with `ids=['id1', 'id2', ...]` and `output_format='json'`."
    10. LLM Orchestrator: Confirms with user. If yes, executes `python ima_cli.py emails trash --ids "id1,id2" ... --output_format json`.
    11. IMA CLI: Calls `gmail_service.py` to batch-trash emails.
    12. `gmail_service.py`: Interacts with Gmail API.
    13. IMA CLI: Formats success/error JSON to `stdout`.
    14. LLM Orchestrator: Parses JSON, informs LLM.
    15. LLM -> LLM Orchestrator: "Successfully trashed X emails."
    16. LLM Orchestrator: Informs user.

**3. Detailed Module Design:**

*   **`ima_cli.py`:**
    *   Use `argparse` (or `Click`/`Typer` for more complex CLIs) for defining subcommands (e.g., `auth`, `emails`, `rules`).
    *   Each subcommand maps to functions in other modules.
    *   Handles `--output_format` (human/json) and `--dry-run` global flags.
    *   Top-level error handling and JSON response wrapping.

*   **`gmail_service.py`:**
    *   `get_credentials()`: Manages OAuth flow, token storage/refresh.
    *   `build_service()`: Returns an authenticated Gmail API service object.
    *   `list_messages(query, page_token=None, max_results=100)`: Fetches message stubs. Implements Gmail API `q` parameter. Handles pagination.
    *   `get_message_details(message_id, format='metadata'|'full'|'raw')`: Fetches specific message.
    *   `batch_modify_messages(message_ids, add_labels=None, remove_labels=None, action='trash'|'delete'|'mark_read'|'mark_unread')`: Uses Gmail API batching for efficiency.
    *   Internal helpers for API call retries with exponential backoff.

*   **`rules_engine.py`:**
    *   `Rule` class/dataclass: Represents a single rule (conditions, action, conjunction `AND/OR`).
        *   Conditions: `{"field": "from", "operator": "contains", "value": "..."}`
        *   Action: `{"type": "trash"}` or `{"type": "add_label", "label_name": "..."}`
    *   `load_rules(filepath)`: Loads rules from `rules.json`.
    *   `save_rules(rules, filepath)`: Saves rules.
    *   `validate_rule(rule_dict)`: Ensures rule schema is correct.
    *   `match_email(email_details_dict, rule)`: Checks if an email matches a rule.
    *   `apply_rules_to_emails(email_ids_or_details_list, rules_list)`: Iterates emails, applies matching rules, collects actions to be performed. Relies on `gmail_service` to execute actions.

*   **`config_manager.py`:**
    *   Loads paths and settings from a config file or environment variables.

*   **`unsubscribe_handler.py`:**
    *   `find_unsubscribe_links(email_message_object)`: Parses `List-Unsubscribe` header. Returns list of `mailto:` and `http` links.
    *   `generate_unsubscribe_email(mailto_link, original_sender)`: Creates a draft unsubscribe email. (Actual sending via `gmail_service`).

*   **`session_data_handler.py` (For advanced in-memory processing):**
    *   `init_session_db()`: Creates an in-memory SQLite database.
    *   `load_emails_to_db(email_list)`: Populates DB with key email metadata for querying.
    *   `query_session_db(sql_query)`: Executes queries against the in-memory DB.
    *   This is useful if an LLM generates a multi-step plan: "1. Find all emails from X. 2. From those, find ones with subject Y. 3. From *that* subset, find those older than Z. Then delete." Instead of multiple API calls, one larger API call could fetch relevant data, load to in-memory DB, and then these refinements happen locally and quickly.

**4. Dynamic Rule Interpretation by LLM:**
*   LLM will be instructed to generate rule definitions in a specific JSON schema that `rules_engine.py` can parse.
    ```json
    // Example LLM-generated rule for IMA
    {
      "description": "LLM suggested: Delete old promotional emails from 'shop@example.com'",
      "conditions": [
        {"field": "from", "operator": "contains", "value": "shop@example.com"},
        {"field": "subject", "operator": "contains_any", "value": ["promo", "sale", "discount"]}, // New operator
        {"field": "date", "operator": "older_than", "value": "90d"} // e.g., 90 days
      ],
      "condition_logic": "AND",
      "action": {"type": "trash"}
    }
    ```
*   `rules_engine.py` will need to be robust in parsing these and supporting a rich set of operators.

**5. Dealing with Large Datasets:**
*   Primarily rely on Gmail API's `q` parameter for server-side filtering.
*   Use pagination for all list operations.
*   Use batch API calls for modifications (up to 100 IDs per batch call).
*   For complex, multi-stage filtering not easily expressed in a single `q` parameter, fetch a broader superset (still using `q`), then use in-memory processing (Python data structures or SQLite in-memory) for further refinement.
    *   Example: LLM wants emails "from X or Y, containing Z, but not if they are also from W unless subject is Q". This can get complex for a single `q`.

---

**Document 3: Other Preliminary Documentation (Best Practices Snippets)**

*   **A. Coding Standards:**
    *   PEP 8 for all Python code.
    *   Use `black` for code formatting, `flake8` or `pylint` for linting.
    *   Type hinting (`typing` module) for improved code clarity and static analysis.
*   **B. Version Control:**
    *   Git repository (e.g., on GitHub, GitLab).
    *   Branching strategy (e.g., `main`, `develop`, feature branches `feature/FRX-description`).
    *   Commit messages should be conventional (e.g., Conventional Commits).
*   **C. Testing Strategy:**
    *   **Unit Tests:** Use `unittest` or `pytest`. Mock Gmail API interactions (`unittest.mock`). Test individual functions in `rules_engine.py`, `gmail_service.py` (excluding actual API calls for unit tests), etc.
    *   **Integration Tests:** Test interaction between modules. E.g., does `ima_cli.py` correctly call `gmail_service.py` and parse its output? These might involve limited, controlled calls to a real test Gmail account.
    *   **End-to-End (E2E) Tests (Manual initially):** Test the full CLI flow against a dedicated test Gmail account.
*   **D. Dependency Management:**
    *   `pyproject.toml` with Poetry or PDM. Alternatively, `requirements.txt` managed with `pip-tools`.
*   **E. Security Considerations (Reiteration & Emphasis):**
    *   **OAuth Token Security:** `token.json` must have restricted file permissions (e.g., `600`). Add to `.gitignore`.
    *   **Input Validation:** Sanitize and validate all inputs, especially those that form Gmail API queries or rule definitions (even if from an LLM).
    *   **No Arbitrary Code Execution:** Never use `eval()` or similar on strings from external sources (including LLM outputs). LLM outputs structured data (JSON), which is then *interpreted* by IMA code.
    *   **Principle of Least Privilege:** Request only necessary Gmail API scopes.
    *   **Unsubscribe Caution:** Be very careful with automating unsubscribe actions, especially for HTTP links. `mailto:` is safer. Always require user confirmation for actions suggested by the LLM that modify data.
*   **F. Documentation:**
    *   Inline code comments for complex logic.
    *   Docstrings for all modules, classes, and functions.
    *   `README.md` with setup, usage instructions, examples.
    *   `CONTRIBUTING.md` if collaboration is expected.
    *   This design document and spec sheet to be kept updated.

---

**Document 4: Action Item Checklist & Program Timeline (High-Level)**

**Phase 0: Setup & Foundation (Est. 1-2 weeks)**
*   [ ] **A0.1:** Set up Google Cloud Project, enable Gmail API, obtain `credentials.json`.
*   [ ] **A0.2:** Initialize Git repository.
*   [ ] **A0.3:** Set up Python project structure (folders, `pyproject.toml` or `requirements.txt`).
*   [ ] **A0.4:** Implement basic CLI structure with `argparse`/`Click` (`ima_cli.py`).
*   [ ] **A0.5:** Implement core authentication (`gmail_service.py` - `get_credentials`, `build_service`).
    *   [ ] Test: Login and store `token.json`.
*   [ ] **A0.6:** Implement basic logging setup.

**Phase 1: Core Email Read Operations (Est. 2-3 weeks)**
*   [ ] **A1.1:** Implement `gmail_service.py::list_messages` (with `q` param, pagination).
*   [ ] **A1.2:** Implement `gmail_service.py::get_message_details`.
*   [ ] **A1.3:** Implement `ima_cli.py` commands: `emails list`, `emails get [--id <id>]`.
    *   [ ] Support `--output_format json` and human-readable.
*   [ ] **A1.4:** Write unit tests for email retrieval logic (mocking API calls).
*   [ ] **A1.5:** Basic manual E2E testing of list/get commands.

**Phase 2: Core Email Write Operations & Basic Rules (Est. 3-4 weeks)**
*   [ ] **A2.1:** Implement `gmail_service.py::batch_modify_messages` (for trash, delete, labels, read/unread).
*   [ ] **A2.2:** Implement `ima_cli.py` commands: `emails trash`, `emails delete`, `emails label`, `emails mark`.
    *   [ ] Implement `--dry-run` for all write operations.
    *   [ ] Implement confirmation prompts for destructive actions.
*   [ ] **A2.3:** Basic `rules_engine.py`:
    *   [ ] Define `Rule` structure.
    *   [ ] `load_rules`/`save_rules` (simple JSON for now).
    *   [ ] `match_email` for basic conditions (sender, subject).
    *   [ ] `apply_rules_to_emails` (integrates with `gmail_service` for actions).
*   [ ] **A2.4:** `ima_cli.py` commands: `rules add`, `rules list`, `rules apply`.
*   [ ] **A2.5:** Unit tests for modification and rule logic.
*   [ ] **A2.6:** Manual E2E testing of write operations and rules.

**Phase 3: LLM Integration & Advanced Features (Est. 4-6 weeks)**
*   [ ] **A3.1:** Refine JSON output of all CLI commands for robustness and LLM consumption.
*   [ ] **A3.2:** (External to IMA) Develop a basic LLM orchestrator prototype that can:
    *   Define IMA commands as "tools" for the LLM.
    *   Translate LLM function calls into IMA CLI commands.
    *   Execute IMA CLI commands and parse JSON output.
    *   Send results back to LLM.
*   [ ] **A3.3:** Enhance `rules_engine.py` to parse complex, LLM-generated rule JSON (more operators, `condition_logic`).
    *   [ ] `ima_cli.py` to accept a `--rule-json <json_string_or_filepath>` for dynamic rules.
*   [ ] **A3.4:** Implement `unsubscribe_handler.py` for `List-Unsubscribe` (focus on `mailto:`).
    *   [ ] `ima_cli.py` command: `emails unsubscribe --id <id>`.
*   [ ] **A3.5:** Implement in-memory data handling (`session_data_handler.py` with SQLite or advanced dicts) if initial tests show need for complex local data manipulation on large, fetched batches.
*   [ ] **A3.6:** Integration testing between LLM orchestrator and IMA.
*   [ ] **A3.7:** Improve error handling and reporting for LLM understanding.

**Phase 4: Polish, Testing & Documentation (Est. 2-3 weeks)**
*   [ ] **A4.1:** Comprehensive review of all code for quality, security, and performance.
*   [ ] **A4.2:** Expand unit and integration test coverage.
*   [ ] **A4.3:** Thorough E2E testing with LLM orchestrator.
*   [ ] **A4.4:** Write detailed `README.md` and user documentation.
*   [ ] **A4.5:** Package for distribution (e.g., PyPI).

**Total Estimated Timeline:** Approx. 12-18 weeks (This is a rough estimate for one developer working diligently; can be faster or slower based on complexity encountered and dedicated time). Iterative development is key; early phases provide usable functionality sooner.

---

This set of documents provides a strong foundation. We can dive into any specific part for more detail. The design explicitly considers your requirements for handling large datasets, dynamic LLM-driven rules, unsubscribe functionality, and session logging, aiming for that "best-in-class" feel.