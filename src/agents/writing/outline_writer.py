from src.agents.base import BaseAgent

class OutlineWriterAgent(BaseAgent):
    def __init__(self, llm_client):
        super().__init__(llm_client, "writing/outline_writer", temperature=0.7, max_tokens=4096)
