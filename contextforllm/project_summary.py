import os
from groq import Groq

SUMMARY_MODEL = "llama-3.3-70b-versatile"

def get_client(api_key):
    if not api_key:
        raise ValueError("No Groq API key provided")
    return Groq(api_key=api_key)

def build_condensed_context(files, max_chars_per_file=800):
    lines = []
    for path, content in files:
        lines.append(f"\n--- FILE: {path} ---")
        preview = content[:max_chars_per_file]
        if len(content) > max_chars_per_file:
            preview += "\n... (truncated)"
        lines.append(preview)
    return "\n".join(lines)

def generate_project_summary(project_name, files, api_key):
    client = get_client(api_key)
    condensed = build_condensed_context(files)
    prompt = f"""You are analyzing a software project called '{project_name}'.

Here is a condensed view of the project files:

{condensed}

Write a concise project summary with exactly these sections:

**What this project does:**
One or two sentences describing what the project is and what problem it solves.

**Tech stack:**
List the main languages, frameworks, and libraries used.

**Main files:**
A short description of what each key file does. One line per file.

**Notes for the LLM:**
Any important things an LLM should know before working on this codebase — conventions, patterns, or things to be careful about.

Keep the entire summary under 300 words. Be specific and factual. Do not make things up."""

    response = client.chat.completions.create(
        model=SUMMARY_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a technical assistant that writes clear, accurate project summaries for developers."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3,
        max_tokens=600
    )
    return response.choices[0].message.content.strip()

# ── Summary storage ────────────────────────────────────────────
def get_summary_path(tool_dir, project_path):
    import hashlib
    summaries_dir = os.path.join(tool_dir, "summaries")
    os.makedirs(summaries_dir, exist_ok=True)
    path_hash = hashlib.md5(project_path.encode()).hexdigest()
    return os.path.join(summaries_dir, f"{path_hash}.txt")

def save_summary(tool_dir, project_path, summary):
    summary_path = get_summary_path(tool_dir, project_path)
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary)

def load_summary(tool_dir, project_path):
    summary_path = get_summary_path(tool_dir, project_path)
    if os.path.isfile(summary_path):
        with open(summary_path, "r", encoding="utf-8") as f:
            return f.read()
    return None

def delete_summary(tool_dir, project_path):
    summary_path = get_summary_path(tool_dir, project_path)
    if os.path.isfile(summary_path):
        os.remove(summary_path)

