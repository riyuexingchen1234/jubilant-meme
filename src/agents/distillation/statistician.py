from src.agents.base import BaseAgent

class StatisticianAgent(BaseAgent):
    def __init__(self, llm_client):
        super().__init__(llm_client, "distillation/statistician", temperature=0.2)
