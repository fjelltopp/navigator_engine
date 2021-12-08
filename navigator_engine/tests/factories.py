import factory
import navigator_engine.model as models
from navigator_engine.common.decision_engine import DecisionEngine
from typing import Any


class ConditionalFactory(factory.Factory):
    class Meta:
        model = models.Conditional

    title: str = 'Test Conditional'
    function: str = 'function()'
    id: int = factory.Sequence(lambda n: int(n))


class ActionFactory(factory.Factory):
    class Meta:
        model = models.Action
    id: int = factory.Sequence(lambda n: int(n))
    title: str = 'Test Action'


class NodeFactory(factory.Factory):
    class Meta:
        model = models.Node
    id: int = factory.Sequence(lambda n: int(n))
    ref: str = factory.Faker('uuid4')


class MilestoneFactory(factory.Factory):
    class Meta:
        model = models.Milestone
    id: int = factory.Sequence(lambda n: int(n))
    title: str = "Test Milestone"
    data_loader: str = "return_empty()"
    graph_id: int = 1


class GraphFactory(factory.Factory):
    class Meta:
        model = models.Graph
    id: int = factory.Sequence(lambda n: int(n))
    title: str = "Test Graph"


class DecisionEngineFactory(factory.Factory):
    class Meta:
        model = DecisionEngine
    data: Any = {}
    graph = GraphFactory()
    skip: list[str] = []
