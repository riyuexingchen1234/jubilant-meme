from src.agents.base import BaseAgent

class WriterAgent(BaseAgent):
    def __init__(self, llm_client):
        super().__init__(llm_client, "writing/writer", temperature=0.8, max_tokens=8192)
