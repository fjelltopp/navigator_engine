from navigator_engine.app import app
import pandas as pd
import re

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


def extract_bdg(fileobj, keywords=None, comment_tags=None, options=None):
    """Extract messages from Navigator BDG Excel files.

    :param fileobj: the file-like object the messages should be extracted
                    from
    :param keywords: a list of keywords (i.e. function names) that should
                     be recognized as translation functions
    :param comment_tags: a list of translator tags to search for and
                         include in the results
    :param options: a dictionary of additional options (optional)
    :return: an iterator over ``(lineno, funcname, message, comments)``
             tuples
    :rtype: ``iterator``"""

    xl = pd.ExcelFile(fileobj)
    #xl = pd.ExcelFile(app.config.get('DEFAULT_DECISION_GRAPH'))
    regex = re.compile(r'[\d]{2,2}-')
    graph_sheets = list(filter(lambda x: regex.match(x), xl.sheet_names))
    graphs = {}

    for index, sheet_name in enumerate(graph_sheets):

        graph_header = pd.read_excel(
            fileobj,
            sheet_name=sheet_name,
            header=0
        ).loc[0][0:7]

        graph_data = pd.read_excel(
            fileobj,
            sheet_name=sheet_name,
            header=3,
            index_col=0,
            dtype=str
        )
        print('foo')


with open(app.config.get('DEFAULT_DECISION_GRAPH'), 'rb') as f:
    extract_bdg(f)

    #for cell in _get_cells(xl):
    #    yield (message_lineno, funcname, messages,
    #                           [comment[1] for comment in translator_comments])
