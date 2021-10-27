from flask_restful import Api
from navigator_engine.api.whats_next import WhatsNext
from navigator_engine.api.decision_graph import DecisionGraph
from navigator_engine.api.conditional import Conditional
from navigator_engine.api.action import Action

api = Api()

api.add_resource(WhatsNext, "/whatsnext")
api.add_resource(DecisionGraph, "/decisiongraph")
api.add_resource(Conditional, "/conditional")
api.add_resource(Action, "/action")
