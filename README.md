# QuizMaster

QuizMaster is a native desktop flashcard app on Tkinter.
You can paste lecture text or open PDF/DOCX/TXT files, generate cards through an LLM API, and study them in one window.

## Installation

```bash
pip install requests pdfplumber python-docx
```

## Run

```bash
python main.py
```

## Set API key

1. Open GenerateScreen.
2. Click the `⚙` button.
3. Paste your API key.
4. Click `Save`.

The key is stored in `data/config.json`.

Optional provider settings (environment variables):

- `LLM_API_URL` (OpenAI-compatible chat completions endpoint)
- `LLM_MODEL` (model name)

## API compatibility

The app works with OpenAI-compatible Chat Completions APIs.
It does not support arbitrary API formats out of the box.

Expected behavior from the provider:

- Bearer token auth (`Authorization: Bearer ...`)
- Chat Completions endpoint schema
- Response content in `choices[0].message.content`

## No internet or no API key

Open DeckScreen and use `+ Add card` to add cards manually.
The app still works for creating and studying cards without generation.

## Supported input

- PDF
- DOCX
- TXT
- Or paste text directly into the GenerateScreen textarea

## UI overview

- Generate screen: paste text or open a file, then generate cards
- Deck screen: search, review, delete, and add cards manually
- Quiz screen: MAD exam prep with spaced repetition and mock exams (see below)
- Study screen: flip-card animation and animated progress bar

## Quiz Mode (MAD — Discrete Mathematics)

The **Quiz** tab provides dedicated exam preparation for the MAD (Matematyka Dyskretna) course.

### Features

- **Learn mode** — questions sorted by mastery (weak first), with immediate feedback and spaced repetition
- **Mock Exam mode** — 20-question timed test matching the real exam topic distribution
- **Results screen** — score, weak topics, expandable wrong answers with explanations
- **Progress persistence** — mastery and streaks saved to `data/quiz_progress.json`

### Question bank

100 questions from the 2018–2023B exams covering:
`equivalence`, `partial_order`, `countable`, `combinatorics`, `logic`,
`set_algebra`, `big_o`, `probability`, `pigeonhole`, `relations`, `predicates`, `well_order`

Questions support multiple correct answers. The engine tracks mastery (0–5) and streak per question.
