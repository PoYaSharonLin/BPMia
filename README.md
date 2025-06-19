# 💬 Chatbot template

A simple Streamlit app that shows how to build a chatbot using OpenAI's GPT-3.5.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://chatbot-template.streamlit.app/)

### How to run it on your own machine

1. Setup virtual environment 
setup
```bash
python3 -m venv venv
```

activate
```bash
source venv/bin/activate
```

2. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

3. Apply for API key 
Apply API key from: 
- https://aistudio.google.com/app/apikey

Replace <YOUR API KEY> with your real API key in `.streamlit/secrets.toml` file:

```bash
GEMINI1_API_KEY = "<YOUR API KEY>"
GEMINI2_API_KEY = "<YOUR API KEY>"
```


4. Run the app

   ```
   $ streamlit run streamlit_app.py
   ```

### Live Demo
https://main-deploy.streamlit.app/



5. For Developers 

VS Code Extensions

- Pylance: auto-completions, type checking
- Ruff: code linting
- Black Formatter: code formatting
- Better Comments: better comments
- Live Preview: live preview of the app


