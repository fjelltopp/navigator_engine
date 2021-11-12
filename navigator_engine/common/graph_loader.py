import navigator_engine.model as model
import logging
import os
import numpy as np
import pandas as pd
import re
import markdown
from urllib.parse import urlparse

MILESTONE_COLUMNS = {
    'TITLE': 'Milestone Title',
    'VERSION': 'Version',
    'DESCRIPTION': 'Description'
}

DATA_COLUMNS = {
    'TITLE': 'Task Test',
    'ACTION': 'Action Title (if test fails)',
    'ACTION_CONTENT': 'Action content',
    'ACTION_RESOURCES': 'Resources / Links',
    'SKIPPABLE': 'Mandatory to proceed?',
    'SKIP_TO': 'Proceed to test (if test fails)',
    'FUNCTION': 'Test Code'
}


def graph_loader(graph_config_file):
    # Clear and reset the db
    model.db.drop_all()
    model.db.create_all()

    split_file_name = os.path.splitext(graph_config_file)
    file_extension = split_file_name[1]

    assert file_extension == '.xlsx', 'File extension of Initial Graph Config must be XLSX'

    xl = pd.ExcelFile(graph_config_file)
    regex = re.compile('[\d]{2,2}-')
    graph_sheets = list(filter(lambda x: regex.match(x), xl.sheet_names))
    graphs = {}

    for index, sheet_name in enumerate(graph_sheets):
        graph_header = pd.read_excel(
            graph_config_file,
            sheet_name=sheet_name,
            header=0
        ).loc[0][0:4]

        graph_data = pd.read_excel(
            graph_config_file,
            sheet_name=sheet_name,
            header=3,
            index_col=0,
            dtype=str
        )

        # Create graphs on first past through
        # So that they can be referenced by foreign keys on second pass
        graph = model.Graph(
            title=graph_header[MILESTONE_COLUMNS['TITLE']],
            version=graph_header[MILESTONE_COLUMNS['VERSION']],
            description=graph_header[MILESTONE_COLUMNS['DESCRIPTION']]
        )
        model.db.session.add(graph)
        model.db.session.commit()

        graphs[sheet_name] = {
            'graph_id': graph.id,
            "graph": graph,
            'title': graph_header[MILESTONE_COLUMNS['TITLE']],
            'graph_header': graph_header,
            'graph_data': graph_data
        }

    for sheet_name in graph_sheets:
        import_data(sheet_name, graphs)


