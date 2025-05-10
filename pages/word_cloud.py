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

# Initialize page config 
def stream_data(stream_str):
    for word in stream_str.split(" "):
        yield word + " "
        time.sleep(0.05)

def save_lang():
    st.session_state['lang_setting'] = st.session_state.get("language_select")

def paging():
    st.page_link("streamlit_app.py", label="Home", icon="🏠")
    st.page_link("pages/rag_agents.py", label="RAG Agent Space", icon="🤖")
    st.page_link("pages/word_cloud.py", label="Word Cloud", icon="☁️")

def main():
    st.set_page_config(
        page_title='Knowledge Assistant',
        layout='wide',
        initial_sidebar_state='auto',
        menu_items={
            'Get Help': 'https://streamlit.io/',
            'Report a bug': 'https://github.com',
            'About': 'About your application: **Hello world**'
            },
        page_icon="img/favicon.ico"
    )

    # Show title and description.
    st.title(f"💬 {user_name}")

    with st.sidebar:
        paging()

        selected_lang = st.selectbox("Language", ["English", "繁體中文"], index=0, on_change=save_lang, key="language_select")
        if 'lang_setting' in st.session_state:
            lang_setting = st.session_state['lang_setting']
        else:
            lang_setting = selected_lang
            st.session_state['lang_setting'] = lang_setting

        st_c_1 = st.container(border=True)
        with st_c_1:
            st.image("https://www.w3schools.com/howto/img_avatar.png")

    st_c_chat = st.container(border=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []
    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                if user_image:
                    st_c_chat.chat_message(msg["role"],avatar=user_image).markdown((msg["content"]))
                else:
                    st_c_chat.chat_message(msg["role"]).markdown((msg["content"]))
            elif msg["role"] == "assistant":
                st_c_chat.chat_message(msg["role"]).markdown((msg["content"]))
            else:
                try:
                    image_tmp = msg.get("image")
                    if image_tmp:
                        st_c_chat.chat_message(msg["role"],avatar=image_tmp).markdown((msg["content"]))
                except:
                    st_c_chat.chat_message(msg["role"]).markdown((msg["content"]))

# ----------------------------------------------------------------------

# Download required NLTK package
nltk.download('punkt_tab')
nltk.download('stopwords')

# Streamlit app title
st.title("Dynamic Word Cloud Generator")
st.write("This word cloud entails the enterprise culture, which suggests some abilities that the employee should be euipped with.")

# URL input
url = st.text_input("Enter URL to scrape:", value="https://www.iss.nthu.edu.tw/About-us/About--us")

@st.cache_data
def scrape_text(url):
    try:
        # Send a GET request to the URL
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract text from all paragraph tags
        paragraphs = soup.find_all('p')
        text = ' '.join([para.get_text() for para in paragraphs])
        
        return text
    except Exception as e:
        st.error(f"Error scraping the webpage: {e}")
        return ""

@st.cache_data
def preprocess_text(text):
    # Convert to lowercase
    text = text.lower()
    
    # Remove special characters and digits
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    
    # Tokenize the text
    tokens = word_tokenize(text)
    
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words and len(word) > 2]
    
    return tokens

@st.cache_data
def generate_wordcloud(tokens):
    # Count word frequencies
    word_freq = Counter(tokens)
    
    # Generate word cloud
    wordcloud = WordCloud(width=800, height=400,
                         background_color='white',
                         min_font_size=10).generate_from_frequencies(word_freq)
    
    # Create a matplotlib figure
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    
    return fig

# Main app logic
def main():
    if url:
        # Scrape text from the URL
        raw_text = scrape_text(url)
        
        if raw_text:
            # Preprocess the text
            tokens = preprocess_text(raw_text)
            
            if tokens:
                # Generate and display the word cloud
                fig = generate_wordcloud(tokens)
                st.pyplot(fig)
                
                # Display top 5 words in a table
                word_freq = Counter(tokens)
                st.subheader("Top 5 Most Frequent Words")
                # Create a DataFrame for the table
                top_words = word_freq.most_common(5)
                df = pd.DataFrame(top_words, columns=["Word", "Frequency"])
                st.table(df)
            else:
                st.warning("No valid words found after preprocessing.")
        else:
            st.warning("No text could be scraped from the webpage.")
    else:
        st.info("Please enter a URL to generate the word cloud.")

if __name__ == "__main__":
    main()