# Execution Scripts

This directory contains deterministic Python scripts — the tools that do the actual work.

## Guidelines

- Scripts should be **reliable, testable, and well-commented**.
- Each script handles a single responsibility (API call, data transform, file op, etc.).
- Read configuration from environment variables (`.env` in project root).
- Never hard-code secrets or API keys — always use `os.getenv()` or `python-dotenv`.
- Name files descriptively (e.g., `scrape_single_site.py`, `upload_to_sheets.py`).

## Dependencies

Add any Python dependencies to `requirements.txt` in the project root.
