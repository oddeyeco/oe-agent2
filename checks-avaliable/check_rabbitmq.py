import urllib2
import os, sys
import ConfigParser
import datetime
import socket
import json

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')

rabbit_url = config.get('RabbitMQ', 'stats')
rabbit_user = config.get('RabbitMQ', 'user')
rabbit_pass = config.get('RabbitMQ', 'pass')
hostname = socket.getfqdn()
cluster_name = config.get('SelfConfig', 'cluster_name')
check_type = 'rabbitmq'

def run_rabbitmq():
    try:
        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, rabbit_url, rabbit_user, rabbit_pass)
        handler = urllib2.HTTPBasicAuthHandler(password_mgr)
        opener = urllib2.build_opener(handler)
        rabbit_stats=opener.open(rabbit_url,timeout=5).read()
        urllib2.install_opener(opener)
        push = __import__('pushdata')
        jsondata=push.JonSon()
        jsondata.create_data()
        stats_json = json.loads(rabbit_stats)
        timestamp = int(datetime.datetime.now().strftime("%s"))
        message_stats=('publish','ack','deliver_get','redeliver','deliver')
        queue_totals=('messages','messages_ready','messages_unacknowledged')
        for stats in message_stats:
            stats_name='rabbitmq_'+stats+'_rate'
            stats_value=stats_json['message_stats'][stats+'_details']['rate']
            jsondata.gen_data(stats_name, timestamp, stats_value, push.hostname, check_type, cluster_name)
        for queue in queue_totals:
            queue_name='rabbitmq_'+queue
            queue_value=stats_json['queue_totals'][queue]
            jsondata.gen_data(queue_name, timestamp, queue_value, push.hostname, check_type, cluster_name)

        jsondata.put_json()
        jsondata.truncate_data()
    except Exception as e:
        push = __import__('pushdata')
        push.print_error(e)
        pass

