from flask_sqlalchemy import SQLAlchemy
import networkx

db = SQLAlchemy()


class Graph(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    version = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    edges = db.relationship("Edge", back_populates="graph")

    def to_networkx(self):
        network = networkx.DiGraph()
        network.add_edges_from([edge.tuple() for edge in self.edges])
        self.network = network
        return network


class Conditional(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ref = db.Column(db.String)
    title = db.Column(db.String)
    function = db.Column(db.String)
    nodes = db.relationship("Node", back_populates="conditional")


class Action(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    html = db.Column(db.String)
    skippable = db.Column(db.Boolean, default=False)
    action_url = db.Column(db.String)
    complete = db.Column(db.Boolean, default=False)
    nodes = db.relationship("Node", back_populates="action")


class Milestone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    graph_id = db.Column(db.Integer, db.ForeignKey('graph.id'))
    data_loader = db.Column(db.String)
    nodes = db.relationship("Node", back_populates="milestone")


class Node(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conditional_id = db.Column(db.Integer, db.ForeignKey('conditional.id'))
    action_id = db.Column(db.Integer, db.ForeignKey('action.id'))
    milestone_id = db.Column(db.Integer, db.ForeignKey('milestone.id'))
    action = db.relationship("Action", back_populates="nodes")
    conditional = db.relationship("Conditional", back_populates="nodes")
    milestone = db.relationship("Milestone", back_populates="nodes")

    def __hash__(self):
        return self.id


class Edge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    graph_id = db.Column(db.Integer,  db.ForeignKey('graph.id'), nullable=False)
    from_id = db.Column(db.Integer, db.ForeignKey('node.id'), nullable=False)
    to_id = db.Column(db.Integer, db.ForeignKey('node.id'), nullable=False)
    type = db.Column(db.Boolean, nullable=False)
    graph = db.relationship("Graph", back_populates="edges")
    from_node = db.relationship("Node", foreign_keys=[from_id])
    to_node = db.relationship("Node", foreign_keys=[to_id])

    def tuple(self):
        return (self.from_node, self.to_node, {'type': self.type, 'object': self})


def load_graph(graph_id: int) -> Graph:
    return Graph.query.filter_by(id=graph_id).first()
