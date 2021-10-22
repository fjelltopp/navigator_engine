from flask_restful import Resource


class WhatsNext(Resource):
    def get(self):
        return {'message': 'WhatsNext'}
