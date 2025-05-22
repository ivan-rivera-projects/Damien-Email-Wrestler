**Document 2: Design Document**

**1. Introduction:**
This document describes the architectural and detailed design of Damien-CLI (Damien).

**2. System Architecture:**

*   **Core Application Type:** Python Command-Line Interface (CLI), invoked as `damien`.
*   **Key Modules (Python files/packages):**
    *   `damien_cli.py`: Main entry point, argument parsing (`Click` or `Typer` recommended for the desired command structure), command dispatching. Handles high-level commands (`analyze`, `clean`, `status`) and routes to granular command handlers.
    *   `gmail_service.py`: (Same as before)
    *   `rules_engine.py`: (Same as before, actions can include moving to "Damien Pit")
    *   `llm_interface.py`: **New Module.**
        *   Handles communication with LLM APIs (e.g., OpenAI).
        *   Takes email data and task (e.g., "classify this email content: ...").
        *   Manages LLM API key configuration (securely, e.g., via environment variables or a config file).
    *   `analysis_processor.py`: **New Module.**
        *   Takes email data and (optional) LLM classifications.
        *   Applies logic for thresholds, scoring, and preparing action plans for the `clean` command.
    *   `config_manager.py`: (Same as before, now also manages LLM API key paths/env vars, "Damien Pit" label name).
    *   `unsubscribe_handler.py`: (Same as before)
    *   `logger.py` / `logging` setup: (Same as before)
    *   `session_data_handler.py`: (Same as before, potentially used by `analyze` for large datasets before sending to LLM).
*   **Data Storage:**
    *   "Damien Pit" Label Name: Configurable, defaults to "Damien-Pit".
    *   (Other storage same as before)

*   **CLI Structure with `Click` (Conceptual):**
    ```python
    # damien_cli.py
    import click

    @click.group()
    @click.option('--config', default='~/.damien/config.ini', help='Path to config file.')
    @click.pass_context
    def cli(ctx, config):
        ctx.obj = {'CONFIG_PATH': config} # Load config, set up services

    @cli.command()
    @click.option('--llm', default='openai', help='LLM provider for analysis.')
    # ... other filter options ...
    @click.pass_context
    def analyze(ctx, llm, **filters):
        """Assesses inbox using specified filters and optional LLM."""
        click.echo(f"Damien is assessing your inbox with the wisdom of {llm}...")
        # 1. Fetch emails using gmail_service based on filters
        # 2. If llm specified, pass data to llm_interface
        # 3. Process results with analysis_processor
        # 4. Output summary / JSON

    @cli.command()
    @click.option('--threshold', type=float, help='Confidence threshold for action.')
    @click.option('--source-analysis', type=click.Path(exists=True), help='File with analysis results.')
    @click.option('--target', type=click.Choice(['trash', 'pit']), default='pit', help='Target for cleaned emails.')
    @click.option('--dry-run', is_flag=True, help="Show what would be done.")
    @click.pass_context
    def clean(ctx, threshold, source_analysis, target, dry_run):
        """Cleans emails based on analysis and threshold."""
        click.echo("Damien is preparing to strike...")
        # 1. Load analysis (from file, or run implicitly)
        # 2. Use analysis_processor to determine actions based on threshold
        # 3. Use gmail_service to move emails to target ('Damien Pit' label or Trash)
        # 4. Output summary

    @cli.command()
    @click.pass_context
    def status(ctx):
        """Shows Damien's current status and last activity."""
        # Fetch log summary, count in "Damien Pit"
        click.echo("Damien is vigilant. Last cleanup: ...")

    # Granular commands (could be nested under `damien emails ...`, `damien rules ...`)
    @cli.group()
    def emails():
        """Manage individual emails."""
        pass

    @emails.command("list")
    # ... options ...
    def emails_list(**options):
        """List emails with granular filters."""
        # Calls gmail_service, outputs JSON or human-readable
        pass
    # ... other granular email commands: get, trash, delete, label, mark, unsubscribe

    @cli.group()
    def rules():
        """Manage persistent filtering rules."""
        pass

    @rules.command("add")
    # ... options ...
    def rules_add(**options):
        """Add a new rule."""
        pass
    # ... other rule commands: list, delete, apply
    ```

**3. Detailed Module Design (Additions/Changes):**

*   **`llm_interface.py`:**
    *   `get_llm_client(provider_name)`: Factory for LLM clients (e.g., OpenAI).
    *   `classify_emails_batch(emails_data_list, prompt_template, provider_name)`: Sends batch data to LLM for classification, handles API limits, returns structured results (e.g., email_id, spam_score, category).
    *   Securely loads API keys (e.g., `config_manager`).

*   **`analysis_processor.py`:**
    *   `process_llm_results(llm_outputs)`: Standardizes LLM outputs.
    *   `apply_threshold(analyzed_emails, threshold, action_if_met, action_if_not_met)`: Determines actions based on scores.
    *   This module bridges the raw output from an LLM (or rule engine) to actionable steps for `damien clean`.

**4. Data Flow (High-Level `damien clean --threshold 0.9`):**
1.  Damien CLI (`damien_cli.py`): Parses `clean` command.
2.  If no `source-analysis` provided, it might trigger an internal `analyze` step first:
    *   `gmail_service`: Fetches candidate emails.
    *   `llm_interface`: Sends email data to configured LLM.
    *   `analysis_processor`: Gets scores/classifications.
3.  Or, loads `source-analysis` if provided.
4.  `analysis_processor`: Applies `threshold (0.9)` to the analysis data to create two lists: e.g., `to_pit_ids`, `to_trash_ids`.
5.  If not `--dry-run`:
    *   `gmail_service`: Batch moves emails in `to_pit_ids` to "Damien Pit" label.
    *   `gmail_service`: Batch moves emails in `to_trash_ids` to Trash.
6.  Damien CLI: Outputs summary ("Quarantined X emails... Trashed Y emails...").
7.  `logger`: Records actions.

