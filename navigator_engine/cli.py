import click

from navigator_engine.common.graph_loader import graph_loader


def register(app):
    @app.cli.group()
    def navigator_engine():
        """Navigator Engine commands"""
        pass

    @navigator_engine.command()
    @click.argument('graph-config-file', default='Estimates 22 BDG [Final].xlsx')
    def load_graph(graph_config_file):
        """Loads binary decision graph into the db"""
        graph_loader(graph_config_file)
