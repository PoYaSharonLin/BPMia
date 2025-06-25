import streamlit as st  # type: ignore
import os
from typing import List
from utils.ui_helper import UIHelper
from services.document_processor.document_crud import CRUDProcessor
from services.document_processor.document_mermaid import MermaidProcessor


class MermaidBlockExtractionError(Exception):
    """Custom exception for Mermaid block extraction failures."""
    pass


class MermaidRenderingError(Exception):
    """Custom exception for Mermaid rendering failures."""
    pass


class DocumentUploader:
    def __init__(self):
        self.base_upload_dir = "uploaded_docs"
        self.doc_types = {
            "Personal Notes": "personal",
            "Organizational Structure": "org"
        }
        self.crud_processor = CRUDProcessor()

    def setup_directories(self, folder: str) -> str:
        """Create and return upload directory path."""
        upload_dir = os.path.join(self.base_upload_dir, folder)
        try:
            os.makedirs(upload_dir, exist_ok=True)
        except OSError as e:
            st.error(f"Error creating directory: {str(e)}")
            return ""
        return upload_dir

    def get_uploaded_files(self, upload_dir: str) -> List[str]:
        """Return list of markdown files in upload directory."""
        try:
            return [f for f in os.listdir(upload_dir) if f.endswith(".md")]
        except FileNotFoundError:
            return []
        except Exception as e:
            st.error(f"Error listing files: {str(e)}")
            return []

    def display_uploaded_files(self, files: List[str], doc_type: str) -> None:
        st.markdown(f"### 📄 Uploaded files in {doc_type}")

        for fname in files:
            file_path = os.path.join(
                self.base_upload_dir,
                self.doc_types[doc_type],
                fname
            )

            # Create columns for file operations
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            with col1:
                show = st.toggle(f"📄 {fname}", key=f"toggle-{fname}")

            with col2:
                if st.button("✏️ Edit", key=f"edit-{fname}"):
                    st.session_state[f"editing_{fname}"] = True

            with col3:
                if st.button("📥 Download", key=f"download-{fname}"):
                    content = self.crud_processor.read_file(file_path)
                    if content:
                        st.download_button(
                            label="💾 Download",
                            data=content,
                            file_name=fname,
                            mime="text/markdown",
                            key=f"download_btn_{fname}"
                        )

            with col4:
                if st.button("🗑️ Delete",
                             key=f"delete-{fname}", type="secondary"):
                    if st.session_state.get(f"confirm_delete_{fname}", False):
                        if self.crud_processor.delete_file(file_path):
                            st.rerun()
                    else:
                        st.session_state[f"confirm_delete_{fname}"] = True
                        st.warning(
                            (
                                f"⚠️ Click delete again to confirm deletion "
                                f"{fname}"
                            )
                        )

            # Handle file editing
            if st.session_state.get(f"editing_{fname}", False):
                self._handle_file_editing(file_path, fname, doc_type)

            # Show file content and Mermaid charts
            if show:
                try:
                    content = self.crud_processor.read_file(file_path)
                    if content:
                        with st.container():
                            # Show file content in expandable section
                            with st.expander("📝 File Content", expanded=False):
                                st.markdown(content)

                            st.markdown("⬇️ Mermaid chart：")
                            mermaid_processor = MermaidProcessor()
                            mermaid_processor.render_mermaid_blocks(
                                content
                            )

                except Exception as e:
                    st.error(f"Error reading `{fname}`: {str(e)}")

    def _handle_file_editing(
        self, file_path: str, fname: str, doc_type: str
    ) -> None:
        """Handle file editing interface."""
        st.markdown(f"### ✏️ Editing: {fname}")

        # Read current content
        current_content = self.crud_processor.read_file(file_path)
        if current_content is None:
            st.error("Failed to read file content")
            return

        # Text area for editing
        edited_content = st.text_area(
            "Edit file content:",
            value=current_content,
            height=400,
            key=f"edit_area_{fname}"
        )

        # Action buttons
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.button("💾 Save", key=f"save_{fname}", type="primary"):
                if self.crud_processor.update_file(file_path, edited_content):
                    st.session_state[f"editing_{fname}"] = False
                    st.success(f"✅ {fname} updated successfully!")
                    st.rerun()

        with col2:
            if st.button("❌ Cancel", key=f"cancel_{fname}"):
                st.session_state[f"editing_{fname}"] = False
                st.rerun()

        with col3:
            # Preview updated Mermaid charts
            if st.button("👁️ Preview Changes", key=f"preview_{fname}"):
                st.markdown("**Preview of changes:**")
                mermaid_processor = MermaidProcessor()
                mermaid_processor.render_mermaid_blocks(edited_content)

    def render(self):
        """Render the document uploader interface."""
        crud_processor = CRUDProcessor()
        try:
            doc_type = st.radio(
                "Select Upload Category",
                list(self.doc_types.keys()))

            upload_dir = self.setup_directories(self.doc_types[doc_type])
            if not upload_dir:
                return

            uploaded_files = self.get_uploaded_files(upload_dir)
            st.sidebar.markdown(
                f"📁 **{doc_type} Files Uploaded:** `{len(uploaded_files)}`")

            # Display uploaded files with CRUD operations
            self.display_uploaded_files(uploaded_files, doc_type)

            # File upload section
            st.markdown("---")
            st.markdown("### 📤 Upload New File")
            uploaded_file = st.file_uploader(
                f"Upload your markdown (.md) file for {doc_type}",
                type=["md"]
            )

            # Handle file upload using CRUD processor
            crud_processor.handle_file_upload(uploaded_file, upload_dir)

        except Exception as e:
            st.error(f"Error rendering interface: {str(e)}")


def main():
    try:
        UIHelper.config_page()
        UIHelper.setup_sidebar()
        uploader = DocumentUploader()
        uploader.render()
    except Exception as e:
        st.error(f"Error in main application: {str(e)}")


if __name__ == "__main__":
    main()
