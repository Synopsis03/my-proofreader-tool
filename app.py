import os
import markdown2
from flask import Flask, render_template, request
from markupsafe import Markup
from google import genai
from openai import OpenAI

app = Flask(__name__)

# --- 1. Clients Setup ---
# Gemini Client
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Grok (xAI) Client - This replaces OpenAI
grok_client = OpenAI(
    api_key=os.getenv("GROK_API_KEY"),
    base_url="https://api.x.ai/v1"
)

# --- 2. Logic Functions ---
def get_proofreading_result(content, dialect, style_guide, model_choice):
    master_prompt = f"""
    Act as an expert editor. Proofread this {dialect} text using {style_guide} rules.
    Use Markdown: '###' for headers, '**' for bold, and '-' for bullet points.
    
    CONTENT: {content}
    """

    try:
        # Check if the user selected 'grok' in the dropdown
        if model_choice == 'grok':
            response = grok_client.chat.completions.create(
                model="grok-beta",
                messages=[{"role": "user", "content": master_prompt}]
            )
            raw_text = response.choices[0].message.content
        else:
            # Default to Gemini if 'gemini' is selected
            response = gemini_client.models.generate_content(
                model='gemini-2.0-flash', 
                contents=master_prompt
            )
            raw_text = response.text

        # Fix the "One Huge Paragraph" issue by converting Markdown to HTML
        formatted_html = markdown2.markdown(raw_text)
        return Markup(formatted_html)

    except Exception as e:
        # Handle the 503 Overloaded or API errors gracefully
        error_msg = f"### ⚠️ API Error\nCould not process the request. {str(e)}"
        return Markup(markdown2.markdown(error_msg))

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        text_content = request.form.get('text_content')
        dialect = request.form.get('dialect')
        style_guide = request.form.get('style_guide')
        model_choice = request.form.get('model_choice')
        
        if request.form.get('action') == 'proofread':
            result = get_proofreading_result(text_content, dialect, style_guide, model_choice)
            
    return render_template('index.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)