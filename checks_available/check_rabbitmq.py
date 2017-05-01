import lib.record_rate
import lib.pushdata
import urllib2
import os, sys
import ConfigParser
import datetime
import socket
import json

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/mq.ini')

rabbit_url = config.get('RabbitMQ', 'stats')
rabbit_user = config.get('RabbitMQ', 'user')
rabbit_pass = config.get('RabbitMQ', 'pass')
queue_details = config.getboolean('RabbitMQ', 'queue_details')
hostname = socket.getfqdn()
cluster_name = config.get('SelfConfig', 'cluster_name')
check_type = 'rabbitmq'

def runcheck():
    try:
        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        url1=rabbit_url+'/api/overview'
        password_mgr.add_password(None, url1, rabbit_user, rabbit_pass)
        handler = urllib2.HTTPBasicAuthHandler(password_mgr)
        opener = urllib2.build_opener(handler)
        rabbit_stats=opener.open(url1,timeout=5).read()
        urllib2.install_opener(opener)
        jsondata=lib.pushdata.JonSon()
        jsondata.prepare_data()
        stats_json = json.loads(rabbit_stats)
        timestamp = int(datetime.datetime.now().strftime("%s"))
        message_stats=('publish','ack','deliver_get','redeliver','deliver')
        queue_totals=('messages','messages_ready','messages_unacknowledged')
        for stats in message_stats:
            try:
                stats_name='rabbitmq_'+stats+'_rate'
                stats_value=stats_json['message_stats'][stats+'_details']['rate']
                jsondata.gen_data(stats_name, timestamp, stats_value, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')
            except Exception as e:
                lib.puylogger.print_message('Cannot get stats for ' + str(e))
                pass

        for queue in queue_totals:
            queue_name='rabbitmq_'+queue
            queue_value=stats_json['queue_totals'][queue]
            jsondata.gen_data(queue_name, timestamp, queue_value, lib.pushdata.hostname, check_type, cluster_name)

        url2 = rabbit_url + '/api/queues'
        password_mgr2 = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_mgr2.add_password(None, url2, rabbit_user, rabbit_pass)
        handler2 = urllib2.HTTPBasicAuthHandler(password_mgr2)
        opener2 = urllib2.build_opener(handler2)
        rabbit_queues=json.loads(opener2.open(url2,timeout=5).read())
        urllib2.install_opener(opener2)
        if queue_details is True :
            import re
            for name in range(len(rabbit_queues)):
                mname='rabbitmq_'+re.sub('[^a-zA-Z0-9]', '_', str(rabbit_queues[name]['name']))
                mvalue=str(rabbit_queues[name]['messages'])
                jsondata.gen_data(mname, timestamp, mvalue, lib.pushdata.hostname, check_type, cluster_name)
                details = ('publish_details', 'deliver_details')
                for detail in details :
                    try:
                        if detail in rabbit_queues[name]['message_stats']:
                            rname = 'rabbitmq_' + str(rabbit_queues[name]['name']) + '_'+ detail
                            rnamesub ='rabbitmq_'+re.sub('[^a-zA-Z0-9]', '_', rname)
                            rvalue= rabbit_queues[name]['message_stats'][detail]['rate']
                            jsondata.gen_data(rnamesub, timestamp, rvalue, lib.pushdata.hostname, check_type, cluster_name)
                    except:
                        pass
                        #raise NotImplementedError('BlueFlood is not supported yet')
        jsondata.put_json()
    except Exception as e:
        lib.pushdata.print_error(__name__ , (e))
        pass

