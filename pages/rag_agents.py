import streamlit as st
from openai import OpenAI
import time
import re
from dotenv import load_dotenv
import os
import re

# Import ConversableAgent class
import autogen
from autogen import ConversableAgent, LLMConfig, Agent
from autogen import AssistantAgent, UserProxyAgent, LLMConfig
from autogen.code_utils import content_str
from coding.constant import JOB_DEFINITION, RESPONSE_FORMAT
from components.navigation import paging
from utils.ui_helper import UIHelper

# Load environment variables from .env file
# load_dotenv(override=True)

# https://ai.google.dev/gemini-api/docs/pricing
# URL configurations
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

placeholderstr = "Please input your command"
user_name = "Mentor"
user_image = "https://www.w3schools.com/howto/img_avatar.png"
assistant_image = "https://www.w3schools.com/howto/img_avatar2.png"

seed = 42

llm_config_gemini = LLMConfig(
    api_type = "google", 
    model="gemini-2.0-flash-lite",                    # The specific model
    api_key=GEMINI_API_KEY,   # Authentication
)

llm_config_openai = LLMConfig(
    api_type = "openai", 
    model="gpt-4o-mini",                    # The specific model
    api_key=OPENAI_API_KEY,   # Authentication
)

with llm_config_gemini:
    student_agent = ConversableAgent(
        name="GraphRAG_Agent",
        system_message="You are a GraphRAG Agent specializing in querying an organizational structure stored in a graph database. Your role is to answer questions about employees, such as their email, position, or reporting relationships. Use precise and accurate information retrieved from the graph database to respond. If the query is unclear or the information is unavailable, politely explain and ask for clarification.",
    )
    teacher_agent = ConversableAgent(
        name="TextRAG_Agent",
        system_message="You are a TextRAG Agent designed to answer questions based on personal markdown notes. Your role is to retrieve relevant information from the notes and provide clear, concise answers. Focus on understanding the context of the notes and delivering responses that align with the user's intent. If the notes lack relevant information, inform the user and suggest rephrasing or providing more details.",
    )

user_proxy = UserProxyAgent(
    "user_proxy",
    human_input_mode="NEVER",
    code_execution_config=False,
    is_termination_msg=lambda x: content_str(x.get("content")).find("ALL DONE") >= 0,
)

def load_uploaded_docs():
    """Load all markdown files from uploaded_docs/personal and uploaded_docs/org."""
    base_dirs = {
        "personal": "uploaded_docs/personal",
        "org": "uploaded_docs/org"
    }

    docs = {"personal": {}, "org": {}}

    for category, path in base_dirs.items():
        if os.path.exists(path):
            for fname in os.listdir(path):
                if fname.endswith(".md"):
                    with open(os.path.join(path, fname), "r", encoding="utf-8") as f:
                        docs[category][fname] = f.read()
    return docs

def stream_data(stream_str):
    for word in stream_str.split(" "):
        yield word + " "
        time.sleep(0.05)

def save_lang():
    st.session_state['lang_setting'] = st.session_state.get("language_select")

def main():
    UIHelper.config_page()
    UIHelper.setup_sidebar()

    user_name = "Mentor"
    user_image = "https://www.w3schools.com/howto/img_avatar.png"
    st.title(f"💬 {user_name}")
    st_c_chat = st.container(border=True)
    UIHelper.setup_chat()

    def extract_mermaid_blocks(markdown_text):
        """Extract only the Mermaid code blocks from a markdown string."""
        pattern = r"```mermaid\n(.*?)```"
        return re.findall(pattern, markdown_text, re.DOTALL)

    def generate_response(prompt):
        docs = load_uploaded_docs()

        prompt_lower = prompt.lower()
        is_org_related = any(keyword in prompt_lower for keyword in [
            "org", "organization", "structure", "team", "manager", "lead", "report", "department", "chart"
        ])

        def should_stop(chat_history):
            last_few = [msg["content"].strip().lower() for msg in chat_history[-3:] if msg["role"] == "assistant"]
            generic_phrases = [
                "i'm unable to answer", 
                "i am sorry", 
                "please rephrase", 
                "notes do not contain", 
                "could you please provide"
            ]
            return all(any(generic in resp for generic in generic_phrases) for resp in last_few)

        if is_org_related:
            mermaid_blocks = []
            for content in docs.get("org", {}).values():
                mermaid_blocks += extract_mermaid_blocks(content)

            mermaid_diagrams = "\n\n".join(f"```mermaid\n{block}\n```" for block in mermaid_blocks)

            final_prompt = (
                "Based on the following organization charts, answer the user's question. "
                "Only use this information to determine reporting lines, structure, or team relationships:\n\n"
                f"{mermaid_diagrams}\n\nUser's question: {prompt}"
            )

            response = student_agent.initiate_chat(
                user_proxy,
                message=final_prompt,
                summary_method="reflection_with_llm",
                max_turns=3  # Reduce if desired
            )
            if should_stop(response.chat_history):
                response.chat_history.append({"role": "assistant", "content": "Ending the chat as no relevant answer can be provided."})
            return response.chat_history

        else:
            personal_content = "\n\n".join(
                f"# {fname}\n{content}" 
                for fname, content in docs.get("personal", {}).items()
            )

            final_prompt = (
                "Use the following personal notes to answer the user's question:\n\n"
                f"{personal_content}\n\nUser's question: {prompt}"
            )

            response = teacher_agent.initiate_chat(
                user_proxy,
                message=final_prompt,
                summary_method="reflection_with_llm",
                max_turns=3
            )
            if should_stop(response.chat_history):
                response.chat_history.append({"role": "assistant", "content": "Ending the chat as no helpful answer can be provided."})
            return response.chat_history

    def show_chat_history(chat_history):
        for entry in chat_history:
            role = entry.get("role", "assistant")
            content = entry.get("content", "").strip()

            # Add to session state for future reference
            st.session_state.messages.append({"role": role, "content": content})

            if not content:
                continue

            # Display with appropriate avatar
            if role == "user":
                st_c_chat.chat_message("user", avatar=user_image).markdown(content)
            elif role == "assistant":
                st_c_chat.chat_message("assistant", avatar=assistant_image).markdown(content)
            else:
                # Fallback: use generic avatar if available or none
                st_c_chat.chat_message(role).markdown(content)

    # Chat function section (timing included inside function)
    def chat(prompt: str):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st_c_chat.chat_message("user", avatar=user_image).markdown(prompt)

        response = generate_response(prompt)
        show_chat_history(response)


    if prompt := st.chat_input(placeholder=placeholderstr, key="chat_bot"):
        chat(prompt)

if __name__ == "__main__":
    main()
