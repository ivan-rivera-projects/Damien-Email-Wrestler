# Damien-CLI: `rules apply` End-to-End (E2E) Testing Checklist

This checklist outlines the steps and considerations for performing thorough manual End-to-End (E2E) testing of the `damien rules apply` command.

## I. Pre-Test Setup

*   [ ] **Latest Code:**
    *   Ensure you have the absolute latest version of the code checked out.
    *   Target commit: `513cfc5` (or later if applicable).
    *   Run `git pull` to be sure.
    *   Verify `git status` shows a clean working directory on the `main` branch.

*   [ ] **Clean `data/` Directory (Optional but Recommended for a Fresh Start):**
    *   [ ] **`data/token.json`**: Consider deleting this file to force a fresh OAuth login to your **TEST** Gmail account. This ensures the authentication flow is tested.
        *   Command: `rm data/token.json` (if you choose to delete)
    *   [ ] **`data/rules.json`**:
        *   Consider deleting to start with a clean slate for rules: `rm data/rules.json`
        *   Alternatively, ensure it only contains the specific rules you intend to use for the E2E tests. You can manually edit this file or use `damien rules delete` for existing rules.
    *   [ ] **`data/damien_session.log`**:
        *   Can be deleted for a fresh log: `rm data/damien_session.log`
        *   Alternatively, allow the application to append to the existing log.

*   [ ] **Test Gmail Account Preparation:**
    *   [ ] **Verify Account:** Double-check you are operating on your designated **TEST** Gmail account. **CRITICAL: DO NOT USE YOUR PRIMARY OR PRODUCTION GMAIL ACCOUNT.**
    *   [ ] **Prepare Emails:** Have a variety of emails ready in the test account that align with your E2E test plan scenarios. This includes:
        *   Emails that *should* match specific test rules.
        *   Emails that *should NOT* match any test rules.
        *   Emails from different senders.
        *   Emails with different subjects.
        *   Emails in various read/unread states.
        *   Emails with some manually pre-applied labels (to test label addition/removal without conflicts if applicable).
    *   [ ] **Create Labels in Gmail:** Manually create any labels in your test Gmail account that your test rules will attempt to add (e.g., "TestLabelForArchive", "ImportantProject"). While `gmail_api_service.py` should handle resolving label names to IDs (and potentially creating them if `get_label_id` is enhanced to do so, though currently it doesn't create), it's good practice for the target labels to exist for E2E testing of application logic.

*   [ ] **Rule Definition Files:**
    *   Have your sample `.json` rule files ready (e.g., the sanitized versions of `rule_trash_subject.json`, `rule_add_label_from.json`, etc., that we prepared).
    *   You will use `damien rules add --rule-json <path_to_rule_file.json>` to add these rules before testing `rules apply`.

## II. Execution Guidance

*   [ ] **Patience and Observation:** E2E testing is about observing the real behavior of the integrated system. Take your time with each test case.
*   [ ] **Monitor Key Areas:**
    *   **CLI Output:** Carefully observe the human-readable output from `damien rules apply`. For at least one complex scenario, also test with `--output-format json` and inspect the JSON structure.
    *   **Gmail Account Changes:** After each `damien rules apply` command (especially non-dry-run):
        *   Verify in your test Gmail account that emails were correctly labeled, trashed, marked read/unread, etc., according to the rules and command options.
        *   Verify that emails *not* supposed to be affected remain untouched.
    *   **`data/damien_session.log`:** Keep an eye on this log file. It can provide valuable insights or error details if something unexpected happens. Increase verbosity with `-v` if needed.
    *   **`data/rules.json`:** After adding rules, you can inspect this file to see how they are stored.

## III. Execute E2E Test Plan

*   [ ] **Execute the manual E2E test plan for `damien rules apply` methodically.**
    *   This refers to the previously discussed Scenarios 1 through 9, covering:
        *   Scenario 1: Basic Dry Run (All enabled rules)
        *   Scenario 2: Basic Actual Run (All enabled rules, with `--confirm`)
        *   Scenario 3: Filtering with `--query`
        *   Scenario 4: Applying Specific Rules with `--rule-ids`
        *   Scenario 5: Using `--scan-limit`
        *   Scenario 6: Date-based Filtering (`--date-after`, `--date-before`, `--all-mail` combinations)
        *   Scenario 7: JSON Output (`--output-format json`)
        *   Scenario 8: Error Handling (e.g., invalid rule ID, API issues if possible to simulate safely)
        *   Scenario 9: No Rules Defined / No Matching Rules

    *(For each scenario, document expected vs. actual outcomes, especially any discrepancies.)*

## IV. Post-Testing

*   [ ] **Review Logs:** Check `data/damien_session.log` for any errors or unexpected messages.
*   [ ] **Clean Up (Optional):**
    *   Remove test labels from your Gmail account.
    *   Move/delete test emails.
    *   Delete test rules from `data/rules.json` using `damien rules delete`.

Good luck with the E2E testing!