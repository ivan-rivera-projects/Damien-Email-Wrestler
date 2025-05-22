**Document 4: Action Item Checklist & Program Timeline**

**Project Name:** Damien-CLI (Damien)

**Phase 0: Setup & Foundation (Est. 1-2 weeks)**
*   ... (same, but project named Damien)
*   [ ] **A0.7:** Choose and set up CLI framework (`Click` or `Typer`).

**Phase 1: Core Email Read Operations (Est. 2-3 weeks)**
*   ... (granular `damien emails list/get` commands)

**Phase 2: Core Email Write Operations & Basic Rules (Est. 3-4 weeks)**
*   ... (granular `damien emails trash/delete/label/mark`, `damien rules add/list/apply`)
*   [ ] **A2.7:** Implement "Damien Pit" as a configurable label for actions.

**Phase 3: High-Level Commands & LLM Integration (Est. 5-7 weeks)** - *This phase expands significantly*
*   [ ] **A3.1:** Design and implement `llm_interface.py` (start with one provider like OpenAI).
    *   [ ] Secure LLM API key management.
*   [ ] **A3.2:** Design and implement `analysis_processor.py`.
*   [ ] **A3.3:** Implement `damien analyze` command:
    *   Integrate `gmail_service` for fetching.
    *   Integrate `llm_interface` for optional LLM calls.
    *   Integrate `analysis_processor` for result handling.
    *   User-friendly output.
*   [ ] **A3.4:** Implement `damien clean` command:
    *   Ability to use analysis from `analyze` step or file.
    *   Threshold logic.
    *   Integration with `gmail_service` for actions (Trash, "Damien Pit").
    *   `--dry-run` flag.
*   [ ] **A3.5:** Implement `damien status` command.
*   [ ] **A3.6:** Implement `damien emails unsubscribe` command.
*   [ ] **A3.7:** Refine JSON output of all commands for robustness (if external LLM orchestrator still a primary use case).
*   [ ] **A3.8:** Unit tests for new modules and high-level commands.

**Phase 4: Polish, Testing & Documentation (Est. 2-3 weeks)**
*   ... (same)
