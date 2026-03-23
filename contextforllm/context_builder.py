import os
import fnmatch
import tiktoken

INCLUDE_EXTENSIONS = [
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".html", ".css", ".json", ".md",
    ".txt", ".env.example", ".yaml", ".yml",
    ".sh", ".sql"
]

SKIP_FOLDERS = [
    "venv", ".venv", "env",
    "node_modules", ".git",
    "__pycache__", ".next",
    "dist", "build", ".idea",
    ".vscode", "coverage",
    "output", "summaries"
]

MAX_TOKENS_PER_PART = 80000

# ── Token counting ─────────────────────────────────────────────
def count_tokens(text):
    try:
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return len(text) // 4

# ── .contextignore ─────────────────────────────────────────────
def load_contextignore(project_path):
    ignore_file = os.path.join(project_path, ".contextignore")
    if not os.path.isfile(ignore_file):
        return []
    patterns = []
    with open(ignore_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)
    return patterns

def is_ignored(rel_path, patterns):
    for pattern in patterns:
        if fnmatch.fnmatch(rel_path, pattern):
            return True
        if fnmatch.fnmatch(os.path.basename(rel_path), pattern):
            return True
    return False

# ── File collection ────────────────────────────────────────────
def collect_files(project_path):
    patterns = load_contextignore(project_path)
    result = []
    for root, dirs, files in os.walk(project_path):
        dirs[:] = [
            d for d in dirs
            if d not in SKIP_FOLDERS and not d.startswith(".")
        ]
        for fname in sorted(files):
            _, ext = os.path.splitext(fname)
            if ext.lower() not in INCLUDE_EXTENSIONS:
                continue
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, project_path)
            if is_ignored(rel_path, patterns):
                continue
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                result.append((rel_path, content))
            except Exception:
                continue
    return result

# ── Folder tree ────────────────────────────────────────────────
def build_folder_tree(project_path):
    lines = []
    for root, dirs, files in os.walk(project_path):
        dirs[:] = sorted([
            d for d in dirs
            if d not in SKIP_FOLDERS and not d.startswith(".")
        ])
        level = os.path.relpath(root, project_path).count(os.sep)
        if os.path.relpath(root, project_path) == ".":
            level = 0
        indent = "    " * level
        if level > 0:
            lines.append(f"{indent}— {os.path.basename(root)}/")
        for fname in sorted(files):
            _, ext = os.path.splitext(fname)
            if ext.lower() in INCLUDE_EXTENSIONS:
                lines.append(f"{'    ' * (level+1 if level > 0 else 1)}— {fname}")
    return lines

# ── File block ─────────────────────────────────────────────────
def build_file_block(rel_path, content, annotation=""):
    lines = []
    lines.append(f"\n{'='*60}")
    lines.append(f"FILE: {rel_path}")
    if annotation:
        lines.append(f"# NOTE: {annotation}")
    lines.append("="*60)
    lines.append(content)
    return "\n".join(lines)

# ── Header ─────────────────────────────────────────────────────
def build_header(project_name, project_path, tree_text, part_num):
    return f"""{'='*60}
CONTEXT DOCUMENT — {project_name}
Part {part_num}
{'='*60}

This document contains the full source code of the project '{project_name}'.
Read all files carefully before responding.

PROJECT PATH: {project_path}

FOLDER STRUCTURE:
{tree_text}

{'='*60}
SOURCE FILES
{'='*60}
"""

# ── Prompt splitter ────────────────────────────────────────────
def split_into_prompts(header, file_blocks, task, project_name):
    parts = []
    current_blocks = []
    current_tokens = count_tokens(header)

    for block in file_blocks:
        block_tokens = count_tokens(block)
        if current_tokens + block_tokens > MAX_TOKENS_PER_PART and current_blocks:
            parts.append(current_blocks)
            current_blocks = [block]
            current_tokens = count_tokens(header) + block_tokens
        else:
            current_blocks.append(block)
            current_tokens += block_tokens

    if current_blocks:
        parts.append(current_blocks)

    total = len(parts)
    prompts = []
    for i, blocks in enumerate(parts):
        part_num = i + 1
        h = build_header(project_name, "", "", part_num)
        body = h + "\n".join(blocks)
        if part_num < total:
            body += f"\n\n{'='*60}\nEND OF PART {part_num} OF {total}\n"
            body += "This is not all the code. Wait for the next part before responding.\n"
            body += f"Reply only with: 'Part {part_num} received. Send part {part_num+1}.'\n{'='*60}"
        else:
            if task:
                body += f"\n\n{'='*60}\nYOUR TASK\n{'='*60}\n{task}"
            body += f"\n\n{'='*60}\nEND OF CONTEXT"
            if total > 1:
                body += f" (Final part {part_num} of {total})"
            body += f"\n{'='*60}"
            if total > 1:
                body += "\nAll parts have been sent. Please complete the task above."
        prompts.append(body)

    return prompts

def save_prompts(prompts, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    saved = []
    for i, prompt in enumerate(prompts):
        path = os.path.join(output_dir, f"prompt_part_{i+1}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(prompt)
        saved.append(path)
    return saved
