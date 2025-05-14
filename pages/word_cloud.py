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
from nltk import pos_tag
import pandas as pd
from dataclasses import dataclass
from typing import List, Optional, Dict
from utils.ui_helper import UIHelper
import os, nltk

# Download NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger_eng')
nltk.data.path.append(os.path.join(os.getcwd(), "nltk_data"))

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
        """Preprocesses text by cleaning, tokenizing, and keeping only adjectives and adverbs."""
        # Convert to lowercase and remove non-alphabetic characters
        text = re.sub(r'[^a-zA-Z\s]', '', text.lower())
        # Tokenize
        tokens = word_tokenize(text)
        # Remove stopwords and short words
        stop_words = set(stopwords.words('english'))
        filtered_tokens = [word for word in tokens if word not in stop_words and len(word) > 2]
        # POS tagging
        tagged_tokens = pos_tag(filtered_tokens)
        # Keep only adjectives (JJ*) and adverbs (RB*)
        allowed_tags = ('JJ', 'JJR', 'JJS', 'RB', 'RBR', 'RBS')
        return [word for word, tag in tagged_tokens if tag.startswith(allowed_tags)]

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
        
        default_url = "https://research.google/philosophy"
        url = st.text_input("Enter URL to scrape:", value=default_url)
        
        if not url:
            st.info("Please enter a URL to generate the word cloud.")
            return
        
        # Scrape and process text
        raw_text = self.scraper.scrape(url)
        if not raw_text:
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
    """Main entry point for the Streamlit application."""
    UIHelper.setup_sidebar()
    app = WordCloudApp()
    app.run()

if __name__ == "__main__":
    main()