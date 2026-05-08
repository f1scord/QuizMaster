# Flashcards AI

A simple desktop app that uses AI to generate flashcards from your lecture notes.
Paste any text or open a PDF/DOCX/TXT file, and the app creates study cards for you.

## Installation

```bash
pip install customtkinter requests
# optional — for file support:
pip install pdfplumber python-docx
```

## Run

```bash
python main.py
```

## How to use

1. **Set API key** — click the 🔑 key button and paste your OpenAI-compatible API key
2. **Paste text or open file** — use the text area or 📂 open file button
3. **Generate** — click ✨ generate and wait for AI to create cards
4. **Deck** — browse, search and delete cards
5. **Study** — review cards by flipping them and marking if you knew the answer

## API compatibility

Works with any OpenAI-compatible Chat Completions API.
Set `LLM_API_URL` or `LLM_MODEL` environment variables to use other providers.

## Files

- `main.py` — entry point
- `app.py` — main window and navigation
- `screens.py` — all UI screens (generate, deck, study)
- `deck.py` — flashcard and deck classes
- `agent.py` — AI API communication
- `parser.py` — file reading (pdf, docx, txt)
- `storage.py` — save/load deck and config
- `decorators.py` — custom decorators
- `exceptions.py` — custom exceptions
