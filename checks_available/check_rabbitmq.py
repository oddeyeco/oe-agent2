import lib.commonclient
import lib.record_rate
import lib.getconfig
import lib.pushdata
import lib.puylogger
import datetime
import json

rabbit_url = lib.getconfig.getparam('RabbitMQ', 'stats')
rabbit_user = lib.getconfig.getparam('RabbitMQ', 'user')
rabbit_pass = lib.getconfig.getparam('RabbitMQ', 'pass')
rabbit_auth = lib.getconfig.getparam('RabbitMQ', 'user')+':'+lib.getconfig.getparam('RabbitMQ', 'pass')

queue_details = lib.getconfig.getparam('RabbitMQ', 'queue_details')
cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
check_type = 'rabbitmq'


def runcheck():
    try:
        url1=rabbit_url+'/api/overview'
        jsondata=lib.pushdata.JonSon()
        jsondata.prepare_data()
        stats_json = json.loads(lib.commonclient.httpget(__name__, url1, rabbit_auth))
        timestamp = int(datetime.datetime.now().strftime("%s"))
        message_stats = ('publish','ack','deliver_get','redeliver','deliver')
        queue_totals = ('messages','messages_ready','messages_unacknowledged')
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

        if queue_details is True :
            url2 = rabbit_url + '/api/queues'
            rabbit_queues = json.loads(lib.commonclient.httpget(__name__, url2, rabbit_auth))
            import re
            for name in range(len(rabbit_queues)):
                mname = 'rabbitmq_'+re.sub('[^a-zA-Z0-9]', '_', str(rabbit_queues[name]['name']))
                mvalue = str(rabbit_queues[name]['messages'])
                jsondata.gen_data(mname, timestamp, mvalue, lib.pushdata.hostname, check_type, cluster_name)
                details = ('publish_details', 'deliver_details')
                for detail in details :
                    if 'message_stats' in rabbit_queues[name]:
                        if detail in rabbit_queues[name]['message_stats']:
                            rname = 'rabbitmq_' + str(rabbit_queues[name]['name']) + '_'+ detail
                            rnamesub ='rabbitmq_'+re.sub('[^a-zA-Z0-9]', '_', rname)
                            rvalue = rabbit_queues[name]['message_stats'][detail]['rate']
                            jsondata.gen_data(rnamesub, timestamp, rvalue, lib.pushdata.hostname, check_type, cluster_name)
        jsondata.put_json()
    except Exception as e:
        lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
        pass

