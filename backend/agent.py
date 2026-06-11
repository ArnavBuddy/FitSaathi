from google.cloud import aiplatform
from .config import settings
import google.generativeai as genai
from typing import List, Dict, Any

class AgentClient:
    def __init__(self):
        self.project_id = settings.GOOGLE_PROJECT_ID
        self.location = settings.GOOGLE_LOCATION
        self.agent_id = settings.AGENT_ID
        if self.project_id:
            try:
                aiplatform.init(project=self.project_id, location=self.location)
            except Exception:
                pass

    async def chat(self, user_id: str, message: str, session_id: str, history: List[Dict[str, str]] = [], body_data: Dict[str, Any] = {}) -> str:
        """
        Routes to Gemini directly for this demo, simulating Vertex AI Agent Builder.
        """
        if not settings.GOOGLE_API_KEY:
            return "I'm sorry, my AI brain isn't connected yet (missing GOOGLE_API_KEY). Please set up your .env file."

        genai.configure(api_key=settings.GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Load system prompt
        try:
            with open("agent_config/system_prompt.txt", "r") as f:
                system_prompt = f.read()
        except FileNotFoundError:
            system_prompt = "You are FitSaathi, a warm and expert AI personal stylist."

        context = f"\n\nUser Body Data: {body_data}\n" if body_data else ""
        
        chat = model.start_chat(history=[]) # Simplified history handling for demo
        
        full_prompt = f"{system_prompt}{context}\nUser: {message}"
        
        try:
            response = chat.send_message(full_prompt)
            return response.text
        except Exception as e:
            return f"I'm sorry, I'm having trouble connecting right now. Error: {str(e)}"

agent_client = AgentClient()
