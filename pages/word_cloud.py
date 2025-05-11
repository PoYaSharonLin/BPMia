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
<<<<<<< HEAD
from dataclasses import dataclass
from typing import List, Optional, Dict
from utils.ui_helper import UIHelper
=======
import time
from components.navigation import paging
>>>>>>> 5d36152 (chore: remove chat function)

# Download NLTK data
nltk.download('punkt_tab')
nltk.download('stopwords')

@dataclass
class Config:
    """Configuration settings for the word cloud app."""
    WORDCLOUD_WIDTH: int = 800
    WORDCLOUD_HEIGHT: int = 400
    WORDCLOUD_BG_COLOR: str = 'white'
    MIN_FONT_SIZE: int = 10
    
class TextScraper:
    """Handles web scraping functionality."""
    
    @staticmethod
    @st.cache_data
    def scrape(url: str) -> str:
        """Scrapes text from paragraphs on a webpage."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            paragraphs = soup.find_all('p')
            return ' '.join(para.get_text(strip=True) for para in paragraphs)
        except requests.RequestException as e:
            st.error(f"Failed to scrape webpage: {e}")
            return ""

class TextProcessor:
    """Handles text preprocessing and tokenization."""
    
    @staticmethod
    @st.cache_data
    def preprocess(text: str) -> List[str]:
        """Preprocesses text by cleaning, tokenizing, and removing stopwords."""
        # Convert to lowercase and remove non-alphabetic characters
        text = re.sub(r'[^a-zA-Z\s]', '', text.lower())
        # Tokenize
        tokens = word_tokenize(text)
        # Remove stopwords and short words
        stop_words = set(stopwords.words('english'))
        return [word for word in tokens if word not in stop_words and len(word) > 2]

class WordCloudGenerator:
    """Generates word cloud visualizations and frequency tables."""
    
    def __init__(self, config: Config):
        self.config = config
    
    @st.cache_data
    def generate(_self, tokens: List[str]) -> plt.Figure:
        """Generates a word cloud from tokenized text."""
        word_freq = Counter(tokens)
        wordcloud = WordCloud(
            width=_self.config.WORDCLOUD_WIDTH,
            height=_self.config.WORDCLOUD_HEIGHT,
            background_color=_self.config.WORDCLOUD_BG_COLOR,
            min_font_size=_self.config.MIN_FONT_SIZE
        ).generate_from_frequencies(word_freq)
        
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        return fig
    
    @staticmethod
    def get_top_words(tokens: List[str], n: int = 5) -> pd.DataFrame:
        """Returns a DataFrame of the top N most frequent words."""
        word_freq = Counter(tokens).most_common(n)
        return pd.DataFrame(word_freq, columns=["Word", "Frequency"])
    
    @staticmethod
    def get_top_words(tokens: List[str], n: int = 5) -> pd.DataFrame:
        """Returns a DataFrame of the top N most frequent words."""
        word_freq = Counter(tokens).most_common(n)
        return pd.DataFrame(word_freq, columns=["Word", "Frequency"])

<<<<<<< HEAD
class WordCloudApp:
    """Main application class for the word cloud generator."""
    
    def __init__(self):
        self.config = Config()
        self.scraper = TextScraper()
        self.processor = TextProcessor()
        self.generator = WordCloudGenerator(self.config)
    
    def run(self):
        """Runs the Streamlit word cloud application."""
        st.title("Dynamic Word Cloud Generator")
        st.write("Visualize key themes in enterprise culture from webpage text.")
        
        default_url = "https://www.iss.nthu.edu.tw/About-us/About--us"
        url = st.text_input("Enter URL to scrape:", value=default_url)
        
        if not url:
            st.info("Please enter a URL to generate the word cloud.")
            return
        
        # Scrape and process text
        raw_text = self.scraper.scrape(url)
        if not raw_text:
=======
        # User profile container
        st_c_1 = st.container(border=True)
        with st_c_1:
            st.image("https://www.w3schools.com/howto/img_avatar.png")

# Save language setting
def save_lang():
    st.session_state['lang_setting'] = st.session_state.get("language_select")

# Word cloud generation functions
@st.cache_data
def scrape_text(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        text = ' '.join([para.get_text() for para in paragraphs])
        return text
    except Exception as e:
        st.error(f"Error scraping the webpage: {e}")
        return ""

@st.cache_data
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    tokens = word_tokenize(text)
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words and len(word) > 2]
    return tokens

@st.cache_data
def generate_wordcloud(tokens):
    word_freq = Counter(tokens)
    wordcloud = WordCloud(width=800, height=400,
                         background_color='white',
                         min_font_size=10).generate_from_frequencies(word_freq)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    return fig

# Word cloud app logic
def word_cloud_app():
    st.title("Dynamic Word Cloud Generator")
    st.write("This word cloud entails the enterprise culture, which suggests some abilities that employees should be equipped with.")

    url = st.text_input("Enter URL to scrape:", value="https://www.iss.nthu.edu.tw/About-us/About--us")

    if url:
        raw_text = scrape_text(url)
        if raw_text:
            tokens = preprocess_text(raw_text)
            if tokens:
                fig = generate_wordcloud(tokens)
                st.pyplot(fig)
                
                st.subheader("Top 5 Most Frequent Words")
                word_freq = Counter(tokens)
                top_words = word_freq.most_common(5)
                df = pd.DataFrame(top_words, columns=["Word", "Frequency"])
                st.table(df)
            else:
                st.warning("No valid words found after preprocessing.")
        else:
>>>>>>> 5d36152 (chore: remove chat function)
            st.warning("No text could be scraped from the webpage.")
            return
        
        tokens = self.processor.preprocess(raw_text)
        if not tokens:
            st.warning("No valid words found after preprocessing.")
            return
        
        # Generate and display word cloud
        fig = self.generator.generate(tokens)
        st.pyplot(fig)
        
        # Display top words
        st.subheader("Top 5 Most Frequent Words")
        df = self.generator.get_top_words(tokens)
        st.table(df)

def main():
<<<<<<< HEAD
    """Main entry point for the Streamlit application."""
    UIHelper.config_page()
    UIHelper.setup_sidebar()
    UIHelper.setup_chat()
    app = WordCloudApp()
    app.run()
=======
    config_page()  # Set up page configuration
    setup_sidebar()  # Set up sidebar
    word_cloud_app()  # Run word cloud generator
>>>>>>> 5d36152 (chore: remove chat function)

if __name__ == "__main__":
    main()