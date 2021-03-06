import navigator_engine.model as model
import navigator_engine.common as common
import logging
import os
import pandas as pd
import re
import markdown
from urllib.parse import urlparse
from flask import current_app as app

MILESTONE_COLUMNS = {
    'TITLE': 'Milestone Title (Visible to User):',
    'VERSION': 'Version:',
    'DESCRIPTION': 'Milestone Description (Visible to User):',
    'COMPLETE_MESSAGE': 'Complete Message',
    'DATA_LOADER': 'Data Loader:'
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

VALID_RESOURCE_TYPES = [
    "inputs-unaids-geographic",
    "inputs-unaids-anc",
    "inputs-unaids-art",
    "inputs-unaids-survey",
    "inputs-unaids-population",
    "inputs-unaids-hiv-testing",
    "inputs-unaids-spectrum-file",
    "inputs-unaids-shiny90-survey",
    "inputs-unaids-shiny90-output-zip",
    "inputs-unaids-naomi-output-zip"
    "inputs-unaids-naomi-report"
]

logger = logging.getLogger(__name__)


def graph_loader(graph_config_file):
    # Clear and reset the db
    model.db.drop_all()
    model.db.create_all()

    split_file_name = os.path.splitext(graph_config_file)
    file_extension = split_file_name[1]

    assert file_extension == '.xlsx', 'File extension of Initial Graph Config must be XLSX'

    default_lang = app.config['DEFAULT_LANGUAGE']
    languages = app.config['LANGUAGES']

    xl = pd.ExcelFile(graph_config_file)
    regex = re.compile(r'[\d]{2,2}-')
    graph_sheets = list(filter(lambda x: regex.match(x), xl.sheet_names))
    graphs = {}

    for index, sheet_name in enumerate(graph_sheets):

        graph_header = pd.read_excel(
            graph_config_file,
            sheet_name=sheet_name,
            header=0
        ).loc[0]

        graph_data = pd.read_excel(
            graph_config_file,
            sheet_name=sheet_name,
            header=3,
            index_col=0,
            dtype=str
        )

        # Create graphs on first past through
        # So that they can be referenced by foreign keys on second pass
        graph = model.Graph()
        graph.version = graph_header[MILESTONE_COLUMNS['TITLE']]
        graph.translations[default_lang].title = graph_header[MILESTONE_COLUMNS['TITLE']]

        for lang in languages:
            if lang == default_lang:
                graph.translations[lang].title = graph_header[MILESTONE_COLUMNS['TITLE']]
                graph.translations[lang].description = graph_header[MILESTONE_COLUMNS['DESCRIPTION']]
            else:
                graph.translations[lang].title = graph_header.get(MILESTONE_COLUMNS['TITLE'] + '::' + lang)
                graph.translations[lang].description = \
                    graph_header.get(MILESTONE_COLUMNS['DESCRIPTION'] + '::' + lang)

        model.db.session.add(graph)
        model.db.session.commit()

        graphs[sheet_name] = {
            'graph_id': graph.id,
            "graph": graph,
            'title': {},
            'graph_header': graph_header,
            'graph_data': graph_data
        }

        for lang in languages:
            if lang == default_lang:
                graphs[sheet_name]['title'][lang] = graph_header[MILESTONE_COLUMNS['TITLE']]
            else:
                graphs[sheet_name]['title'][lang] = graph_header.get(MILESTONE_COLUMNS['TITLE'] + '::' + lang)

    for sheet_name in graph_sheets:
        import_data(sheet_name, graphs)


def import_data(sheet_name, graphs):

    default_lang = app.config['DEFAULT_LANGUAGE']

    graph_data = graphs[sheet_name]['graph_data']
    graph_header = graphs[sheet_name]['graph_header']
    graph = graphs[sheet_name]['graph']

    # Add new columns for references to database primary keys
    graph_data.insert(0, 'DbNodeId', None)
    graph_data.insert(1, 'DbActionNodeId', None)

    # Loop through the graph dataframe to create nodes, conditionals and actions
    for idx in graph_data.index:
        try:
            # Create a Milestone or a Conditional depending on which one the row represents
            p = re.compile(r'[\d]{2,2}-')
            is_milestone = p.match(graph_data.loc[idx, DATA_COLUMNS['TITLE']])
            if is_milestone:
                graph_data.at[idx, 'DbNodeId'] = _create_milestone(graph_data, graphs, idx)
            else:
                graph_data.at[idx, 'DbNodeId'] = _create_conditional(graph_data, graphs, idx)

        except Exception as e:
            logger.error(f"Error reading row: {idx}")
            raise e

    # Add a completion action
    message = graph_header.get(
        MILESTONE_COLUMNS['COMPLETE_MESSAGE'],
        "Well done.  You have completed the milestone "
        f"{graph_header[MILESTONE_COLUMNS['TITLE']]}. "
        "Time to move on to the next one..."
    )
    complete_action = model.Action()
    complete_action.translations[default_lang].title = f"{graph_header[MILESTONE_COLUMNS['TITLE']]} complete!"
    complete_action.translations[default_lang].html = _markdown_to_html(message)
    complete_action.skippable = False
    complete_action.complete = True

    complete_node = model.Node()
    complete_node.action = complete_action
    complete_node.ref = _get_ref(idx, 'complete')

    model.db.session.add(complete_node)
    model.db.session.commit()

    # Loop through the graph dataframe to create edges
    for idx in graph_data.index:
        try:
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
            is_milestone = re.compile(r'[\d]{2,2}-').match(graph_data.loc[idx, DATA_COLUMNS['TITLE']])

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
        except Exception as e:
            logger.error(f"Error creating edges for {idx}")
            raise e


def _create_milestone(graph_data, graphs, idx):
    languages = app.config['LANGUAGES']

    milestone_sheet_name = graph_data.loc[idx, DATA_COLUMNS['TITLE']]
    data_loader = graphs[milestone_sheet_name]['graph_header'].get(
        MILESTONE_COLUMNS['DATA_LOADER']
    )
    milestone = model.Milestone()
    milestone.graph_id = graphs[milestone_sheet_name]['graph_id']
    milestone.data_loader = data_loader
    for lang in languages:
        milestone.translations[lang].title = graphs[milestone_sheet_name]['title'][lang]
    model.db.session.add(milestone)
    model.db.session.commit()

    node_milestone = model.Node()
    node_milestone.ref = _get_ref(idx, 'milestone')
    node_milestone.milestone_id = milestone.id

    model.db.session.add(node_milestone)
    model.db.session.commit()

    return node_milestone.id


def _create_conditional(graph_data, graphs, idx):
    default_lang = app.config['DEFAULT_LANGUAGE']
    languages = app.config['LANGUAGES']

    conditional = model.Conditional()
    conditional.function = graph_data.loc[idx, DATA_COLUMNS['FUNCTION']]
    model.db.session.add(conditional)
    model.db.session.commit()
    for lang in languages:
        if lang == default_lang:
            conditional.translations[lang].title = graph_data.loc[idx, DATA_COLUMNS['TITLE']]
        else:
            conditional.translations[lang].title = \
                graph_data.loc[idx].get(DATA_COLUMNS['TITLE'] + '::' + lang)

    node_conditional = model.Node()
    node_conditional.ref = _get_ref(idx, 'conditional')
    node_conditional.conditional_id = conditional.id
    model.db.session.add(node_conditional)
    model.db.session.commit()

    # If Conditional is False, add an action node if no skip destination is given
    if graph_data.loc[:, DATA_COLUMNS['SKIP_TO']].isnull().loc[idx]:

        if 'check_not_skipped' in conditional.function:
            graph_data.loc[idx, :] = _create_check_skips_action(conditional, graph_data.loc[idx, :])

        skippable = not _map_excel_boolean(graph_data.at[idx, DATA_COLUMNS['UNSKIPPABLE']])
        _create_action(graph_data, skippable, idx)

    return node_conditional.id


def _create_action(graph_data, skippable, idx):
    default_lang = app.config['DEFAULT_LANGUAGE']
    languages = app.config['LANGUAGES']

    action = model.Action()
    action.skippable = skippable
    action.complete = False

    for lang in languages:
        if lang == default_lang:
            action.translations[lang].title = graph_data.at[idx, DATA_COLUMNS['ACTION']]
            action.translations[lang].html = \
                _markdown_to_html(graph_data.at[idx, DATA_COLUMNS['ACTION_CONTENT']])
        else:
            action.translations[lang].title = graph_data.loc[idx].get(
                DATA_COLUMNS['ACTION'] + '::' + lang)
            action.translations[lang].html = _markdown_to_html(graph_data.loc[idx].get(
                DATA_COLUMNS['ACTION_CONTENT'] + '::' + lang))
    model.db.session.add(action)
    model.db.session.commit()

    _create_resources(graph_data, action, idx)

    # Add node to action
    node_action = model.Node()
    node_action.ref = _get_ref(idx, 'action')
    node_action.action_id = action.id

    model.db.session.add(node_action)
    model.db.session.commit()

    graph_data.at[idx, 'DbNodeActionId'] = node_action.id
    model.db.session.add(node_action)
    model.db.session.commit()


def _create_resources(graph_data, action, idx):
    default_lang = app.config['DEFAULT_LANGUAGE']
    languages = app.config['LANGUAGES']
    resources = {}

    for lang in languages:
        if lang == default_lang:
            resources[lang] = _parse_resources(graph_data.at[idx, DATA_COLUMNS['ACTION_RESOURCES']])
        else:
            resources[lang] = _parse_resources(
                graph_data.loc[idx].get(DATA_COLUMNS['ACTION_RESOURCES'] + '::' + lang))

    resource_idx = 0
    for resource_row in resources[default_lang]:
        resource = model.Resource()
        resource.url = resource_row['url']
        resource.action = action
        for lang in languages:
            if len(resources[lang]) > 0:
                resource.translations[lang].title = resources[lang][resource_idx].get('title')
        model.db.session.add(resource)
        model.db.session.commit()

        resource_idx = resource_idx + 1


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
        ref = '-'.join(ref.split('-')[:-2] + ['CPLT'])
        node_type = 'action'
    return f'EST-{ref}-{node_type[0].upper()}'


def _is_null_or_false(value):
    return pd.isnull(value) or not bool(value)


def _create_check_skips_action(conditional, graph_data):

    if _is_null_or_false(graph_data[DATA_COLUMNS['ACTION']]):
        graph_data[DATA_COLUMNS['ACTION']] = "You have skipped some essential tasks"

    if _is_null_or_false(graph_data[DATA_COLUMNS['ACTION_CONTENT']]):
        function_name, function_args = common.get_pluggable_function_and_args(conditional.function)

        tasks = []
        for node_ref in function_args[0]:
            node = model.load_node(node_ref=node_ref)
            tasks.append(node.action.title)
        tasks_list = "\n - ".join(tasks)

        graph_data[DATA_COLUMNS['ACTION_CONTENT']] = (
            f"One or more of the following essential tasks remains incomplete:\n\n - {tasks_list}\n\n"
            "You must ensure you complete all these tasks in order to proceed any further.\n\n"
            "Navigator will now take you back to ensure you complete these tasks.\n\n"
            "If you have understood this message, mark this task as complete and click *What's"
            "Next?* to see your first incomplete task."
        )

    return graph_data


def require(constraint, message):
    if not constraint:
        raise ValueError(message)


def validate_pluggable_logic(node, network):

    function_string = node.conditional.function
    function_name, function_args = common.get_pluggable_function_and_args(function_string)

    if function_name.startswith('check_manual_confirmation'):
        arg_action_is_child = False
        for node, child_node in network.out_edges(node):
            if child_node.ref == function_args[0]:
                arg_action_is_child = True

        require(arg_action_is_child, f"{node.ref} has bad function {function_string}")

    elif function_name.startswith('check_not_skipped'):
        ...  # We already validate args in _create_check_skips_action()

    elif function_name.startswith('check_resource_key'):
        resource_types = function_args[0]
        if type(resource_types) is str:
            resource_types = [resource_types]
        for resource_type in resource_types:
            require(
                resource_type in VALID_RESOURCE_TYPES,
                f"{node.ref} function references invalid resource_type {resource_type}"
            )

    elif function_name.startswith('check_spectrum'):
        spectrum_checks = function_args[0]
        valid_spectrum_checks = pd.read_csv('spectrum_check_list.csv')['ID']
        if type(spectrum_checks) is str:
            spectrum_checks = [spectrum_checks]
        for check in spectrum_checks:
            require(
                check in valid_spectrum_checks.values,
                f"{node.ref} function references spectrum check {check}"
            )

    elif function_name.startswith('check_naomi'):
        naomi_checks = function_args[0]
        valid_naomi_checks = pd.read_csv('naomi_check_list.csv')['NaomiCheckPermPrimKey']
        if type(naomi_checks) is str:
            naomi_checks = [naomi_checks]
        for check in naomi_checks:
            require(
                check in valid_naomi_checks.values,
                f"{node.ref} function references Naomi check {check}"
            )


def validate_graph(graph_id):
    graph = model.load_graph(graph_id)
    network = graph.to_networkx()
    milestones = []

    complete_node = None
    for node, out_degree in network.out_degree():

        if getattr(node, 'action_id'):
            require(out_degree == 0, f"{node.ref} has wrong out_degree")
            require(node.action.title, f"{node.ref} has no title specified")
            require(node.action.html, f"{node.ref} has no content specified")
        elif getattr(node, 'conditional_id'):
            require(out_degree == 2, f"{node.ref} has wrong out_degree")
            require(node.conditional.function, f"{node.ref} has no test function")
            edge_types = [edge[2] for edge in network.out_edges([node], 'type')]
            require(set(edge_types) == {True, False}, f"{node.ref} has wrong out edges")
            validate_pluggable_logic(node, network)
        elif getattr(node, 'milestone_id'):
            require(out_degree == 1, f"{node.ref} has wrong out_degree")
            require(node.milestone.graph_id, f"{node.ref} has no graph ID")
            edge_types = [edge[2] for edge in network.out_edges([node], 'type')]
            require(edge_types == [True], f"{node.ref} has wrong out edges")
            milestones.append(node.milestone.graph_id)

        if getattr(node, 'action') and node.action.complete:
            complete_node = node

    require(complete_node, f"Graph {graph_id} has no complete node")

    for milestone in milestones:
        validate_graph(milestone)
