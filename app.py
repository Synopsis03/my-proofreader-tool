import os
from flask import Flask, render_template, request
from markupsafe import Markup
from google import genai

app = Flask(__name__)

# --- 1. API KEY CHECK AND CLIENT SETUP ---
# The client automatically reads the GEMINI_API_KEY from the environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    # If the key isn't set, this will print an error
    raise ValueError("GEMINI_API_KEY environment variable not set. Please set it in your terminal.")

# Initialize the Gemini Client
client = genai.Client(api_key=GEMINI_API_KEY)


# --- 2. FUNCTION FOR THE 'WORD COUNT ONLY' BUTTON ---

def get_word_count(content):
    """A simple Python function to count words locally, no API call needed."""
    word_count = len(content.split())
    return Markup(f"### 2. Word Count Result\nYour content contains **{word_count}** words.")


# --- 3. FUNCTION FOR THE 'PROOFREAD CONTENT' BUTTON (GEMINI API CALL) ---

def get_proofreading_result(content, dialect, style_guide):
    """Constructs the Master Prompt and calls the Gemini API."""

    # This is your final, complete prompt injected with user choices
    master_prompt = f"""
    # ✨ Final Master Proofreading Prompt (Model Instructions) ✨

    ROLE: Act as an expert, highly constrained copyeditor.

    GOAL: Proofread the provided text (below) to eliminate all errors.

    ### I. Style and Context
    * **Style Rule:** Adhere strictly to {dialect} spelling/grammar and the rules of {style_guide} for punctuation and formatting (e.g., spacing, titles).

    ### II. Core Constraints (Non-Negotiable)
    1.  **No Rephrasing:** Fix errors without altering the original sentence structure or meaning.
    2.  **Word Count (Max 250):** If content exceeds 250 words, reduction must be achieved *only* by removing redundant words/phrases (no rephrasing).
    3.  **Inevitable Changes:** If a critical change violates Constraint 1, a 3-sentence justification **must** be included in the final output.

    ### III. Required Output Format

    Provide your response using the following four headings, in this exact order. Use Markdown formatting (like bolding and lists) for clarity under each heading:

    **1. Error Severity Score:**

    **2. Proofread Content:**

    **3. Log of Changes:**

    **4. Justification for Inevitable Changes:**

    ---
    **Content to Proofread:**

    {content}
    """

    try:
        # This is the core API call
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=master_prompt
        )
        return Markup(response.text)

    except Exception as e:
        return Markup(f"### ⚠️ API Error\nCould not process the request. Check your API Key and terminal connection: {e}")


# --- 4. FLASK WEB ROUTES (Handles the Button Logic) ---

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None

    if request.method == 'POST':
        # Get data from the HTML form
        text_content = request.form['text_content']
        dialect = request.form['dialect']
        style_guide = request.form['style_guide']

        # Check which button was pressed using the 'name="action"' from the HTML
        submitted_action = request.form.get('action') 

        if submitted_action == 'proofread':
            result = get_proofreading_result(text_content, dialect, style_guide)

        elif submitted_action == 'count':
            result = get_word_count(text_content)

    return render_template('index.html', result=result)

# --- 5. RUN THE APP ---
if __name__ == '__main__':
    app.run(debug=True)