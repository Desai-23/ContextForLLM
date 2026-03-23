import os
import json
from flask import Flask, request, jsonify, send_from_directory
from context_builder import (
    build_folder_tree,
    collect_files,
    build_file_block,
    build_header,
    split_into_prompts,
    save_prompts,
    count_tokens,
    load_contextignore,
)
from project_summary import (
    generate_project_summary,
    save_summary,
    load_summary,
    delete_summary,
)

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), "ui"))

TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
RECENT_FILE = os.path.join(TOOL_DIR, "recent_projects.json")
MAX_RECENT = 8

# Session-only Groq key (not saved to disk)
session_groq_key = ""

# ── Recent projects ────────────────────────────────────────────
def load_recent():
    if os.path.isfile(RECENT_FILE):
        try:
            with open(RECENT_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_recent(project_path, project_name):
    recent = load_recent()
    recent = [r for r in recent if r["path"] != project_path]
    recent.insert(0, {"path": project_path, "name": project_name})
    recent = recent[:MAX_RECENT]
    with open(RECENT_FILE, "w") as f:
        json.dump(recent, f, indent=2)

# ── Routes ─────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory("ui", "index.html")

@app.route("/api/recent", methods=["GET"])
def get_recent():
    recent = load_recent()
    recent = [r for r in recent if os.path.isdir(r["path"])]
    return jsonify({"recent": recent})

@app.route("/api/recent/remove", methods=["POST"])
def remove_recent():
    data = request.json
    path = data.get("path", "")
    recent = load_recent()
    recent = [r for r in recent if r["path"] != path]
    with open(RECENT_FILE, "w") as f:
        json.dump(recent, f, indent=2)
    delete_summary(TOOL_DIR, path)
    return jsonify({"ok": True})

@app.route("/api/groq-key", methods=["POST"])
def set_groq_key():
    global session_groq_key
    data = request.json
    key = data.get("key", "").strip()
    if not key:
        return jsonify({"error": "Key is empty"}), 400
    if not key.startswith("gsk_"):
        return jsonify({"error": "Invalid key — Groq keys start with gsk_"}), 400
    session_groq_key = key
    return jsonify({"ok": True})

@app.route("/api/groq-key/status", methods=["GET"])
def groq_key_status():
    return jsonify({"has_key": bool(session_groq_key)})

@app.route("/api/scan", methods=["POST"])
def scan():
    data = request.json
    project_path = data.get("project_path", "").strip()
    project_path = os.path.expanduser(project_path)
    project_path = os.path.abspath(project_path)

    if not os.path.isdir(project_path):
        return jsonify({"error": f"Folder not found: {project_path}"}), 400

    project_name = os.path.basename(project_path)
    tree_lines = build_folder_tree(project_path)
    files = collect_files(project_path)
    patterns = load_contextignore(project_path)
    save_recent(project_path, project_name)

    file_blocks = [build_file_block(path, content) for path, content in files]
    header = build_header(project_name, project_path, "\n".join(tree_lines), 1)
    full_text = header + "\n".join(file_blocks)
    total_tokens = count_tokens(full_text)

    existing_summary = load_summary(TOOL_DIR, project_path)

    return jsonify({
        "project_name": project_name,
        "project_path": project_path,
        "tree": tree_lines,
        "files": [{"path": p, "tokens": count_tokens(c)} for p, c in files],
        "total_tokens": total_tokens,
        "file_count": len(files),
        "contextignore_rules": patterns,
        "existing_summary": existing_summary,
        "groq_key_set": bool(session_groq_key)
    })

@app.route("/api/summary/generate", methods=["POST"])
def generate_summary():
    global session_groq_key
    data = request.json
    project_path = os.path.abspath(
        os.path.expanduser(data.get("project_path", "")))

    if not session_groq_key:
        return jsonify({"error": "No Groq API key set for this session"}), 400

    if not os.path.isdir(project_path):
        return jsonify({"error": "Folder not found"}), 400

    project_name = os.path.basename(project_path)
    files = collect_files(project_path)

    try:
        summary = generate_project_summary(project_name, files, session_groq_key)
        save_summary(TOOL_DIR, project_path, summary)
        return jsonify({"summary": summary})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/summary/save", methods=["POST"])
def save_summary_route():
    data = request.json
    project_path = os.path.abspath(
        os.path.expanduser(data.get("project_path", "")))
    summary = data.get("summary", "").strip()
    if not summary:
        return jsonify({"error": "Summary is empty"}), 400
    save_summary(TOOL_DIR, project_path, summary)
    return jsonify({"ok": True})

@app.route("/api/summary/delete", methods=["POST"])
def delete_summary_route():
    data = request.json
    project_path = os.path.abspath(
        os.path.expanduser(data.get("project_path", "")))
    delete_summary(TOOL_DIR, project_path)
    return jsonify({"ok": True})

@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.json
    project_path = os.path.abspath(
        os.path.expanduser(data.get("project_path", "")))
    task = data.get("task", "").strip()
    excluded = set(data.get("excluded", []))
    annotations = data.get("annotations", {})
    include_summary = data.get("include_summary", True)

    if not os.path.isdir(project_path):
        return jsonify({"error": "Folder not found"}), 400

    project_name = os.path.basename(project_path)
    tree_lines = build_folder_tree(project_path)
    all_files = collect_files(project_path)
    files = [(p, c) for p, c in all_files if p not in excluded]

    summary_text = ""
    if include_summary:
        summary_text = load_summary(TOOL_DIR, project_path) or ""

    output_dir = os.path.join(TOOL_DIR, "output")
    os.makedirs(output_dir, exist_ok=True)

    file_blocks = [
        build_file_block(path, content, annotations.get(path, ""))
        for path, content in files
    ]
    header = build_header(project_name, project_path, "\n".join(tree_lines), 1)

    if summary_text:
        header = f"## PROJECT SUMMARY\n\n{summary_text}\n\n{header}"

    prompts = split_into_prompts(header, file_blocks, task, project_name)
    saved_files = save_prompts(prompts, output_dir)

    parts = []
    for i, filepath in enumerate(saved_files):
        with open(filepath, "r") as f:
            content = f.read()
        parts.append({
            "part": i + 1,
            "filename": os.path.basename(filepath),
            "tokens": count_tokens(content),
            "content": content
        })

    return jsonify({
        "total_parts": len(parts),
        "output_dir": output_dir,
        "parts": parts
    })

if __name__ == "__main__":
    print("\nContextForLLM is running.")
    print("Open this in your browser: http://localhost:5000\n")
    app.run(debug=False, port=5000)




    