'''
This check required Python MongoDB, On Debian like systems do
apt-get install python-pymongo
'''

import pymongo
import datetime
import ConfigParser
import os, sys

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
cluster_name = config.get('SelfConfig', 'cluster_name')

mongo_host = config.get('MongoDB', 'host')
mongo_user = config.get('MongoDB', 'user')
mongo_pass = config.get('MongoDB', 'pass')
mongo_auth = config.get('MongoDB', 'auth')
mongo_port = int(config.get('MongoDB', 'port'))
mongo_mechanism = config.get('MongoDB', 'auth_mechanism')


def run_mongodb():
    try:
        check_type = 'mongo'
        mongoclient = pymongo.MongoClient(mongo_host, mongo_port)
        if mongo_auth is True:
            mongoclient.admin.authenticate(mongo_user, mongo_pass, mechanism=mongo_mechanism)
        db =mongoclient.test

        connections_dict = db.command("serverStatus")
        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
        push = __import__('pushdata')
        value_rate= __import__('record_rate')
        jsondata=push.JonSon()
        jsondata.create_data()
        rate=value_rate.ValueRate()
        timestamp = int(datetime.datetime.now().strftime("%s"))

        for key, value in connections_dict['metrics']['document'].iteritems():
            reqrate=rate.record_value_rate('mongo_document_'+key, value, timestamp)
            jsondata.gen_data('mongo_document_'+key, timestamp, reqrate, push.hostname, check_type, cluster_name)
        for key, value in connections_dict['metrics']['operation'].iteritems():
            reqrate=rate.record_value_rate('mongo_operation_'+key, value, timestamp)
            jsondata.gen_data('mongo_operation_'+key, timestamp, reqrate, push.hostname, check_type, cluster_name)
        for key, value in connections_dict['opcounters'].iteritems():
            reqrate=rate.record_value_rate('mongo_opcounters_'+key, value, timestamp)
            jsondata.gen_data('mongo_opcounters_'+key, timestamp, reqrate, push.hostname, check_type, cluster_name)
        for key, value in connections_dict['connections'].iteritems():
            jsondata.gen_data('mongo_connections_'+key, timestamp, value, push.hostname, check_type, cluster_name)

        jsondata.put_json()
        jsondata.truncate_data()

    except Exception as e:
        push = __import__('pushdata')
        push.print_error(__name__ , (e))
        pass

