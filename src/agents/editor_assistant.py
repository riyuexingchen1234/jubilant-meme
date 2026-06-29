from src.agents.base import BaseAgent

class EditorAssistantAgent(BaseAgent):
    def __init__(self, llm_client):
        super().__init__(llm_client, "editor_assistant/system", temperature=0.5, max_tokens=2048)
