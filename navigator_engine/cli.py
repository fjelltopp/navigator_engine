import click
from navigator_engine.common.graph_loader import graph_loader, validate_graph
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def register(app):
    @app.cli.group()
    def navigator_engine():
        """Navigator Engine commands"""
        pass

    @navigator_engine.command()
    @click.argument(
        'graph-config-file',
        default=app.config.get(
            'DEFAULT_DECISION_GRAPH'
        )
    )
    def load_graph(graph_config_file):
        """Loads binary decision graph into the db"""
        logger.info(f"Loading the graph {graph_config_file}")
        graph_loader(graph_config_file)
        logger.info("Loading graph successful")
        logger.info("Validating graph with graph_id = 1")
        validate_graph(1)
        logger.info("Graph validation successful")
