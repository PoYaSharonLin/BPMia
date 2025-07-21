import streamlit as st  # type: ignore
import time
from autogen.code_utils import content_str  # type: ignore
from utils.ui_helper import UIHelper
from utils.llm_setup import LLMSetup  # type: ignore


class OrchestratorAgent:
    def __init__(self):
        self.user_name = "OMT Project Management Office, Business Planning"
        self.assistant_avatar = "🧠"
        self.user_avatar = "https://www.w3schools.com/howto/img_avatar.png"
        self.placeholderstr = "Chat with On-boarding Mentor to start on-boarding"
        UIHelper.config_page()
        self._load_api_keys()
        self._setup_llm()

    def _load_api_keys(self):
        self.gemini1_api_key, self.gemini2_api_key = LLMSetup.load_api_keys()

    def _setup_llm(self):
        self.assistant = LLMSetup.create_assistant(
            system_message=(
                "'This website helps users get familiar with onboarding"
                "website allows users to: "
                "1. Understand organization stakeholders using Chat with Notes, and "
                "2. Get to know with the company using notes with Chat with Notes.' "
                "If the user does not know where to start with,"
                "Recommend user to start uploading the notes and try out the agents"
                "Answer all user questions in a concise and helpful."
            ),
            api_key=self.gemini1_api_key,
        )
        self.user_proxy = LLMSetup.create_user_proxy(
            is_termination_msg=lambda x: (
                "ALL DONE" in content_str(x.get("content", ""))
            )
        )

    def stream_data(self, stream_str):
        for word in stream_str.split(" "):
            yield word + " "
            time.sleep(0.05)

    def generate_response(self, prompt):
        result = self.user_proxy.initiate_chat(
            recipient=self.assistant,
            message=prompt
        )
        return result.chat_history

    def show_chat_history(self, chat_history, container):
        for entry in chat_history:
            role = entry.get("role")
            content = entry.get("content", "").strip()
            if not content or "ALL DONE" in content:
                continue

            st.session_state.messages.append(
                {"role": role, "content": content})

            # 🧠 for user input, avatar icon for assistant
            if role in ["user", "user_proxy"]:
                container.chat_message(
                    "user", avatar=self.user_avatar
                ).markdown(f"**{content}**")
            else:
                container.chat_message(
                    "assistant", avatar=self.assistant_avatar
                ).markdown(content)

    def run(self):
        # Create two columns: one for the text, one for the button
        col1, col2 = st.columns([4, 1])  # Adjust the ratio as needed

        with col1:
            st.title(f"💬 On-boarding Mentor")

        with col2:
            st.write(" ")
            st.write(" ")
            if st.button("🔄 Restart Session"):
                st.session_state.clear()
                st.rerun()
        
        st.write("This is a website that could answers your queston about the department. ")
        st.write("Agent at this page could help you with general issues, such as drafting an email.")
        st.write("As for question answering with domain specific knowledge, please visit :blue-background[Chat with Notes]!")

        UIHelper.setup_sidebar()
        chat_container = st.container()
        

        # Initialize messages & flags 
        if "messages" not in st.session_state:
            st.session_state.messages = []

        if "conversation_started" not in st.session_state: 
            st.session_state.conversation_started = False
        
        
        @st.dialog("💡 Recommended Prompts")
        def show_recommended_prompts():
            st.write("Choose a question to get started:")
            recommended_prompts = [
                "What is this On-boarding website for?",
                "Where should I start with using this?",
                "Help me write email to my manager",
            ]
            
            # Create one column per prompt
            cols = st.columns(len(recommended_prompts))
        
            for col, prompt in zip(cols, recommended_prompts):
                with col:
                    if st.button(prompt, key=f"dialog_{prompt}"):
                        st.session_state.conversation_started = True
                        st.session_state.messages.append({"role": "user", "content": prompt})
                        st.session_state.selected_prompt = prompt
                        st.rerun()

        # Show dialog only if conversation hasn't started
        if not st.session_state.conversation_started:
            show_recommended_prompts()
        
        # Handle selected prompt after rerun
        if "selected_prompt" in st.session_state:
            history = self.generate_response(st.session_state.selected_prompt)
            self.show_chat_history(history, chat_container)
            del st.session_state.selected_prompt  # Clean up


        # Prompt input
        if prompt := st.chat_input(
                placeholder=self.placeholderstr, key="chat_bot"):
            st.session_state.conversation_started = True
            st.session_state.messages.append(
                {"role": "user", "content": prompt}
            )
            history = self.generate_response(prompt)
            self.show_chat_history(history, chat_container)


if __name__ == "__main__":
    orchestrator = OrchestratorAgent()
    orchestrator.run()
