import os
import google.generativeai as genai
from dotenv import load_dotenv

def generate_ai_response(user_message: str) -> str:
    
    template = """
        [INST] <<SYS>>
        

        You are a helpful AI assistant. Your task is to provide concise and accurate responses to user queries.
        Your name is AI Assistant and you are here to help users with their questions.
        Your Creator is Kaustubh who built this system.


        Input : {prompt}[/INST]
    """

    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))  # Set your Google API key
    prompt = template.format(prompt=user_message)
    model = genai.GenerativeModel('gemini-1.5-flash')  # Adjust model as needed
    response = model.generate_content(prompt)

    # Defensive: handle empty parts gracefully
    text = ""
    try:
        text = response.text or ""
    except Exception:
        text = ""

    if not text.strip():
        text = "I'm here, but I couldn't generate a response right now."
    return text.strip()
