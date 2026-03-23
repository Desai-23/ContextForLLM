# ContextForLLM

A local web UI that scans any project folder on your machine, lets you select and annotate files, and generates a structured prompt you can paste directly into any LLM chat — Claude, ChatGPT, Gemini, or any other.

---


## Why this exists

Every other tool in this space is a CLI that dumps your entire repo into one file. ContextForLLM gives you a browser UI where you can:

- Toggle individual files in or out
- Add a note to any file that gets embedded into the prompt
- Generate an AI summary of your project using Groq
- Automatically split large projects into sequenced prompt parts
- Set your task so the LLM knows exactly what to do

---

## Demo

> Screenshot / GIF coming soon

---

## Installation

You need Python 3.8 or higher installed.

**Step 1 — Clone the repo**
```bash
git clone https://github.com/Desai-23/ContextForLLM.git
cd ContextForLLM
```

**Step 2 — Install dependencies**
```bash
pip install -r requirements.txt
```

**Step 3 — Run the app**
```bash
python app.py
```

Then open your browser at:
```
http://localhost:5000
```

---

## How to use it

1. Paste the path to any project folder on your machine
2. Click Scan
3. Review the files — toggle any file off to exclude it from the prompt
4. Add annotations to files if needed (the LLM will see these notes)
5. Optionally generate an AI summary of your project using Groq
6. Set your task — what you want the LLM to do
7. Click Generate Context Prompt
8. Copy the prompt and paste it into any LLM chat

---

## Features

- Local — your code never leaves your machine
- Browser UI — no terminal required after launch
- Per-file exclusion — toggle files in or out with a switch
- Per-file annotations — add notes that get embedded into the prompt
- Token counter — live token count with a visual usage bar
- Prompt splitting — large projects automatically split into sequenced parts with handoff instructions
- AI project summary — uses Groq to generate a project summary injected at the top of every prompt
- .contextignore support — create a .contextignore file in any project to permanently exclude files

---

## .contextignore

Create a `.contextignore` file in any project folder to exclude files automatically on scan. Uses the same pattern syntax as `.gitignore`.

Example:
```
*.test.js
migrations/
old_auth.py
```

---

## Groq API key

The AI summary feature requires a free Groq API key.

1. Get a free key at console.groq.com
2. Click "Add Groq Key" in the top right of the UI
3. Paste your key — it is held in memory only and never saved to disk

---

## Tech stack

- Python / Flask — backend server
- Vanilla HTML, CSS, JS — frontend UI
- tiktoken — token counting
- Groq — AI project summary (optional)

---

## License

MIT
