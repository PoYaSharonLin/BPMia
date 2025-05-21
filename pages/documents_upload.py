import streamlit as st
import os
from typing import List
from utils.ui_helper import UIHelper

class DocumentUploader:
    def __init__(self):
        self.base_upload_dir = "uploaded_docs"
        self.doc_types = {
            "Personal Notes": "personal",
            "Organizational Structure": "org"
        }
        
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
        """Display uploaded files with individual expanders (not nested)."""
        st.markdown(f"### 📄 Uploaded files in {doc_type}")
        
        if files:
            for fname in files:
                file_path = os.path.join(self.base_upload_dir, self.doc_types[doc_type], fname)
                with st.expander(f"📄 {fname}"):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            st.markdown(content, unsafe_allow_html=False)
                    except Exception as e:
                        st.error(f"Error reading `{fname}`: {str(e)}")
        else:
            st.info("No files uploaded yet.")



    def handle_file_upload(self, uploaded_file, upload_dir: str) -> None:
        """Handle file upload and preview."""
        if uploaded_file is None:
            return

        try:
            file_path = os.path.join(upload_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.success("✅ Upload Successful!")
            st.markdown(f"**File saved as:** `{uploaded_file.name}`")

            st.subheader("📝 File Preview")
            try:
                file_content = uploaded_file.getvalue().decode("utf-8")
                st.markdown(file_content, unsafe_allow_html=False)
            except UnicodeDecodeError:
                st.error("Error: Unable to decode file content. Please ensure the file is a valid text file.")
        except Exception as e:
            st.error(f"Error uploading file: {str(e)}")

    def render(self):
        """Render the document uploader interface."""
        try:
            doc_type = st.radio("Select Upload Category", list(self.doc_types.keys()))
            upload_dir = self.setup_directories(self.doc_types[doc_type])
            if not upload_dir:
                return
                
            uploaded_files = self.get_uploaded_files(upload_dir)
            st.sidebar.markdown(f"📁 **{doc_type} Files Uploaded:** `{len(uploaded_files)}`")
            
            self.display_uploaded_files(uploaded_files, doc_type)
            
            uploaded_file = st.file_uploader(
                f"Upload your markdown (.md) file for {doc_type}",
                type=["md"]
            )
            
            self.handle_file_upload(uploaded_file, upload_dir)
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