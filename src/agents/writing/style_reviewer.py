from src.agents.base import BaseAgent

class StyleReviewer(BaseAgent):
    def __init__(self, llm_client):
        super().__init__(llm_client, "writing/reviewers/style_reviewer", temperature=0.3)
