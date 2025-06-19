import streamlit as st  # type: ignore
import time
from autogen.code_utils import content_str  # type: ignore
from utils.ui_helper import UIHelper
from utils.llm_setup import LLMSetup  # type: ignore


class OrchestratorAgent:
    def __init__(self):
        self.user_name = "Mentor"
        self.assistant_avatar = "🧠"
        self.user_avatar = "https://www.w3schools.com/howto/img_avatar.png"
        self.placeholderstr = "Please input your command"
        UIHelper.config_page()
        self._load_api_keys()
        self._setup_llm()

    def _load_api_keys(self):
        self.gemini1_api_key, self.gemini2_api_key = LLMSetup.load_api_keys()

    def _setup_llm(self):
        self.assistant = LLMSetup.create_assistant(
            system_message=(
                "'This website helps you get familiar with onboarding"
                "website allows you to: "
                "1. Visualize the enterprise culture, "
                "2. Understand organization stakeholders, and "
                "3. Grow with the company using your personal note.' "
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
        st.title(f"💬 {self.user_name}")
        UIHelper.setup_sidebar()
        chat_container = st.container()

        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Render chat history
        for i, msg in enumerate(st.session_state.messages):
            # Skip the last message if it's a user input just rendered above
            if (
                i == len(st.session_state.messages) - 1
                and msg["role"] in ["user", "user_proxy"]
            ):
                continue
            role = msg["role"]
            content = msg["content"]
            if role in ["user", "user_proxy"]:
                chat_container.chat_message(
                    "user", avatar=self.user_avatar
                ).markdown(f"**{content}**")
            else:
                chat_container.chat_message(
                    "assistant", avatar=self.assistant_avatar
                ).markdown(content)

        # Prompt input
        if prompt := st.chat_input(
                placeholder=self.placeholderstr, key="chat_bot"):
            st.session_state.messages.append(
                {"role": "user", "content": prompt}
            )
            history = self.generate_response(prompt)
            self.show_chat_history(history, chat_container)


if __name__ == "__main__":
    orchestrator = OrchestratorAgent()
    orchestrator.run()
