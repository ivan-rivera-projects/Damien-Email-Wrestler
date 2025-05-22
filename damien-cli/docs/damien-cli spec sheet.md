**Project Title:** Damien-CLI (Damien)

**Project Vision:** To create a best-in-class, Python-based CLI email management tool for Gmail, named Damien. Damien will empower users to efficiently manage, clean, and automate actions on their email, leveraging both predefined rules and dynamic, LLM-driven intelligence. It is designed for extensibility and seamless integration with Large Language Models (LLMs), offering both direct user control and programmatic access.

---

**Document 1: Specification Sheet (Functional & Non-Functional Requirements) **

**1. Introduction & Purpose:**
This document outlines the specifications for Damien-CLI (referred to as Damien), a command-line tool for managing Gmail accounts. It is designed to be used directly by users (e.g., `damien --analyze`) and programmatically by LLM-driven orchestrators (e.g., an orchestrator calling `damien emails list --json ...`).

**2. Scope:**
*   **In Scope:**
    *   Secure Gmail authentication (OAuth 2.0).
    *   Listing and retrieving email metadata and (optionally) content.
    *   Filtering emails based on user-defined criteria and LLM-driven analysis.
    *   Actions on emails: move to trash, delete permanently, add/remove labels (including a special "Damien Pit" label for quarantined items), mark as read/unread.
    *   Management of persistent filtering rules.
    *   High-level commands for common tasks (e.g., `damien analyze`, `damien clean`, `damien status`).
    *   Optional direct LLM integration (e.g., OpenAI) for analysis tasks within Damien itself, configurable by the user.
    *   "Dry run" mode for all destructive operations.
    *   Structured (JSON) output for programmatic consumption, alongside user-friendly human-readable output.
    *   Basic unsubscribe assistance.
    *   Session logging of actions performed.
    *   Handling of large email volumes.
    *   Support for dynamic rule creation/interpretation as suggested by an external LLM (via structured input).
*   **Out of Scope (Initially, can be future enhancements):**
    *   Full GUI.
    *   Support for email providers other than Gmail.
    *   Complex, built-in AI/ML models (relies on external LLMs or user rules).

**3. Functional Requirements:**

*   **FR1: Authentication:** 
    *   FR1.1: Securely authenticate with Gmail using OAuth 2.0.
    *   FR1.2: Store and refresh access/refresh tokens securely.
    *   FR1.3: Allow re-authentication if tokens are invalid.
*   **FR2: Email Retrieval & Listing (Granular Commands):**
    *   FR2.1: Command `damien emails list`: List emails matching specified criteria (sender, subject, date range, labels, read/unread status, keywords in body snippet, Gmail query string).
    *   FR2.2: Command `damien emails get`: Retrieve full details of a specific email.
    *   FR2.3: Support pagination.
    *   FR2.4: Output in human-readable and JSON formats.
*   **FR3: Email Actions (Granular Commands):**
    *   FR3.1: Command `damien emails trash`: Move specified emails to Trash.
    *   FR3.2: Command `damien emails delete`: Permanently delete specified emails.
    *   FR3.3: Command `damien emails label`: Add/remove labels, including moving to "Damien Pit" (e.g., `damien emails label --id <id> --add "Damien Pit"`).
    *   FR3.4: Command `damien emails mark`: Mark emails as read/unread.
    *   FR3.5: Support batch operations.
*   **FR4: Rule Management (Granular Commands):**
    *   FR4.1: Command `damien rules add/list/delete/apply`: Manage persistent rules.
    *   FR4.2: Rules based on attributes, actions include moving to "Damien Pit".
    *   FR4.3: Store rules persistently.
    *   FR4.4: Support interpretation of dynamically generated rules (JSON schema) from an external LLM.
*   **FR5: Unsubscribe Assistance (Granular Command):**
    *   FR5.1: Command `damien emails unsubscribe`: Identify `List-Unsubscribe` headers.
    *   FR5.2: Offer to generate/send `mailto:` unsubscribe emails.
*   **FR6: LLM Interaction & High-Level Commands:**
    *   **FR6.1 (Damien as a Tool):** All granular commands (FR2-FR5) accessible via clearly defined CLI subcommands/arguments, with JSON output for external LLM orchestrators.
    *   **FR6.2 (Damien as an Agent - Analyze):** Command `damien analyze [--llm <provider>] [--output_format <format>] [--other_filters]`:
        *   Fetches relevant emails.
        *   Optionally uses a configured LLM (e.g., OpenAI) to analyze/classify emails (e.g., spam score, sentiment, categorization).
        *   Outputs analysis results (human-readable summary and/or JSON with scores/classifications).
        *   Example: `damien analyze --llm openai` -> "Damien is assessing your inbox with the wisdom of OpenAI..."
    *   **FR6.3 (Damien as an Agent - Clean):** Command `damien clean [--threshold <value>] [--target-pit | --target-trash] [--dry-run] [--source-analysis <file_or_stdin>]`:
        *   Acts on analysis results (either from a previous `damien analyze` step, a file, or by running analysis implicitly).
        *   Uses a `--threshold` (e.g., spam score) to decide actions.
        *   Moves emails to "Damien Pit" (quarantine label) or Trash.
        *   Example: `damien clean --threshold 0.9 --target-pit` -> "Damien is preparing to strike... Quarantined 3 suspicious emails in the Damien Pit."
*   **FR7: Operational:**
    *   FR7.1: Command `damien status`: Display summary of last run, number of items in "Damien Pit", etc.
    *   FR7.2: Implement "dry run" mode (`--dry-run`).
    *   FR7.3: Log actions to a local log file and to console (with verbosity levels).
    *   FR7.4: Clear error messages.
    *   FR7.5: User-friendly status messages for long-running operations.

**4. Non-Functional Requirements:** (Largely the same, emphasizing usability for the new commands)
*   ...
*   **NFR3: Usability (CLI):**
    *   NFR3.1: Intuitive high-level commands (`analyze`, `clean`, `status`).
    *   NFR3.2: Clear, consistent granular commands (`emails list`, `rules add`).
    *   NFR3.3: Engaging and informative status messages (e.g., "Damien is assessing...").
*   ...
*   **NFR4: Reliability & Robustness:
    *   NFR4.1: Graceful handling of Gmail API errors and rate limits (e.g., implement exponential backoff).
    *   NFR4.2: Idempotent operations where possible (e.g., re-trashing an already trashed email should not cause an error).
*   **NFR5: Extensibility & Maintainability:
    *   NFR5.1: Modular code design with clear separation of concerns.
    *   NFR5.2: Code well-commented and adhering to Python best practices (PEP 8).
    *   NFR5.3: Easy to add new commands, rule conditions, or actions.
*   **NFR6: Data Handling (Large Datasets & In-Memory):
    *   NFR6.1: Leverage Gmail API's server-side filtering (q parameter) to minimize data transfer.
    *   NFR6.2: Use pagination (nextPageToken) for fetching large lists of emails.
    *   NFR6.3: For session-specific complex processing (e.g., cross-referencing data from multiple LLM-suggested queries before actioning), utilize in-memory SQLite (:memory:) or efficient Python data structures (dictionaries, sets) to handle temporary datasets. This avoids writing large temporary files to disk unnecessarily. The choice depends on the complexity of operations needed on the temporary data (SQLite for relational, Python dicts/lists for simpler lookups/iterations).