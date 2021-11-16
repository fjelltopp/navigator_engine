from navigator_engine.common.graph_loader import graph_loader
import navigator_engine.common as common
import navigator_engine.model as model
import pytest
import json
import os


@pytest.mark.vcr()
@pytest.mark.usefixtures('with_app_context')
def test_end_to_end(client):
    graph_loader('Estimates 22 BDG [Final].xlsx')
    validate_graph(1)
    # For the time being the following code is ignored
    # It will be updated once the production graph is loading properly
    # response = client.post("/api/decide", data=json.dumps({
    #     'data': {
    #         'url': 'https://dev.adr.fjelltopp.org/api/3/action/package_show'
    #                '?id=antarctica-country-estimates-2022-1-2-3',
    #         'authorization_header': os.getenv('ADR_SYSADMIN_KEY')
    #     },
    #     'skipActions': ['EST-1-4-A', 'EST-2-2-A']
    # }))
    # assert response.status_code == 200
    # assert response.json['decision']['id'] == 'EST-0-C-A'


def validate_pluggable_logic(node, network):

    function_string = node.conditional.function
    function_name, function_args = common.get_pluggable_function_and_args(function_string)

    if function_name.startswith('check_manual_confirmation'):
        arg_action_is_child = False
        for node, child_node in network.out_edges(node):
            if child_node.ref == function_args[0]:
                arg_action_is_child = True
        assert arg_action_is_child, f"{node.ref} has bad function {function_string}"


def validate_graph(graph_id):
    graph = model.load_graph(graph_id)
    network = graph.to_networkx()
    milestones = []

    complete_node = None
    for node, out_degree in network.out_degree():

        if getattr(node, 'action_id'):
            assert out_degree == 0, f"{node.ref} has wrong out_degree"
            assert node.action.title, f"{node.ref} has no title specified"
            assert node.action.html, f"{node.ref} has no content specified"
        elif getattr(node, 'conditional_id'):
            assert out_degree == 2, f"{node.ref} has wrong out_degree"
            assert node.conditional.function, f"{node.ref} has no test function"
            edge_types = [edge[2] for edge in network.out_edges([node], 'type')]
            assert set(edge_types) == {True, False}, f"{node.ref} has wrong out edges"
            validate_pluggable_logic(node, network)
        elif getattr(node, 'milestone_id'):
            assert out_degree == 1, f"{node.ref} has wrong out_degree"
            assert node.milestone.graph_id, f"{node.ref} has no graph ID"
            edge_types = [edge[2] for edge in network.out_edges([node], 'type')]
            assert edge_types == [True], f"{node.ref} has wrong out edges"
            milestones.append(node.milestone.graph_id)

        if getattr(node, 'action') and node.action.complete:
            complete_node = node

    assert complete_node, "Graph {graph_id} has no complete node"

    for milestone in milestones:
        validate_graph(milestone)
