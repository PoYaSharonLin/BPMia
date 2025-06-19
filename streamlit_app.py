import streamlit as st  # type: ignore
import time
from dotenv import load_dotenv  # type: ignore
from autogen import AssistantAgent, UserProxyAgent, LLMConfig  # type: ignore
from autogen.code_utils import content_str  # type: ignore
from utils.ui_helper import UIHelper


class OrchestratorAgent:
    def __init__(self):
        self.user_name = "Mentor"
        self.assistant_avatar = "🧠"
        self.user_avatar = "https://www.w3schools.com/howto/img_avatar.png"
        self.placeholderstr = "Please input your command"
        self._load_environment()
        UIHelper.config_page()
        self._setup_llm_configs()
        self._initialize_agents()

    def _load_environment(self):
        load_dotenv(override=True)
        self.gemini1_api_key = st.secrets["GEMINI1_API_KEY"]
        self.gemini2_api_key = st.secrets["GEMINI2_API_KEY"]

    def _setup_llm_configs(self):
        self.llm_config_gemini = LLMConfig(
            api_type="google",
            model="gemini-2.0-flash-lite",
            api_key=self.gemini1_api_key
        )

    def _initialize_agents(self):
        self.assistant = AssistantAgent(
            name="assistant",
            system_message=(
                "'This website helps you get familiar with onboarding"
                "website allows you to: "
                "1. Visualize the enterprise culture, "
                "2. Understand organization stakeholders, and "
                "3. Grow with the company using your personal note.' "
                "Answer all user questions in a concise and helpful."
            ),
            llm_config=self.llm_config_gemini,
            max_consecutive_auto_reply=1
        )

        self.user_proxy = UserProxyAgent(
            name="user_proxy",
            human_input_mode="NEVER",
            code_execution_config=False,
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
