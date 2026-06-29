from src.agents.base import BaseAgent

class MaterialMatcherAgent(BaseAgent):
    def __init__(self, llm_client):
        super().__init__(llm_client, "writing/material_matcher", temperature=0.4)
