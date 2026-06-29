from src.agents.base import BaseAgent

class RationalityReviewer(BaseAgent):
    def __init__(self, llm_client):
        super().__init__(llm_client, "writing/reviewers/rationality_reviewer", temperature=0.3)
