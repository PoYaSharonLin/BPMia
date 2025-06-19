import streamlit as st  # type: ignore
import os
import re
import json
from datetime import datetime
from dateutil.parser import parse
from utils.ui_helper import UIHelper
import dateparser  # type: ignore

UPLOAD_FOLDER = "uploaded_docs/personal"
ACTION_ITEMS_FILE = "action_items.json"
CURRENT_DATE = datetime.now()


def parse_due_date(task_text, base_date):
    """
    Extract due date from natural language phrases within task text.
    Examples: "next Wednesday", "this afternoon", "in 3 days", etc.
    """
    base = base_date or CURRENT_DATE
    lowered = task_text.lower()

    # Common keywords after which a due phrase usually follows
    trigger_keywords = ["by", "on", "before", "due", "around", "this", "next",
                        "in", "within", "after", "at", "until"]

    # Look for a phrase following a keyword
    for kw in trigger_keywords:
        if f" {kw} " in lowered:
            phrase = lowered.split(f" {kw} ", 1)[1]
            parsed = dateparser.parse(
                phrase,
                settings={
                    "RELATIVE_BASE": base,
                    "PREFER_DATES_FROM": "future",
                    "RETURN_AS_TIMEZONE_AWARE": False,
                    "PARSERS": ["relative-time",
                                "absolute-time", "custom-formats"]
                }
            )
            if parsed:
                return parsed

    # Fallback: try parsing the whole task string
    parsed = dateparser.parse(
        lowered,
        settings={
            "RELATIVE_BASE": base,
            "PREFER_DATES_FROM": "future",
            "RETURN_AS_TIMEZONE_AWARE": False,
            "PARSERS": ["relative-time", "absolute-time", "custom-formats"]
        }
    )
    return parsed


def load_action_items():
    items = []
    for filename in os.listdir(UPLOAD_FOLDER):
        if not filename.endswith(".md"):
            continue
        with open(os.path.join
                  (UPLOAD_FOLDER, filename), "r", encoding="utf-8") as f:
            content = f.read()
        date_match = re.search(r"\*Date\*: (\d{4}-\d{2}-\d{2})", content)
        doc_date = parse(date_match.group(1)) if date_match else None
        section = re.search(r"## Action Items\n([\s\S]*?)(\n## |\Z)", content)
        if not section:
            continue

        action_text = section.group(1)
        matches = re.findall(r"^- \[( |x)\] (.+)$", action_text, re.MULTILINE)
        for i, (checked, full_text) in enumerate(matches):
            task = full_text.strip()
            due_date = parse_due_date(task, doc_date)
            items.append({
                "id": f"{filename}_{i}",
                "task": task,
                "completed": checked == "x",
                "due_date": due_date.isoformat() if due_date else None,
                "filename": filename,
                "markdown": task
            })
    items.sort(key=lambda x: x["due_date"] or "9999-12-31")
    with open(ACTION_ITEMS_FILE, "w") as f:
        json.dump(items, f, indent=2)
    return items


def get_file_hash():
    return sum(os.path.getmtime(os.path.join(UPLOAD_FOLDER, f))
               for f in os.listdir(UPLOAD_FOLDER) if f.endswith(".md"))


def update_markdown_file(item_id, new_task, new_completed,
                         new_due, new_filename):
    old_filename, index = item_id.rsplit("_", 1)
    index = int(index)
    file_path = os.path.join(UPLOAD_FOLDER, old_filename)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return False

    match = re.search(r"(## Action Items\n)([\s\S]*?)(\n## |\Z)", content)
    if not match:
        return False

    section = match.group(2)
    matches = re.findall(r"(- \[( |x)\] (.*?)(?: by ([^\n]+))?\n?)", section)
    if index >= len(matches):
        return False

    full_line, _, _, _ = matches[index]
    new_line = f"- [{'x' if new_completed else ' '}] {new_task}"
    if new_due:
        new_line += f" by {new_due}"
    new_line += "\n"
    new_section = section.replace(full_line, new_line)
    updated = (
        content[:match.start(1)]
        + match.group(1)
        + new_section
        + content[match.end(2):]
    )

    new_path = os.path.join(UPLOAD_FOLDER, new_filename)
    if new_filename != old_filename and os.path.exists(new_path):
        return False
    elif new_filename != old_filename:
        os.rename(file_path, new_path)

    with open(new_path, "w", encoding="utf-8") as f:
        f.write(updated)
    return True


def display_action_items():
    for item in st.session_state.action_items:
        with st.container():
            st.markdown(f"**Task**: {item['task']}")
            due_str = (
                item['due_date'][:10] if item['due_date'] else 'No due date'
            )
            st.markdown(f"**Due Date**: {due_str}")
            st.markdown(
                f"**Completed**: {'Yes' if item['completed'] else 'No'}"
            )
            st.markdown(f"**Source**: {item['filename']}")
            if st.button("Edit", key=f"edit_{item['id']}"):
                st.session_state[f"editing_{item['id']}"] = True

            if st.session_state.get(f"editing_{item['id']}", False):
                new_task = st.text_area(
                    "Edit Task",
                    value=item['task'],
                    key=f"task_{item['id']}"
                )
                new_due = st.text_input(
                    "Edit Due Date",
                    value=item['due_date'][:10] if item['due_date'] else "",
                    key=f"due_{item['id']}"
                )
                new_completed = st.checkbox(
                    "Completed",
                    value=item['completed'],
                    key=f"complete_{item['id']}"
                )
                new_filename = st.text_input(
                    "Edit Filename",
                    value=item['filename'],
                    key=f"file_{item['id']}"
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Save", key=f"save_{item['id']}"):
                        if update_markdown_file(
                            item['id'],
                            new_task,
                            new_completed,
                            new_due,
                            new_filename
                        ):
                            st.session_state[f"editing_{item['id']}"] = False
                            st.rerun()
                with col2:
                    if st.button("Cancel", key=f"cancel_{item['id']}"):
                        st.session_state[f"editing_{item['id']}"] = False
                        st.rerun()
            st.markdown("---")


def main():
    UIHelper.config_page()
    UIHelper.setup_sidebar()
    if "file_hash" not in st.session_state:
        st.session_state.file_hash = get_file_hash()
        st.session_state.action_items = load_action_items()
    elif get_file_hash() != st.session_state.file_hash:
        st.session_state.file_hash = get_file_hash()
        st.session_state.action_items = load_action_items()
    display_action_items()


if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    main()
