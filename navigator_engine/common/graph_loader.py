import navigator_engine.model as model
import navigator_engine.common as common
import logging
import os
import numpy as np
import pandas as pd
import re
import markdown
from urllib.parse import urlparse

MILESTONE_COLUMNS = {
    'TITLE': 'Milestone Title (Visible to User):',
    'VERSION': 'Version:',
    'DESCRIPTION': 'Milestone Description (Visible to User):',
    'COMPLETE_MESSAGE': 'Complete Message'
}

DATA_COLUMNS = {
    'TITLE': 'Task Test (if test passes, proceed to next test)',
    'ACTION': 'Task Title (Visible to User)',
    'ACTION_CONTENT': 'If test fails, present this to user:',
    'ACTION_RESOURCES': 'Resources / Links',
    'UNSKIPPABLE': 'Mandatory right now',
    'SKIP_TO': 'Proceed to test (if test fails)',
    'FUNCTION': 'Test function'
}

logger = logging.getLogger(__name__)


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
        ).loc[0][0:7]

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
                ref=_get_ref(idx, 'milestone'),
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
                ref=_get_ref(idx, 'conditional'),
                conditional_id=conditional.id
            )

            model.db.session.add(node_conditional)
            model.db.session.commit()

            graph_data.at[idx, 'DbNodeId'] = node_conditional.id

            # If Conditional is False, add an action node if no skip destination is given
            if graph_data.loc[:, DATA_COLUMNS['SKIP_TO']].isnull().loc[idx]:

                if 'check_not_skipped' in conditional.function:
                    graph_data.loc[[idx]] = _create_check_skips_action(conditional, graph_data.loc[[idx]])

                skippable = not _map_excel_boolean(graph_data.at[idx, DATA_COLUMNS['UNSKIPPABLE']])

                action_html = _markdown_to_html(graph_data.at[idx, DATA_COLUMNS['ACTION_CONTENT']])
                action = model.Action(
                    title=graph_data.at[idx, DATA_COLUMNS['ACTION']],
                    html=action_html,
                    skippable=skippable,
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
                        action=action
                    )
                    model.db.session.add(resource)
                    model.db.session.commit()

                # Add node to action
                node_action = model.Node(
                    ref=_get_ref(idx, 'action'),
                    action_id=action.id
                )
                model.db.session.add(node_action)
                model.db.session.commit()

                graph_data.at[idx, 'DbNodeActionId'] = node_action.id
                model.db.session.add(node_action)
                model.db.session.commit()

    # Add a completion action
    message = graph_header.get(
        MILESTONE_COLUMNS['COMPLETE_MESSAGE'],
        "Well done.  You have completed the milestone "
        f"{graph_header[MILESTONE_COLUMNS['TITLE']]}. "
        "Time to move on to the next one..."
    )
    complete_node = model.Node(action=model.Action(
        title=f"{graph_header[MILESTONE_COLUMNS['TITLE']]} complete!",
        html=_markdown_to_html(message),
        skippable=False,
        complete=True
    ), ref=_get_ref(idx, 'complete'))
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
    if boolean in ['TRUE', 1, "1", "1.0", "T", "t", "true", "True"]:
        return True
    elif boolean in ['FALSE', 0, "0.0", "0", "1.0", "F", "f", "false", "False", ''] or pd.isnull(boolean):
        return False
    else:
        raise ValueError('Value {} read from Initial Graph Config is not valid; Only TRUE and FALSE are valid values.'
                         .format(boolean))


def _markdown_to_html(md_in):
    if pd.isnull(md_in):
        return None
    try:
        html_out = markdown.markdown(md_in)
    except Exception:
        raise ValueError(f'Not valid Markdown: {md_in}')
    return html_out


def _parse_resources(resource_cell):
    resources = []

    if pd.isnull(resource_cell):
        return resources

    resource_rows = resource_cell.split('\n')
    for row in resource_rows:
        try:
            title = row.split('http')[0].strip()
            url = row.split(title)[1].strip()
        except ValueError:
            logger.error(f"There's a problem parsing resources: \n{resource_cell}")

        try:
            url_parsed = urlparse(url)
            resources.append({'title': title, 'url': url_parsed.geturl()})
        except ValueError:
            logger.error(f'{url} is not a valid URL, omitting resource')

    return resources


def _get_ref(ref, node_type):
    if node_type == 'complete':
        ref = '-'.join(ref.split('-')[:-1] + ['C'])
        node_type = 'action'
    return f'EST-{ref}-{node_type[0].upper()}'


def _create_check_skips_action(conditional, graph_data):

    function_name, function_args = common.get_pluggable_function_and_args(conditional.function)

    tasks = []
    for node_ref in function_args[0]:
        node = model.load_node(node_ref=node_ref)
        tasks.append(node.action.title)
    tasks_list = "\n - ".join(tasks)

    graph_data[DATA_COLUMNS['ACTION']] = "You have skipped some essential tasks"
    graph_data[DATA_COLUMNS['ACTION_CONTENT']] = (
        f"You have skipped some of following essential tasks:\n\n - {tasks_list}\n\n"
        "You must ensure you complete all these tasks in order to proceed any further.\n\n"
        "If you have understood this message, mark this task as complete and click *What's"
        "Next* to be taken to the first of your incomplete essential tasks."
    )

    return graph_data
