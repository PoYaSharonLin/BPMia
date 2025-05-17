import streamlit as st

class UIHelper:
    @staticmethod
    def config_page():
        st.set_page_config(
            page_title='Knowledge Assistant',
            layout='wide',
            initial_sidebar_state='auto',
            menu_items={
                'Get Help': 'https://streamlit.io/',
                'Report a bug': 'https://github.com',
                'About': 'About your application: **Hello world**'
            },
            page_icon="img/favicon.ico"
        )

    @staticmethod
    def setup_sidebar():
        with st.sidebar:
            st.page_link("streamlit_app.py", label="On-boarding Mentor", icon="🏠")
            st.page_link("pages/rag_agents.py", label="Chat with Notes", icon="🤖")
            st.page_link("pages/documents_upload.py", label="Upload Notes", icon="📄")
            st.page_link("pages/word_cloud.py", label="Create Word Cloud", icon="☁️")


            selected_lang = st.selectbox(
                "Language", ["English", "繁體中文"],
                index=0, on_change=UIHelper.save_lang, key="language_select"
            )
            if 'lang_setting' not in st.session_state:
                st.session_state['lang_setting'] = selected_lang

            st_c_1 = st.container(border=True)
            with st_c_1:
                st.image("https://www.w3schools.com/howto/img_avatar.png")

    @staticmethod
    def save_lang():
        st.session_state['lang_setting'] = st.session_state.get("language_select")

    # @staticmethod
    # def setup_chat(st_c_chat):
    #     user_image = "https://www.w3schools.com/howto/img_avatar.png"
    #     # st_c_chat = st.container(border=True)

    #     if "messages" not in st.session_state:
    #         st.session_state.messages = []
    #     else:
    #         for msg in st.session_state.messages:
    #             if msg["role"] == "user":
    #                 st_c_chat.chat_message(msg["role"], avatar=user_image).markdown(msg["content"])
    #             elif msg["role"] == "assistant":
    #                 st_c_chat.chat_message(msg["role"]).markdown(msg["content"])
    #             else:
    #                 try:
    #                     image_tmp = msg.get("image")
    #                     if image_tmp:
    #                         st_c_chat.chat_message(msg["role"], avatar=image_tmp).markdown(msg["content"])
    #                 except:
    #                     st_c_chat.chat_message(msg["role"]).markdown(msg["content"])