def import_data(sheet_name, graphs):
    graph_data = graphs[sheet_name]['graph_data']
    graph_header = graphs[sheet_name]['graph_header']
    graph = graphs[sheet_name]['graph']

    # Add new columns for references to database primary keys
    graph_data.insert(0, 'DbNodeId', None)
    graph_data.insert(1, 'DbActionNodeId', None)

    # Loop through the graph dataframe to create nodes, conditionals and actions
    for idx in graph_data.index:
        # Create a Milestone or a Conditional depending on which one the row represents
        p = re.compile('[\d]{2,2}-')
        is_milestone = p.match(graph_data.loc[idx, DATA_COLUMNS['TITLE']])
        if is_milestone:
            milestone_sheet_name = graph_data.loc[idx, DATA_COLUMNS['TITLE']]
            milestone = model.Milestone(
                title=graphs[milestone_sheet_name]['title'],
                graph_id=graphs[milestone_sheet_name]['graph_id']
            )
            model.db.session.add(milestone)
            model.db.session.commit()

            node_milestone = model.Node(
                milestone_id=milestone.id
            )

            model.db.session.add(node_milestone)
            model.db.session.commit()

            graph_data.at[idx, 'DbNodeId'] = node_milestone.id
        else:
            conditional = model.Conditional(
                title=graph_data.loc[idx, DATA_COLUMNS['TITLE']],
                function=graph_data.loc[idx, DATA_COLUMNS['FUNCTION']]
            )
            model.db.session.add(conditional)
            model.db.session.commit()

            node_conditional = model.Node(
                conditional_id=conditional.id
            )

            model.db.session.add(node_conditional)
            model.db.session.commit()

            graph_data.at[idx, 'DbNodeId'] = node_conditional.id

            # If Conditional is False, add an action node if no skip destination is given
            if graph_data.loc[:, DATA_COLUMNS['SKIP_TO']].isnull().loc[idx]:
                action_html = _markdown_to_html(graph_data.at[idx, DATA_COLUMNS['ACTION_CONTENT']])
                action = model.Action(
                    title=graph_data.at[idx, DATA_COLUMNS['ACTION']],
                    html=action_html,
                    skippable=_map_excel_boolean(graph_data.at[idx, DATA_COLUMNS['SKIPPABLE']]),
                    complete=False
                )
                model.db.session.add(action)
                model.db.session.commit()

                # Parse action's resource urls and add them to database
                resources = _parse_resources(graph_data.at[idx, DATA_COLUMNS['ACTION_RESOURCES']])
                for resource_row in resources:
                    resource = model.Resource(
                        title=resource_row['title'],
                        url=resource_row['url'],
                        action_id=action.id,
                        action=action
                    )
                    model.db.session.add(resource)
                    model.db.session.commit()

                # Add node to action
                node_action = model.Node(
                    action_id=action.id
                )
                model.db.session.add(node_action)
                model.db.session.commit()

                graph_data.at[idx, 'DbNodeActionId'] = node_action.id
                model.db.session.add(node_action)
                model.db.session.commit()

    # Add a completion action
    complete_node = model.Node(action=model.Action(
        title=f"{graph_header[MILESTONE_COLUMNS['TITLE']]} complete!",
        html=_markdown_to_html("Well done.  You have completed the milestone "
              f"{graph_header[MILESTONE_COLUMNS['TITLE']]}. Time to move on to the next one..."),
        skippable=False,
        complete=True
    ))
    model.db.session.add(complete_node)
    model.db.session.commit()

    # Loop through the graph dataframe to create edges
    for idx in graph_data.index:

        if graph_data.iloc[-1, :].equals(graph_data.loc[idx, :]):
            logging.info('End node reached')
            edge_true_to_id = complete_node.id
        else:
            edge_true_to_id = graph_data.iloc[graph_data.index.get_loc(graph_data.loc[idx].name) + 1].loc['DbNodeId']
        edge_true = model.Edge(
            graph_id=graph.id,
            from_id=graph_data.at[idx, 'DbNodeId'],
            to_id=edge_true_to_id,
            type=True
        )
        model.db.session.add(edge_true)
        model.db.session.commit()

        false_edge_to_id = None
        is_milestone = re.compile('[\d]{2,2}-').match(graph_data.loc[idx, DATA_COLUMNS['TITLE']])

        # Add a "False" edge from conditional to the relevant action if no skip destination is given
        if graph_data.loc[:, DATA_COLUMNS['SKIP_TO']].isnull().loc[idx] and not is_milestone:
            false_edge_to_id = graph_data.at[idx, 'DbNodeActionId']
        # if skip destination is "complete", create an edge to the complete action
        elif graph_data.loc[idx, DATA_COLUMNS['SKIP_TO']] == 'complete':
            false_edge_to_id = complete_node.id
        # if skip destination is given, add an edge to its node
        elif not pd.isnull(graph_data.loc[idx, DATA_COLUMNS['SKIP_TO']]):
            false_edge_to_id = graph_data.at[graph_data.at[idx, DATA_COLUMNS['SKIP_TO']], 'DbNodeId']

        if false_edge_to_id:
            edge_false = model.Edge(
                graph_id=graph.id,
                from_id=graph_data.at[idx, 'DbNodeId'],
                to_id=false_edge_to_id,
                type=False
            )
            model.db.session.add(edge_false)
            model.db.session.commit()


def _map_excel_boolean(boolean):
    if boolean in ['TRUE', 1, "1", "T", "t", "true", "True"]:
        return True
    elif boolean in ['FALSE', 0, "0", "F", "f", "false", "False", ''] or np.isnan(boolean):
        return False
    else:
        raise ValueError('Value {} read from Initial Graph Config is not valid; Only TRUE and FALSE are valid values.'
                         .format(boolean))


def _markdown_to_html(md_in):
    if pd.isnull(md_in):
            return None

    try:
        html_out = markdown.markdown(md_in)
    except Exception as e:
        raise ValueError(f'Not valid Markdown: {md_in}')

    return html_out


def _parse_resources(resource_cell):
    resources = []

    if pd.isnull(resource_cell):
        return resources

    resource_rows = re.split('\n', resource_cell)
    for row in resource_rows:
        url_re = re.compile(r'(https?://[^\s]+)')
        search_results = url_re.search(row)
        url = search_results.group(0)
        title = row[0:search_results.span()[0]].strip()

        try:
            url_parsed = urlparse(url)
            resources.append({'title': title, 'url': url_parsed.geturl()})
        except ValueError as e:
            logging.warning(f'{url} is not a valid URL, omitting resource')

    return resources
