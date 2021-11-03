import factory
import navigator_engine.model as models
from navigator_engine.common.decision_engine import DecisionEngine


class ConditionalFactory(factory.Factory):
    class Meta:
        model = models.Conditional

    title = 'Test Conditional'
    function = 'function()'
    id = 1


class ActionFactory(factory.Factory):
    class Meta:
        model = models.Action
    id = 1
    title = 'Test Action'


class NodeFactory(factory.Factory):
    class Meta:
        model = models.Node
    id = 1


class MilestoneFactory(factory.Factory):
    class Meta:
        model = models.Milestone
    id = 1
    title = "Test Milestone"
    data_loader = "return_empty()"


class GraphFactory(factory.Factory):
    class Meta:
        model = models.Graph
    id = 1
    title = "Test Graph"


class DecisionEngine(factory.Factory):
    class Meta:
        model = DecisionEngine
    data = {}
    graph = GraphFactory()
    skip = []
