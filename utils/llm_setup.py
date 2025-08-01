import streamlit as st  # type: ignore
from dotenv import load_dotenv  # type: ignore
from autogen import LLMConfig, AssistantAgent, UserProxyAgent  # type: ignore
from autogen.code_utils import content_str  # type: ignore


class LLMSetup:
    @staticmethod
    @st.cache_resource
    def load_api_keys():
        """Load API keys from environment and Streamlit secrets."""
        load_dotenv(override=True)
        gemini1 = st.secrets["GEMINI1_API_KEY"]
        gemini2 = st.secrets["GEMINI2_API_KEY"]
        return gemini1, gemini2

    @staticmethod
    @st.cache_resource
    def create_llm_config(
        api_key: str,
        model: str = "gemini-2.0-flash-lite"
    ) -> LLMConfig:
        """Return a basic LLMConfig for the given API key."""
        return LLMConfig(api_type="google", model=model, api_key=api_key, temperature=0.3)

    @staticmethod
    def create_assistant(system_message: str, api_key: str) -> AssistantAgent:
        """Create an AssistantAgent with the default configuration."""
        return AssistantAgent(
            name="assistant",
            system_message=system_message,
            llm_config=LLMSetup.create_llm_config(api_key),
            max_consecutive_auto_reply=1,
        )

    @staticmethod
    def create_user_proxy(is_termination_msg=None) -> UserProxyAgent:
        """Create a UserProxyAgent used for chat sessions."""
        if is_termination_msg is None:
            def default_termination_msg(x):
                return "ALL DONE" in content_str(
                    x.get("content", "")
                )
            is_termination_msg = default_termination_msg

        return UserProxyAgent(
            name="user_proxy",
            human_input_mode="NEVER",
            code_execution_config=False,
            is_termination_msg=is_termination_msg,
        )
