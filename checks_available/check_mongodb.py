'''
This check required Python MongoDB, On Debian like systems do
apt-get install python-pymongo
'''
import lib.record_rate
import lib.pushdata
import pymongo
import datetime
import ConfigParser
import os, sys

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/sql_cache.ini')
cluster_name = config.get('SelfConfig', 'cluster_name')

mongo_host = config.get('MongoDB', 'host')
mongo_user = config.get('MongoDB', 'user')
mongo_pass = config.get('MongoDB', 'pass')
mongo_auth = config.get('MongoDB', 'auth')
mongo_port = int(config.get('MongoDB', 'port'))
mongo_mechanism = config.get('MongoDB', 'auth_mechanism')


def runcheck():
    try:
        check_type = 'mongo'
        mongoclient = pymongo.MongoClient(mongo_host, mongo_port)
        if mongo_auth is True:
            mongoclient.admin.authenticate(mongo_user, mongo_pass, mechanism=mongo_mechanism)
        db =mongoclient.test

        connections_dict = db.command("serverStatus")
        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
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

        jsondata.put_json()

    except Exception as e:
        lib.pushdata.print_error(__name__ , (e))
        pass

