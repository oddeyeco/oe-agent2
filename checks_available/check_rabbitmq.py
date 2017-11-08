import lib.commonclient
import lib.record_rate
import lib.getconfig
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
    local_vars = []
    try:
        url1 = rabbit_url+'/api/overview'
        stats_json = json.loads(lib.commonclient.httpget(__name__, url1, rabbit_auth))
        timestamp = int(datetime.datetime.now().strftime("%s"))
        message_stats = ('publish','ack','deliver_get','redeliver','deliver')
        queue_totals = ('messages','messages_ready','messages_unacknowledged')
        for stats in message_stats:
            try:
                stats_name = 'rabbitmq_'+stats+'_rate'
                stats_value = stats_json['message_stats'][stats+'_details']['rate']
                local_vars.append({'name': stats_name, 'timestamp': timestamp, 'value': stats_value, 'chart_type': 'Rate', 'check_type': check_type})
            except Exception as e:
                lib.puylogger.print_message('Cannot get stats for ' + str(e))
                pass

        for queue in queue_totals:
            queue_name = 'rabbitmq_'+queue
            queue_value = stats_json['queue_totals'][queue]
            local_vars.append({'name': queue_name, 'timestamp': timestamp, 'value': queue_value, 'check_type': check_type})

        if queue_details is True :
            url2 = rabbit_url + '/api/queues'
            rabbit_queues = json.loads(lib.commonclient.httpget(__name__, url2, rabbit_auth))
            import re
            for name in range(len(rabbit_queues)):
                mname = re.sub('[^a-zA-Z0-9]', '_', str(rabbit_queues[name]['name']))
                mvalue = str(rabbit_queues[name]['messages'])
                local_vars.append({'name': 'rabbitmq_perqueue_messages', 'timestamp': timestamp, 'value': mvalue, 'check_type': check_type, 'extra_tag':{'queue': mname}})
                details = ('publish_details', 'deliver_details')
                for detail in details :
                    if 'message_stats' in rabbit_queues[name]:
                        if detail in rabbit_queues[name]['message_stats']:
                            rname = 'rabbitmq_' + str(rabbit_queues[name]['name']) + '_'+ detail
                            rnamesub  = re.sub('[^a-zA-Z0-9]', '_', rname)
                            rvalue = rabbit_queues[name]['message_stats'][detail]['rate']
                            local_vars.append({'name': 'rabbitmq_perqueue_' + detail.replace('_details', ''), 'timestamp': timestamp, 'value': rvalue, 'check_type': check_type, 'extra_tag':{'queue': rnamesub}})
        return  local_vars
    except Exception as e:
        lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
        pass

