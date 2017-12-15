'''
This check required Python MongoDB, On Debian like systems do
apt-get install python-pymongo
'''
import lib.record_rate
import pymongo
import lib.basecheck
import lib.getconfig
import lib.puylogger

mongo_host = lib.getconfig.getparam('MongoDB', 'host')
mongo_user = lib.getconfig.getparam('MongoDB', 'user')
mongo_pass = lib.getconfig.getparam('MongoDB', 'pass')
mongo_auth = lib.getconfig.getparam('MongoDB', 'auth')
mongo_port = int(lib.getconfig.getparam('MongoDB', 'port'))
mongo_mechanism = lib.getconfig.getparam('MongoDB', 'auth_mechanism')
check_type = 'mongo'

class Check(lib.basecheck.CheckBase):

    def precheck(self):

        try:
            mongoclient = pymongo.MongoClient(mongo_host, mongo_port)
            if mongo_auth is True:
                mongoclient.admin.authenticate(mongo_user, mongo_pass, mechanism = mongo_mechanism)
            db  = mongoclient.test

            connections_dict = db.command("serverStatus")

            for key, value in list(connections_dict['metrics']['document'].items()):
                reqrate = self.rate.record_value_rate('mongo_document_'+key, value, self.timestamp)
                self.local_vars.append({'name': 'mongo_document_' + key, 'timestamp': self.timestamp, 'value': reqrate, 'check_type': check_type, 'chart_type': 'Rate'})
            for key, value in list(connections_dict['metrics']['operation'].items()):
                reqrate = self.rate.record_value_rate('mongo_operation_'+key, value, self.timestamp)
                self.local_vars.append({'name': 'mongo_operation_'+key, 'timestamp': self.timestamp, 'value': reqrate, 'check_type': check_type, 'chart_type': 'Rate'})
            for key, value in list(connections_dict['opcounters'].items()):
                reqrate = self.rate.record_value_rate('mongo_opcounters_'+key, value, self.timestamp)
                self.local_vars.append({'name': 'mongo_opcounters_'+key, 'timestamp': self.timestamp, 'value': reqrate, 'check_type': check_type, 'chart_type': 'Rate'})
            for key, value in list(connections_dict['connections'].items()):
                self.local_vars.append({'name': 'mongo_connections_'+key, 'timestamp': self.timestamp, 'value': value, 'check_type': check_type})

            mongoclient.close()

        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass

