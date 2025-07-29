# On Boarding Mentor 

Demo: https://on-boarding-mentor.streamlit.app/


## How to run it on your own machine

###  01 Setup virtual environment 
setup
```bash
python3 -m venv venv
```

activate
```bash
source venv/bin/activate
```

### 02 Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

### 03 Apply for API key 
Apply API key from: https://aistudio.google.com/app/apikey

Replace <YOUR API KEY> with your real API key in `.streamlit/secrets.toml` file:

```bash
GEMINI1_API_KEY = "<YOUR API KEY>"
GEMINI2_API_KEY = "<YOUR API KEY>"
```


### 04 Run the app

   ```
   $ streamlit run streamlit_app.py
   ```

### 05 Test the app 
```bash
   $ pytest tests/
```


### 06 For Developers 

VS Code Extensions

- Pylance: auto-completions, type checking
- Ruff: code linting
- Black Formatter: code formatting
- Better Comments: better comments
- Live Preview: live preview of the app


