# GIS_langchain

GitHub issue summarizer and PR analyzer built with LangChain, for learning purposes.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add your OPENROUTER_API_KEY
```

## Usage

```bash
python main.py issue <user> <repo> <number>
python main.py pr <user> <repo> <number>
```

Examples:

```bash
python main.py issue langchain-ai langchain 38950
python main.py pr langchain-ai langchain 1000
```

The CLI fetches the issue or PR from the GitHub API, builds a prompt, sends it to
a model via OpenRouter, and prints the structured result (pydantic).

## Structure

- `main.py` — CLI entry point and LCEL chains
- `github_api.py` — GitHub API fetching with retries
- `prompts.py` — prompt templates
- `model.py` — model setup and programmatic API
- `schemas.py` — pydantic output schemas
- `exceptions.py` — custom exceptions

## Tests

```bash
pytest
```
