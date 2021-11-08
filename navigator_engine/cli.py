from navigator_engine.graph_loader import graph_loader


def register(app):
    @app.cli.group()
    def navigator_engine():
        """Navigator Engine commands"""
        pass

    @navigator_engine.command()
    def load_graph():
        """Loads binary decision graph into the db"""
        graph_loader()
