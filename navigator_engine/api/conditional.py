from flask_restful import Resource


class Conditional(Resource):
    def get(self):
        return {'message': 'Conditional'}
