import streamlit as st
st.set_page_config(page_title="📄 Upload Notes & Org Charts", layout="centered")

import os

def paging():
    st.page_link("streamlit_app.py", label="🏠 Home")
    st.page_link("pages/rag_agents.py", label="🤖 RAG Agent Space")
    st.page_link("pages/documents_upload.py", label="📄 Document Upload")

with st.sidebar:
    paging()

st.title("📄 Upload Your Documents")

# select doc type
doc_type = st.radio("Select Upload Category", ["Personal Notes", "Organizational Structure"])

# select doc path based on doc type
doc_folder = "personal" if doc_type == "Personal Notes" else "org"
upload_dir = f"uploaded_docs/{doc_folder}"
os.makedirs(upload_dir, exist_ok=True)

# display the number of uploaded files of selected doc type
uploaded_files = [f for f in os.listdir(upload_dir) if f.endswith(".md")]
st.sidebar.markdown(f"📁 **{doc_type} Files Uploaded:** `{len(uploaded_files)}`")

# dropdown to display uploaded files
with st.expander(f"📄 View uploaded files in {doc_type}"):
    if uploaded_files:
        for fname in uploaded_files:
            st.markdown(f"- `{fname}`")
    else:
        st.info("No files uploaded yet.")

# uploaded files block
uploaded_file = st.file_uploader(
    f"Upload your markdown (.md) file for {doc_type}",
    type=["md"]
)

# save and preview uploaded file
if uploaded_file is not None:
    file_path = os.path.join(upload_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success("✅ Upload Successfully!")
    st.markdown(f"**File saved as:** `{uploaded_file.name}`")

    st.subheader("📝 File Preview")
    file_content = uploaded_file.getvalue().decode("utf-8")
    st.markdown(file_content, unsafe_allow_html=False)
