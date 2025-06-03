import streamlit as st
import requests
from bs4 import BeautifulSoup
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import pandas as pd
from dataclasses import dataclass
from typing import List
from openai import OpenAI
from io import BytesIO
from PyPDF2 import PdfReader
import docx
from utils.ui_helper import UIHelper

# === Setup ===
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
nltk.download('punkt')
nltk.download('stopwords')

@dataclass
class Config:
    WORDCLOUD_WIDTH: int = 800
    WORDCLOUD_HEIGHT: int = 400
    WORDCLOUD_BG_COLOR: str = 'white'
    MIN_FONT_SIZE: int = 10

# === Web scraping and word processing ===
class TextScraper:
    @staticmethod
    @st.cache_data
    def scrape(url: str) -> str:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            paragraphs = soup.find_all('p')
            return ' '.join(p.get_text(strip=True) for p in paragraphs)
        except requests.RequestException as e:
            st.error(f"Failed to scrape webpage: {e}")
            return ""

class TextProcessor:
    @staticmethod
    @st.cache_data
    def preprocess(text: str) -> List[str]:
        text = re.sub(r'[^a-zA-Z\s]', '', text.lower())
        tokens = word_tokenize(text)
        stop_words = set(stopwords.words('english'))
        return [t for t in tokens if t not in stop_words and len(t) > 2]

class WordCloudGenerator:
    def __init__(self, config: Config):
        self.config = config

    def generate(self, tokens: List[str]) -> plt.Figure:
        word_freq = Counter(tokens)
        wordcloud = WordCloud(
            width=self.config.WORDCLOUD_WIDTH,
            height=self.config.WORDCLOUD_HEIGHT,
            background_color=self.config.WORDCLOUD_BG_COLOR,
            min_font_size=self.config.MIN_FONT_SIZE
        ).generate_from_frequencies(word_freq)
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        return fig

    @staticmethod
    def get_top_words(tokens: List[str], n: int = 5) -> pd.DataFrame:
        word_freq = Counter(tokens).most_common(n)
        return pd.DataFrame(word_freq, columns=["Word", "Frequency"])

# === Resume parsing and trait extraction ===
def extract_text_from_file(uploaded_file):
    if uploaded_file.name.endswith(".txt"):
        return uploaded_file.read().decode("utf-8", errors="ignore")
    elif uploaded_file.name.endswith(".pdf"):
        reader = PdfReader(uploaded_file)
        return "\n".join(p.extract_text() for p in reader.pages if p.extract_text())
    elif uploaded_file.name.endswith(".docx"):
        doc = docx.Document(uploaded_file)
        return "\n".join(p.text for p in doc.paragraphs)
    return ""

def extract_traits_from_resume(text: str) -> List[str]:
    prompt = f"""
You are a career coach. From the following resume content, extract the 10 most representative personal traits or work values.

Resume:
{text}

Return a clean comma-separated list like: innovation, collaboration, adaptability, leadership
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        raw = response.choices[0].message.content
        traits = re.split(r",\s*|\n|\d+\.\s*", raw.strip())
        return list(dict.fromkeys(t.lower() for t in traits if t.strip()))
    except Exception as e:
        st.error(f"Error analyzing resume: {e}")
        return []

def compatibility_check_with_openai(top_words: List[str], user_traits: List[str], resume_text: str = "") -> str:
    prompt = f"""
You are a career advisor helping users evaluate compatibility with a company.
The company values (based on word cloud) are: {', '.join(top_words)}.
The user values are: {', '.join(user_traits)}.
Use user values as a reference to their priority.
Use their resume as context to understand their work values.

Resume:
{resume_text}

Evaluate compatibility and respond starting with:
"High", "Moderate", or "Low", followed by a short explanation. Does not need to be bolded.
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ OpenAI Error: {e}"

# === Main App ===
def main():
    UIHelper.config_page()
    UIHelper.setup_sidebar()

    st.title("🌐 Word Cloud & Company Compatibility Checker")
    st.write("Analyze a company's website and compare it with your work values.")

    url = st.text_input("Enter URL to scrape:", value="https://www.iss.nthu.edu.tw/About-us/About--us")
    if not url:
        st.info("Please enter a URL.")
        return

    raw_text = TextScraper.scrape(url)
    tokens = TextProcessor.preprocess(raw_text)
    if not tokens:
        st.warning("No usable text found.")
        return

    generator = WordCloudGenerator(Config())
    st.pyplot(generator.generate(tokens))
    df = generator.get_top_words(tokens)
    st.subheader("Top 5 Most Frequent Words")
    st.table(df)
    top_words = df["Word"].tolist()

    # Resume Upload
    resume_text = ""
    default_traits = [
        "innovation", "diversity", "collaboration", "learning", "integrity",
        "freedom", "respect", "growth", "impact", "flexibility", "discipline", "autonomy"
    ]

    with st.expander("📄 Upload Resume to Auto-Generate Traits"):
        uploaded = st.file_uploader("Upload your resume (.txt, .pdf, .docx)", type=["txt", "pdf", "docx"])
        if uploaded:
            resume_text = extract_text_from_file(uploaded)
            traits = extract_traits_from_resume(resume_text)
            all_traits = list(set(default_traits + traits))
            all_traits.sort()
            # Reset traits
            st.session_state.trait_states = {trait: (trait in traits) for trait in all_traits}
            st.success("Traits extracted from resume:")
            st.write(", ".join(traits))

    # Self-Assessment
    with st.expander("🔍 Self-Assessment: What's important to you at work?"):
        if "trait_states" not in st.session_state:
            all_traits = default_traits
            all_traits.sort()
            st.session_state.trait_states = {trait: False for trait in all_traits}
        if "submit_traits" not in st.session_state:
            st.session_state.submit_traits = False

        cols = st.columns(4)
        for i, trait in enumerate(st.session_state.trait_states.keys()):
            col = cols[i % 4]
            with col:
                st.session_state.trait_states[trait] = st.toggle(
                    trait.title(),
                    value=st.session_state.trait_states.get(trait, False),
                    key=f"toggle_{trait}"
                )

        selected = [k for k, v in st.session_state.trait_states.items() if v]
        st.markdown("---")
        st.write(f"Selected Traits: {', '.join(selected) if selected else 'None'}")

        if st.button("📊 Submit for Compatibility Check"):
            st.session_state.submit_traits = True
            st.session_state.last_submitted_traits = st.session_state.trait_states.copy()

    # Compatibility Result
    if st.session_state.get("submit_traits") and selected:
        result = compatibility_check_with_openai(top_words, selected, resume_text=resume_text)
        lower = result.lower()
        if lower.startswith("high"):
            level, color, border, emoji = "high", "#dcfce7", "#22c55e", "✅"
        elif lower.startswith("low"):
            level, color, border, emoji = "low", "#fee2e2", "#ef4444", "❌"
        else:
            level, color, border, emoji = "moderate", "#fef9c3", "#eab308", "⚠️"

        st.markdown(
            f"""
            <div style="
                background-color: {color};
                border-left: 6px solid {border};
                padding: 20px 24px;
                border-radius: 8px;
                margin-top: 16px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
                color: #111;
                font-size: 1.15em;
                line-height: 1.6;
            ">
                <p style="margin: 0;"><strong>{emoji} Compatibility:</strong> {result}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

if __name__ == "__main__":
    main()
