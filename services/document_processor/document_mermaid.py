import streamlit as st  # type: ignore
import streamlit.components.v1 as components  # type: ignore
import re


class MermaidProcessor:
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

    def render_mermaid_blocks(self, markdown_text: str):
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
