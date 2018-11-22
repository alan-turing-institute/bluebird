from flask_restful import Resource, reqparse

import bluebird as bb
from bluebird.utils.errprint import errprint

parser = reqparse.RequestParser()
parser.add_argument('filename', type=str, location='json', required=False)


class Ic(Resource):
    """ BlueSky IC (initial condition) command """

    def post(self):
        args = parser.parse_args()
        errprint(args)

        if args['filename'] is not None:
            cmd = args['filename']
        else:
            cmd = 'IC'

        bb.CLIENT.send_stackcmd('IC ' + cmd)

        # TODO Get return status. Can hook this up to a 'SIMRESET' signal?
        return 'Ok?'
