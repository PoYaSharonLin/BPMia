import streamlit as st  # type: ignore
import os
from typing import Optional
from services.document_processor.document_mermaid import MermaidProcessor


class CRUDProcessor:
    def __init__(self):
        self.mermaid_processor = MermaidProcessor()

    def handle_file_upload(self, uploaded_file, upload_dir: str) -> None:
        """Handle file upload with preview."""
        if uploaded_file is None:
            return

        try:
            file_path = os.path.join(upload_dir, uploaded_file.name)

            # Check if file already exists
            if os.path.exists(file_path):
                if not st.session_state.get(
                    f"overwrite_{uploaded_file.name}", False
                ):
                    st.warning(
                        f"⚠️ File '{uploaded_file.name}' already exists!"
                    )
                    if st.button(
                        f"Overwrite {uploaded_file.name}?",
                        key=f"overwrite_btn_{uploaded_file.name}"
                    ):
                        st.session_state[
                            f"overwrite_{uploaded_file.name}"
                        ] = True
                        st.rerun()
                    return

            # Write file
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.success("✅ Upload successful!")

            # Show preview of uploaded content
            file_content = uploaded_file.getvalue().decode("utf-8")
            with st.expander("📋 Preview uploaded content", expanded=True):
                st.markdown(file_content)

            # Extract and render Mermaid blocks
            st.markdown("⬇️ Mermaid chart preview：")
            self.mermaid_processor.render_mermaid_blocks(file_content)

        except Exception as e:
            st.error(f"❌ Upload failed: {str(e)}")

    def read_file(self, file_path: str) -> Optional[str]:
        """Read file content."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            st.error(f"❌ File not found: {file_path}")
            return None
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
            return None

    def update_file(self, file_path: str, content: str) -> bool:
        """Update file with new content."""
        try:
            # Create backup before updating
            backup_path = f"{file_path}.backup"
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    backup_content = f.read()
                with open(backup_path, "w", encoding="utf-8") as f:
                    f.write(backup_content)
            # Write new content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            # Clean up backup after successful write
            if os.path.exists(backup_path):
                os.remove(backup_path)
            return True

        except Exception as e:
            st.error(f"❌ Error updating file: {str(e)}")
            # Restore from backup if it exists
            backup_path = f"{file_path}.backup"
            if os.path.exists(backup_path):
                try:
                    with open(backup_path, "r", encoding="utf-8") as f:
                        backup_content = f.read()
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(backup_content)
                    os.remove(backup_path)
                    st.info("🔄 File restored from backup")
                except Exception:
                    pass

            return False

    def delete_file(self, file_path: str) -> bool:
        """Delete file."""
        try:
            if not os.path.exists(file_path):
                st.error(f"❌ File not found: {file_path}")
                return False

            # Create a backup before deletion (optional safety measure)
            backup_dir = os.path.join(os.path.dirname(file_path), ".deleted")
            os.makedirs(backup_dir, exist_ok=True)

            backup_path = os.path.join(backup_dir,
                                       f"{os.path.basename(file_path)}.deleted"
                                       )

            # Move to backup location instead of permanent deletion
            os.rename(file_path, backup_path)

            st.success(
                "✅ File deleted successfully!"
            )
            return True

        except Exception as e:
            st.error(f"❌ Error deleting file: {str(e)}")
            return False

    def create_file(self, file_path: str, content: str) -> bool:
        """Create a new file."""
        try:
            if os.path.exists(file_path):
                st.error(f"❌ File already exists: {file_path}")
                return False
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            st.success(
                f"✅ File created successfully: {os.path.basename(file_path)}")
            return True

        except Exception as e:
            st.error(f"❌ Error creating file: {str(e)}")
            return False

    def list_files(self, directory: str, extension: str = ".md") -> list:
        """List files in directory with given extension."""
        try:
            if not os.path.exists(directory):
                return []

            return [
                f for f in os.listdir(directory)
                if f.endswith(extension)
                and os.path.isfile(os.path.join(directory, f))
            ]

        except Exception as e:
            st.error(f"❌ Error listing files: {str(e)}")
            return []

    def get_file_info(self, file_path: str) -> dict:
        """Get file information (size, modified date, etc.)."""
        try:
            if not os.path.exists(file_path):
                return {}
            stat = os.stat(file_path)
            return {
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "created": stat.st_ctime,
                "readable": os.access(file_path, os.R_OK),
                "writable": os.access(file_path, os.W_OK)
            }
        except Exception as e:
            st.error(f"❌ Error getting file info: {str(e)}")
            return {}
