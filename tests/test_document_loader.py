
import importlib
import streamlit.file_util as file_util  # type: ignore
import streamlit as st  # type: ignore

import pages.rag_agents as rag_agents
importlib.reload(rag_agents)


def setup_secrets(tmp_path, monkeypatch):
    secret_file = tmp_path / 'secrets.toml'
    secret_file.write_text(
        'GEMINI1_API_KEY = "dummy"\n'
        'GEMINI2_API_KEY = "dummy"'
    )
    monkeypatch.setattr(
        file_util,
        'get_project_streamlit_file_path',
        lambda name: str(secret_file)
    )
    monkeypatch.setattr(
        file_util, 'get_streamlit_file_path',
        lambda name: str(secret_file)
    )
    importlib.reload(st.runtime.secrets)
    monkeypatch.setattr(
        'utils.llm_setup.LLMSetup.load_api_keys',
        lambda: ("dummy", "dummy")
    )
    return secret_file


def test_load_documents(monkeypatch, tmp_path):
    setup_secrets(tmp_path, monkeypatch)

    docs = rag_agents.DocumentLoader.load_documents()
    assert 'personal' in docs
    assert 'org' in docs
    assert len(docs['personal']) >= 1
    assert len(docs['org']) >= 1
