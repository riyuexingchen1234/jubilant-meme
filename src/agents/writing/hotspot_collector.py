from src.agents.base import BaseAgent

class HotspotCollectorAgent(BaseAgent):
    def __init__(self, llm_client):
        super().__init__(llm_client, "writing/hotspot_collector", temperature=0.4)
