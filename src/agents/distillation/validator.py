from src.agents.base import BaseAgent

class DistillationValidatorAgent(BaseAgent):
    def __init__(self, llm_client):
        super().__init__(llm_client, "distillation/validator", temperature=0.4)
