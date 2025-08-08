import streamlit as st  # type: ignore


class UIHelper:
    @staticmethod
    def config_page():
        st.set_page_config(
            page_title='Knowledge Assistant',
            layout='wide',
            initial_sidebar_state='expanded',
            page_icon="💼",
            menu_items={
                'Get Help': 'https://streamlit.io/',
                'Report a bug': 'https://github.com',
                'About': 'About your application: **Hello world**'
            }
        )

    @staticmethod
    def setup_sidebar():
        with st.sidebar:
            st.header("OMT PMO BP")
            st.page_link("streamlit_app.py", label="BP Mia", icon="👧")

            # Group related pages under an expander
            with st.expander("Notes & Actions", expanded=True):
                st.page_link("pages/documents_upload.py",
                             label="Upload Notes", icon="📁")
                st.page_link("pages/loading_visualization.py",
                             label="Loading Mia", icon="📈")

    @staticmethod
    def save_lang():
        st.session_state['lang_setting'] = st.session_state.get(
            "language_select")
