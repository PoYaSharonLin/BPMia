import streamlit as st

def paging():
    st.page_link("streamlit_app.py", label="Home", icon="🏠")
    st.page_link("pages/rag_agents.py", label="RAG Agent Space", icon="🤖")
    st.page_link("pages/word_cloud.py", label="Word Cloud", icon="☁️")
    st.page_link("pages/documents_upload.py", label="Document Upload", icon="📄")