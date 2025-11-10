# TeachingAssistant/src/memory/knowledge_graph_adapter.py
import networkx as nx
import time
from typing import Dict, Any, List

class KnowledgeGraphAdapter:
    def __init__(self):
        self.g = nx.DiGraph()

    def add_utterance_node(self, utt_id: str, text: str, metadata: Dict[str,Any]):
        self.g.add_node(utt_id, text=text, ts=time.time(), **metadata)

    def link_nodes(self, from_id: str, to_id: str, relation: str = "next"):
        self.g.add_edge(from_id, to_id, relation=relation)

    def get_conversation_flow(self, last_n: int = 50) -> List[Dict[str,Any]]:
        nodes = [(n, d) for n,d in self.g.nodes(data=True)]
        nodes.sort(key=lambda x: x[1].get("ts",0))
        flow = []
        for n,d in nodes[-last_n:]:
            flow.append({"id": n, "text": d.get("text",""), "meta": {k:v for k,v in d.items() if k!='text'}})
        return flow
