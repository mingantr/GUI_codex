# Repository Guidelines

## Project Structure & Module Organization
- `src/` – Application code (e.g., `src/main.py`, `src/ui/`, `src/widgets/`).
- `tests/` – Pytest tests mirroring `src/` (e.g., `tests/test_main.py`).
- `assets/` – Static files: icons, `.qss`, `.ui` forms.
- `scripts/` – Helper/packaging scripts (optional).
- `.venv/` – Virtual environment created by `install.bat` (ignored by Git).
- `.env` – Local config/secrets. Provide a tracked `.env.example`.

## Build, Test, and Development Commands
- Setup (Windows): `install.bat` – Creates `.venv`, upgrades `pip`, installs `requirements.txt`, prepares `.env`.
- Activate venv: `.venv\Scripts\activate` (PowerShell/CMD).
- Run app (adjust entry point): `python src/main.py` or `python -m app`.
- Run tests: `pytest -q` (from repo root).
- Lint/format (if installed): `ruff check src tests` and `black src tests`.
- Optional packaging: `pyinstaller -n AppName src/main.py`.

## Coding Style & Naming Conventions
- Python 3.9+. Follow PEP 8; 4-space indentation; UTF-8.
- Type hints required for public functions/classes.
- Names: modules `snake_case.py`, classes `PascalCase`, functions/vars `snake_case`, constants `UPPER_SNAKE`.
- UI: keep Qt Designer `.ui` files in `assets/` or `src/ui/`; generated code lives in `src/`.

## Testing Guidelines
- Framework: `pytest`. Place tests under `tests/` named `test_*.py`.
- Aim for meaningful coverage of core logic; target ≥80% where practical.
- Prefer small, focused tests; use fixtures; avoid GUI-heavy tests unless isolated.

## Commit & Pull Request Guidelines
- Use Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`.
  - Example: `feat(ui): add toolbar actions for export`.
- PRs include: summary, motivation, linked issues, test updates, and screenshots/gifs for UI changes.
- Keep diffs minimal; avoid drive-by refactors.

## Security & Configuration Tips
- Do not commit secrets. Use `.env` and document needed keys in `.env.example` (e.g., `OPENAI_API_KEY=`).
- Validate user input; never trust file paths or external data.
- Review third-party additions before updating `requirements.txt`.

## Agent-Specific Instructions
- Prefer small, surgical changes; follow this guide’s structure and naming.
- Coordinate via plans when altering many files; keep Windows-friendly commands.
- Do not introduce new dependencies or tooling without justification in the PR.

