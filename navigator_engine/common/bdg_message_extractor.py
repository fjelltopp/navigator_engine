from navigator_engine.app import app
import pandas as pd
import re
import polib
from datetime import datetime, timezone

MILESTONE_COLUMNS = {
    'TITLE': 'Milestone Title (Visible to User):',
    'DESCRIPTION': 'Milestone Description (Visible to User):',
    'COMPLETE_MESSAGE': 'Complete Message',
    'ENTRY_CRITERIA': 'Entry Criteria:'
}

DATA_COLUMNS = {
    'ACTION': 'Task Title (Visible to User)',
    'ACTION_CONTENT': 'If test fails, present this to user:',
    'ACTION_RESOURCES': 'Resources / Links'
}

TRANSLATIONS = ['FR']


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
    #regex = re.compile(r'[\d]{2,2}-')
    regex = re.compile(r'[0]{2,2}-')
    graph_sheets = list(filter(lambda x: regex.match(x), xl.sheet_names))

    dt = datetime.now(tz=timezone.utc)
    po = polib.POFile()
    po.metadata = {
        'Project-Id-Version': '1.0',
        'Report-Msgid-Bugs-To': 'support@fjelltopp.org',
        'POT-Creation-Date': dt.strftime('%Y-%m-%d %H:%M%z'),
        'PO-Revision-Date': dt.strftime('%Y-%m-%d %H:%M%z'),
        'Last-Translator': 'Fjelltopp Ltd <support@fjelltopp.org>',
        'Language-Team': 'French <support@fjelltopp.org>',
        'MIME-Version': '1.0',
        'Content-Type': 'text/plain; charset=utf-8',
        'Content-Transfer-Encoding': '8bit',
    }

    for index, sheet_name in enumerate(graph_sheets):
        graph_header = pd.read_excel(
            fileobj,
            sheet_name=sheet_name,
            header=0
        ).loc[0][0:13]

        for key in MILESTONE_COLUMNS:
            entry = polib.POEntry(
                msgid=graph_header.get(MILESTONE_COLUMNS[key]),
                msgstr=graph_header.get(TRANSLATIONS[0] + '::' + MILESTONE_COLUMNS[key]),
                occurrences=[('welcome.py', '12')]
            )
            po.append(entry)

        graph_data = pd.read_excel(
            fileobj,
            sheet_name=sheet_name,
            header=3,
            index_col=0,
            dtype=str
        )

        for graph_data_index, row in graph_data.iterrows():
            for key in DATA_COLUMNS:
                if not row.isna().get(DATA_COLUMNS[key])\
                        and not row.isna().get(TRANSLATIONS[0] + '::' + DATA_COLUMNS[key]):
                    entry = polib.POEntry(
                        msgid=row.get(DATA_COLUMNS[key]),
                        msgstr=row.get(TRANSLATIONS[0] + '::' + DATA_COLUMNS[key]),
                        occurrences=[('welcome.py', '12')]
                    )
                    po.append(entry)

    po.save('./newfile.po')


with open(app.config.get('DEFAULT_DECISION_GRAPH'), 'rb') as f:
    extract_bdg(f)

