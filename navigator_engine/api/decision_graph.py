from flask_restful import Resource


class DecisionGraph(Resource):
    def get(self):
        return {'message': 'Decision Graph'}
