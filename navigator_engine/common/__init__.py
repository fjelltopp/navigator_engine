import networkx
from navigator_engine.model import Graph


def load_graph(graph_id: str):
    graph = Graph.query.filter_by(id=graph_id).first().to_networkx()
    root = [n for n, d in graph.in_degree() if d==0]
    return graph
