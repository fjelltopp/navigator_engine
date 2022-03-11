from flask_sqlalchemy import SQLAlchemy, orm
from flask_sqlalchemy.model import DefaultMeta
import sqlalchemy_utils
from flask_babel import get_locale
from sqlalchemy_i18n import (
    make_translatable,
    translation_base,
    Translatable,
)
from sqlalchemy_i18n.manager import BaseTranslationMixin
import networkx
import os

db = SQLAlchemy()

BaseModel: DefaultMeta = db.Model

sqlalchemy_utils.i18n.get_locale = get_locale

languages = os.environ.get('NAVIGATOR_LANGUAGES', 'en,fr,pt_PT').split(',')
default_language = os.environ.get('NAVIGATOR_DEFAULT_LANGUAGE', 'en')

make_translatable(options={'locales': languages})


class Graph(Translatable, BaseModel):
    __translatable__ = {'locales': languages}
    locale = default_language

    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String, nullable=False)
    edges = db.relationship("Edge", back_populates="graph")

    def to_networkx(self):
        network = networkx.DiGraph()
        network.add_edges_from([edge.tuple() for edge in self.edges])
        self.network = network
        return network


class Conditional(Translatable, BaseModel):
    __translatable__ = {'locales': languages}
    locale = default_language
    id = db.Column(db.Integer, primary_key=True)
    function = db.Column(db.String)
    nodes = db.relationship("Node", back_populates="conditional")


class Action(Translatable, BaseModel):
    __translatable__ = {'locales': languages}
    locale = default_language
    id = db.Column(db.Integer, primary_key=True)
    skippable = db.Column(db.Boolean, default=False)
    action_url = db.Column(db.String)
    complete = db.Column(db.Boolean, default=False)
    nodes = db.relationship("Node", back_populates="action")
    resources = db.relationship("Resource", back_populates="action")

    def to_dict(self):
        return {
            "title": self.title,
            "displayHTML": self.html,
            "skippable": self.skippable,
            "terminus": self.complete,
            "helpURLs": [resource.to_dict() for resource in self.resources]
        }


class Milestone(Translatable, BaseModel):
    __translatable__ = {'locales': languages}
    locale = default_language
    id = db.Column(db.Integer, primary_key=True)
    graph_id = db.Column(db.Integer, db.ForeignKey('graph.id'))
    data_loader = db.Column(db.String)
    nodes = db.relationship("Node", back_populates="milestone")


class Node(BaseModel):
    __table_args__ = (db.UniqueConstraint('ref'), )
    id = db.Column(db.Integer, primary_key=True)
    ref = db.Column(db.String, nullable=False)
    conditional_id = db.Column(db.Integer, db.ForeignKey('conditional.id'))
    action_id = db.Column(db.Integer, db.ForeignKey('action.id'))
    milestone_id = db.Column(db.Integer, db.ForeignKey('milestone.id'))
    action = db.relationship("Action", back_populates="nodes")
    conditional = db.relationship("Conditional", back_populates="nodes")
    milestone = db.relationship("Milestone", back_populates="nodes")

    def __hash__(self):
        return self.id


class Edge(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    graph_id = db.Column(db.Integer, db.ForeignKey('graph.id'), nullable=False)
    from_id = db.Column(db.Integer, db.ForeignKey('node.id'), nullable=False)
    to_id = db.Column(db.Integer, db.ForeignKey('node.id'), nullable=False)
    type = db.Column(db.Boolean, nullable=False)
    graph = db.relationship("Graph", back_populates="edges")
    from_node = db.relationship("Node", foreign_keys=[from_id])
    to_node = db.relationship("Node", foreign_keys=[to_id])

    def tuple(self):
        return (self.from_node, self.to_node, {'type': self.type, 'object': self})


class Resource(Translatable, BaseModel):
    __translatable__ = {'locales': languages}
    locale = default_language
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String, nullable=False)
    action_id = db.Column(db.Integer, db.ForeignKey('action.id'), nullable=False)
    action = db.relationship("Action", back_populates="resources")

    def to_dict(self):
        return {'label': self.title, 'url': self.url}


GraphTranslationMixin: BaseTranslationMixin = translation_base(Graph)
ResourceTranslationMixin: BaseTranslationMixin = translation_base(Resource)
ActionTranslationMixin: BaseTranslationMixin = translation_base(Action)
MilestoneTranslationMixin: BaseTranslationMixin = translation_base(Milestone)
ConditionalTranslationMixin: BaseTranslationMixin = translation_base(Conditional)


class GraphTranslation(GraphTranslationMixin):
    title = db.Column(db.UnicodeText)
    description = db.Column(db.UnicodeText)


class ResourceTranslation(ResourceTranslationMixin):
    title = db.Column(db.UnicodeText, nullable=False)


class ActionTranslation(ActionTranslationMixin):
    title = db.Column(db.UnicodeText)
    html = db.Column(db.UnicodeText)


class ConditionalTranslation(ConditionalTranslationMixin):
    title = db.Column(db.UnicodeText)


class MilestoneTranslation(MilestoneTranslationMixin):
    title = db.Column(db.UnicodeText)


def load_all_graphs():
    return Graph.query. \
        options(orm.joinedload(Graph.translations[get_locale()]))


def load_graph(graph_id: int) -> Graph:
    return Graph.query.\
        options(orm.joinedload(Graph.translations[get_locale()])).\
        filter_by(id=graph_id).\
        first()


def load_node(node_id: int = None, node_ref: str = None) -> Node:
    if node_id:
        return Node.query.filter_by(id=node_id).first()
    else:
        return Node.query.filter_by(ref=node_ref).first()


def load_edge(from_id: int, to_id: int) -> Edge:
    return Edge.query.filter_by(from_id=from_id, to_id=to_id).first()
