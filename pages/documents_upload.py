import streamlit as st  # type: ignore
import streamlit.components.v1 as components  # type: ignore
import os
import re
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

    def render_mermaid_raw(self, code: str, height=700):
        html_code = f"""
        <div class="mermaid">
        {code}
        </div>
        <script src=
        "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js">
        </script>
        <script>
        mermaid.initialize({{ startOnLoad: true }});
        </script>
        """
        components.html(html_code, height=height, scrolling=True)

    def extract_and_render_mermaid_blocks(self, markdown_text: str):
        pattern = r"```mermaid\s*\n([\s\S]*?)```"
        matches = re.findall(pattern, markdown_text)

        for i, code in enumerate(matches):
            # st.markdown(f"### Mermaid block #{i+1}")
            # st.code(code, language="mermaid")
            cleaned = (
                code.strip()
                .replace("\\n", "<br>")
                .replace('\r\n', '\n')
                .replace('\r', '\n')
            )
            self.render_mermaid_raw(cleaned)

        cleaned_text = re.sub(pattern, '', markdown_text, flags=re.DOTALL)
        if cleaned_text.strip():
            st.markdown("---")
            st.markdown(cleaned_text, unsafe_allow_html=True)

    def display_uploaded_files(self, files: List[str], doc_type: str) -> None:
        st.markdown(f"### 📄 Uploaded files in {doc_type}")

        for fname in files:
            file_path = os.path.join(
                self.base_upload_dir,
                self.doc_types[doc_type],
                fname
            )

            # use a toggle to show/hide file content
            show = st.toggle(f"📄 {fname}", key=f"toggle-{fname}")
            if show:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    with st.container():
                        st.markdown("⬇️ Mermaid chart：")
                        self.extract_and_render_mermaid_blocks(content)

                except Exception as e:
                    st.error(f"Error reading `{fname}`: {str(e)}")

    def handle_file_upload(self, uploaded_file, upload_dir: str) -> None:
        if uploaded_file is None:
            return
        file_path = os.path.join(upload_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("✅ Upload successful!")
        file_content = uploaded_file.getvalue().decode("utf-8")
        self.extract_and_render_mermaid_blocks(file_content)

    def render(self):
        """Render the document uploader interface."""
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
