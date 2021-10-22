from flask_restful import Resource


class Action(Resource):
    def get(self):
        return {'message': 'Action'}
