import streamlit as st
import os
import re
import json
from datetime import datetime, timedelta
from dateutil.parser import parse
from utils.ui_helper import UIHelper


# Configuration
UPLOAD_FOLDER = "uploaded_docs/personal"
ACTION_ITEMS_FILE = "action_items.json"
CURRENT_DATE = datetime.now()  # Use system date and time

# Helper function to parse due dates relative to doc date
def parse_due_date(due_text, doc_date):
    try:
        day_map = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }
        due_text = due_text.lower()
        for day, offset in day_map.items():
            if day in due_text:
                base_date = doc_date if doc_date else CURRENT_DATE
                current_dow = base_date.weekday()
                days_ahead = (offset - current_dow + 7) % 7
                if days_ahead == 0 and "next" in due_text:
                    days_ahead = 7
                return base_date + timedelta(days=days_ahead)
        return parse(due_text, fuzzy=True)
    except:
        return None

# Function to load action items
def load_action_items():
    action_items = []
    for filename in os.listdir(UPLOAD_FOLDER):
        if filename.endswith(".md"):
            with open(os.path.join(UPLOAD_FOLDER, filename), "r") as f:
                content = f.read()
                date_match = re.search(r"\*Date\*: (\d{4}-\d{2}-\d{2})", content)
                doc_date = parse(date_match.group(1)) if date_match else None
                action_section = re.search(r"## Action Items\n([\s\S]*?)(?:\n## |\Z)", content)
                if action_section:
                    items = re.findall(r"- \[( |x)\] (.*?)(?: by (\w+))?", action_section.group(1))
                    for completed, task, due in items:
                        due_date = parse_due_date(due, doc_date) if due else None
                        action_items.append({
                            "id": f"{filename}_{len(action_items)}",
                            "task": task,
                            "completed": completed == "x",
                            "due_date": due_date.isoformat() if due_date else None,
                            "filename": filename,
                            "markdown": task
                        })
    action_items.sort(key=lambda x: x["due_date"] or "9999-12-31")
    with open(ACTION_ITEMS_FILE, "w") as f:
        json.dump(action_items, f, indent=2)
    return action_items

# Calculate a hash of file modification times to detect changes
def get_file_hash():
    return sum(os.path.getmtime(os.path.join(UPLOAD_FOLDER, f)) for f in os.listdir(UPLOAD_FOLDER) if f.endswith(".md"))

# Function to update markdown file
def update_markdown_file(item_id, new_task, new_completed, new_due, new_filename):
    old_filename, item_index = item_id.rsplit("_", 1)
    item_index = int(item_index)
    file_path = os.path.join(UPLOAD_FOLDER, old_filename)
    
    # Read the content of the original markdown file
    try:
        with open(file_path, "r") as f:
            content = f.read()
    except FileNotFoundError:
        st.error(f"File {old_filename} not found.")
        return False
    
    # Find the action items section
    action_section_match = re.search(r"(## Action Items\n)([\s\S]*?)(?:\n## |\Z)", content)
    if not action_section_match:
        st.error(f"Action Items section not found in {old_filename}.")
        return False
    
    action_section = action_section_match.group(2)
    # Find all action items
    items = re.findall(r"(- \[( |x)\] (.*?)(?: by (\w+))?\n)", action_section)
    if item_index >= len(items):
        st.error(f"Item index {item_index} out of range in {old_filename}.")
        return False
    
    # Update the specific item
    full_line, _, _, _ = items[item_index]
    new_line = f"- [{'x' if new_completed else ' '}] {new_task}"
    if new_due:
        new_line += f" by {new_due}"
    new_line += "\n"
    
    # Replace the old line with the new one
    updated_action_section = action_section.replace(full_line, new_line)
    updated_content = (
        content[:action_section_match.start(1)] +
        "## Action Items\n" +
        updated_action_section +
        content[action_section_match.end(2):]
    )
    
    # Handle filename change
    new_file_path = os.path.join(UPLOAD_FOLDER, new_filename)
    if new_filename != old_filename:
        # Check if the new filename already exists
        if os.path.exists(new_file_path):
            st.error(f"File {new_filename} already exists. Please choose a different name.")
            return False
        # Rename the file
        os.rename(file_path, new_file_path)
    
    # Write updated content to the (possibly renamed) file
    with open(new_file_path, "w") as f:
        f.write(updated_content)
    
    return True

# Function to display action items
def display_action_items():
    for item in st.session_state.action_item_session_action_items:
        with st.container():
            # Display only the date part of due_date (YYYY-MM-DD)
            display_due_date = item['due_date'][:10] if item['due_date'] else "No due date"
            st.markdown(f"**Task**: {item['task']}")
            st.markdown(f"**Due Date**: {display_due_date}")
            st.markdown(f"**Completed**: {'Yes' if item['completed'] else 'No'}")
            st.markdown(f"**Source**: {item['filename']}")
            
            # Edit functionality
            if st.button("Edit", key=f"edit_{item['id']}"):
                st.session_state[f"editing_{item['id']}"] = True

            if st.session_state.get(f"editing_{item['id']}", False):
                new_task = st.text_area("Edit Task", value=item['markdown'], key=f"edit_task_{item['id']}")
                # Use only the date part for editing
                new_due = st.text_input("Edit Due Date (e.g., 'Monday' or '2025-12-31')", 
                                       value=item['due_date'][:10] if item['due_date'] else "", 
                                       key=f"edit_due_{item['id']}")
                new_completed = st.checkbox("Completed", value=item['completed'], key=f"edit_completed_{item['id']}")
                new_filename = st.text_input("Edit Source Filename", value=item['filename'], key=f"edit_filename_{item['id']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Save", key=f"save_{item['id']}"):
                        # Validate due date
                        parsed_due = parse_due_date(new_due, None) if new_due else None
                        # Update the markdown file
                        if update_markdown_file(item['id'], new_task, new_completed, new_due, new_filename):
                            # Update in-memory action items
                            item['task'] = new_task
                            item['markdown'] = new_task
                            item['completed'] = new_completed
                            item['due_date'] = parsed_due.isoformat() if parsed_due else None
                            item['filename'] = new_filename
                            item['id'] = f"{new_filename}_{item['id'].rsplit('_', 1)[1]}"  # Update ID with new filename
                            with open(ACTION_ITEMS_FILE, "w") as f:
                                json.dump(st.session_state.action_item_session_action_items, f, indent=2)
                            st.session_state[f"editing_{item['id']}"] = False
                            st.rerun()
                with col2:
                    if st.button("Cancel", key=f"cancel_{item['id']}"):
                        st.session_state[f"editing_{item['id']}"] = False
                        st.rerun()
            st.markdown("---")

# Main Streamlit app
def main():
    UIHelper.config_page()
    UIHelper.setup_sidebar()

    # Initialize session state
    if "action_item_session_file_hash" not in st.session_state:
        st.session_state.action_item_session_file_hash = get_file_hash()
    if "action_item_session_action_items" not in st.session_state:
        st.session_state.action_item_session_action_items = load_action_items()
    if "action_item_session_last_checked" not in st.session_state:
        st.session_state.action_item_session_last_checked = datetime.now()

    # Check for file changes every 10 seconds
    if (datetime.now() - st.session_state.action_item_session_last_checked).total_seconds() > 10:
        current_hash = get_file_hash()
        if current_hash != st.session_state.action_item_session_file_hash:
            st.session_state.action_item_session_file_hash = current_hash
            st.session_state.action_item_session_action_items = load_action_items()
        st.session_state.action_item_session_last_checked = datetime.now()

    # Display action items
    display_action_items()

if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    main()