import pytest
import navigator_engine.model as model
import navigator_engine.tests.util as test_util


@pytest.mark.usefixtures('with_app_context')
def test_db_graph_storage():
    """
    This was an early proof of concept that I am preserving for the time being
    as an integration test.
    """
    test_util.create_demo_data()

    # Load the demo graph from the db
    graph = model.Graph.query.filter_by(id=1).first()

    # Convert data into a networkx Graph
    graph.to_networkx()

    # Find the decision graph root node
    root = [n for n, d in graph.network.in_degree() if d == 0]
    root = root[0]  # (there should only be one root)
    original_title = root.conditional.title
    test_util.logger.info(f"Root node {root} with title {original_title}")

    # Update the root node's title
    new_title = "Is geographic data loaded?"
    root.conditional.title = new_title

    # Write all changes made to the graph back to the db
    model.db.session.add(graph)
    model.db.session.commit()

    # Reload the graph from the db and check that the title of the root node is updated
    graph_reloaded = model.Graph.query.filter_by(id=1).first()
    graph_reloaded.to_networkx()
    root = [n for n, d in graph_reloaded.network.in_degree() if d == 0]
    root = root[0]
    test_util.logger.info(f"Reloaded root node {root} with title {root.conditional.title}")

    # Assert that the updated title was stored in the DB
    assert new_title == root.conditional.title
