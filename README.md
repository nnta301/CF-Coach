# CF-Coach

CF-Coach is a personalized Codeforces problem recommender for competitive programmers.

## Current status

Current sprint: [Sprint 1](docs/sprints/sprint-01.md)

## Documentation

- [Proposal](docs/proposal.md)
- [Architecture](docs/architecture.md)
- [Data contracts](docs/contracts.md)
- [Team workflow](docs/workflow.md)
- [Sprint history](docs/sprints/README.md)

## Prerequisites

- Python 3.11 or newer
- pip
- Git

## Local setup

### macOS/Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

### Windows (PowerShell)

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

## Run tests

With the virtual environment activated:

```bash
pytest
ruff check .
```
