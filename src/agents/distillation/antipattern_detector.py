from src.agents.base import BaseAgent

class AntipatternDetectorAgent(BaseAgent):
    def __init__(self, llm_client):
        super().__init__(llm_client, "distillation/antipattern_detector", temperature=0.3)
