'''
This check required Python MongoDB, On Debian like systems do
apt-get install python-pymongo
'''
import lib.record_rate
import lib.pushdata
import pymongo
import datetime
import lib.getconfig

cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')

mongo_host = lib.getconfig.getparam('MongoDB', 'host')
mongo_user = lib.getconfig.getparam('MongoDB', 'user')
mongo_pass = lib.getconfig.getparam('MongoDB', 'pass')
mongo_auth = lib.getconfig.getparam('MongoDB', 'auth')
mongo_port = int(lib.getconfig.getparam('MongoDB', 'port'))
mongo_mechanism = lib.getconfig.getparam('MongoDB', 'auth_mechanism')


def runcheck():
    try:
        check_type = 'mongo'
        mongoclient = pymongo.MongoClient(mongo_host, mongo_port)
        if mongo_auth is True:
            mongoclient.admin.authenticate(mongo_user, mongo_pass, mechanism=mongo_mechanism)
        db =mongoclient.test

        connections_dict = db.command("serverStatus")
        jsondata=lib.pushdata.JonSon()
        jsondata.prepare_data()
        rate=lib.record_rate.ValueRate()
        timestamp = int(datetime.datetime.now().strftime("%s"))

        for key, value in connections_dict['metrics']['document'].iteritems():
            reqrate=rate.record_value_rate('mongo_document_'+key, value, timestamp)
            jsondata.gen_data('mongo_document_'+key, timestamp, reqrate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')
        for key, value in connections_dict['metrics']['operation'].iteritems():
            reqrate=rate.record_value_rate('mongo_operation_'+key, value, timestamp)
            jsondata.gen_data('mongo_operation_'+key, timestamp, reqrate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')

        for key, value in connections_dict['opcounters'].iteritems():
            reqrate=rate.record_value_rate('mongo_opcounters_'+key, value, timestamp)
            jsondata.gen_data('mongo_opcounters_'+key, timestamp, reqrate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')
        '''
        for key, value in connections_dict['indexCounters'].iteritems():
            reqrate=rate.record_value_rate('mongo_indexcounters_'+key, value, timestamp)
            jsondata.gen_data('mongo_indexcounters_'+key, timestamp, reqrate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')
        '''
        for key, value in connections_dict['connections'].iteritems():
            jsondata.gen_data('mongo_connections_'+key, timestamp, value, lib.pushdata.hostname, check_type, cluster_name)

        mongoclient.close()
        jsondata.put_json()

    except Exception as e:
        lib.pushdata.print_error(__name__ , (e))
        pass

