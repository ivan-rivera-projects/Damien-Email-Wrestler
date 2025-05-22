# Damien-CLI Architecture

## Overview

Damien-CLI is a Python-based command-line interface (CLI) application built using the Click framework. It follows a feature-sliced architecture to promote modularity and maintainability.

## System Diagram

```mermaid
graph TD
    subgraph User/External_LLM_Orchestrator
        U[User via Terminal]
        ELO[External LLM Orchestrator]
    end

    subgraph Damien_CLI_Application [Damien-CLI Application]
        DC[damien_cli.cli_entry.py <br> (Click, Cmd Dispatch)]

        subgraph Core_Components [damien_cli.core]
            CONF[config.py]
            LOGS[logging_setup.py]
            CORE_EXC[core/exceptions.py]
            UTIL[utils.py (Optional)]
        end

        subgraph Core_API_Layer [damien_cli.core_api]
            GMAIL_API_SVC[gmail_api_service.py]
            RULES_API_SVC[rules_api_service.py]
            API_EXC[core_api/exceptions.py]
        end

        subgraph Feature_Slices [damien_cli.features]
            EM[email_management <br> (commands.py, models.py)]
            RM[rule_management <br> (commands.py, models.py)]
            LLMA[llm_analysis <br> (Planned)]
        end

        subgraph Integrations_Layer [damien_cli.integrations]
            GI[gmail_integration.py <br> (Gmail API Auth & Low-level Calls)]
        end

        subgraph Data_Storage_Local [Local Data (in ./data/)]
            TOK[token.json]
            RULES_JSON[rules.json]
            LOGF[damien_session.log]
        end
    end

    subgraph External_Services_APIs
        G_API[Google Gmail API]
        LLM_API_EXT[External LLM APIs <br> (Planned for Orchestrator)]
    end

    U --> DC; ELO --> DC;
    DC --> CONF; DC --> LOGS;
    DC --> EM; DC --> RM;

    EM --> GMAIL_API_SVC;
    RM --> RULES_API_SVC;

    GMAIL_API_SVC --> GI;
    GMAIL_API_SVC --> API_EXC;
    RULES_API_SVC --> RULES_JSON;
    RULES_API_SVC --> API_EXC;
    RULES_API_SVC --> GMAIL_API_SVC; # Added: Rules service uses Gmail service for fetching and actions
    
    GI --> G_API;
    GI --> TOK; # gmail_integration reads/writes token

    CONF --> TOK; CONF --> RULES_JSON; LOGS --> LOGF;
    DC --> CORE_EXC; # cli_entry might use core exceptions

    classDef user fill:#c9f,stroke:#333;
    classDef cli fill:#f9f,stroke:#333;
    classDef core fill:#ffc,stroke:#333;
    classDef core_api fill:#fcc,stroke:#333;
    classDef feature fill:#cff,stroke:#333;
    classDef integration fill:#9cf,stroke:#333;
    classDef storage fill:#lightgrey,stroke:#333;
    classDef external fill:#9f9,stroke:#333;

    class U,ELO user; class DC cli;
    class CONF,LOGS,CORE_EXC,UTIL core;
    class GMAIL_API_SVC,RULES_API_SVC,API_EXC core_api;
    class EM,RM,LLMA feature;
    class GI integration;
    class TOK,RULES_JSON,LOGF storage;
    class G_API,LLM_API_EXT external;
```

## Key Modules

* **damien_cli/cli_entry.py**: The main entry point for the CLI using Click. Defines top-level commands and registers command groups from feature slices.
* **damien_cli/core/**: Contains shared, cross-cutting concerns:
  * **config.py**: Application configuration (paths, API scopes, data file names).
  * **logging_setup.py**: Configures logging for the application.
  * **exceptions.py**: Core custom exception classes (if any, distinct from API layer exceptions).
  * **utils.py** (Optional): Common utility functions.
* **damien_cli/core_api/**: A service layer that abstracts interactions with integrations and data storage. Provides a cleaner interface for feature commands.
  * **gmail_api_service.py**: Handles business logic related to Gmail operations, using `integrations/gmail_integration.py` for raw API calls and token management.
  * **rules_api_service.py**: Handles business logic for rule storage (CRUD from `rules.json`), rule matching logic, and orchestrates the rule application process. This includes fetching emails (via `gmail_api_service.py`), performing server-side and client-side matching (e.g., using `translate_rule_to_gmail_query` and `does_email_match_rule`), and delegating email actions (like labeling or trashing) back to `gmail_api_service.py`.
  * **exceptions.py**: Custom exceptions specific to the API service layer (e.g., `RuleNotFoundError`, `GmailApiError`).
* **damien_cli/features/**: Houses the feature slices. Each slice typically contains:
  * **commands.py**: Click command definitions specific to the feature. These commands now primarily interact with services in the `core_api` layer.
  * **models.py**: Pydantic data models relevant to the feature (e.g., `RuleModel`).
* **damien_cli/integrations/**: Modules for interacting with external services.
  * **gmail_integration.py**: Lower-level wrapper for direct calls to the Google Gmail API and handles the initial OAuth 2.0 authentication flow (token creation, refresh).
* **data/**: Directory (created by the app) for storing runtime user data like `token.json`, `rules.json`, and logs. This directory is typically in .gitignore.
* **tests/**: Contains all automated tests, mirroring the application structure.

## Design Principles

* **Modularity & Separation of Concerns**: Each part of the application has a distinct responsibility.
* **Feature-Sliced Architecture**: Code is grouped by feature for easier navigation and development.
* **Testability**: Designed with unit and integration testing in mind.
* **Extensibility**: Structured to allow for new features and integrations to be added.
* **Clear CLI Interface**: Uses Click for a user-friendly command-line experience.
* **Programmatic Use**: Provides JSON output for integration with other scripts or LLM orchestrators.
