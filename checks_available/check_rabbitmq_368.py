import lib.commonclient
import lib.record_rate
import lib.getconfig
import lib.puylogger
import datetime
import json
import re

rabbit_url = lib.getconfig.getparam('RabbitMQ 3.6', 'stats')
rabbit_user = lib.getconfig.getparam('RabbitMQ 3.6', 'user')
rabbit_pass = lib.getconfig.getparam('RabbitMQ 3.6', 'pass')
rabbit_auth = lib.getconfig.getparam('RabbitMQ 3.6', 'user')+':'+lib.getconfig.getparam('RabbitMQ 3.6', 'pass')
queue_details = lib.getconfig.getparam('RabbitMQ 3.6', 'queue_details')

if queue_details is True:
    try:
        rabbit_queues_needed = lib.getconfig.getparam('RabbitMQ 3.6', 'desired_queues').replace(' ', '').split(',')
        all_queues = False
    except:
        lib.puylogger.print_message(__name__ + ' WARNING : Parameter "desired_queues" is missing, monitoring all existing Queues')
        all_queues = True
        rabbit_queues_needed = ()


cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
check_type = 'rabbitmq'


def runcheck():
    local_vars = []
    try:
        url1 = rabbit_url+'/api/overview'
        stats_json = json.loads(lib.commonclient.httpget(__name__, url1, rabbit_auth))
        timestamp = int(datetime.datetime.now().strftime("%s"))
        queue_totals = ('messages','messages_ready','messages_unacknowledged')
        queue_rates = ('messages_details','messages_ready_details','messages_unacknowledged_details')
        for queue in queue_totals:
            local_vars.append({'name': 'rabbitmq_'+queue, 'timestamp': timestamp, 'value': stats_json['queue_totals'][queue], 'check_type': check_type, 'extra_tag':{'queue': 'all'}})

        for qrate in queue_rates:
            local_vars.append({'name': 'rabbitmq_'+ qrate, 'timestamp': timestamp, 'value': stats_json['queue_totals'][qrate]['rate'], 'check_type': check_type, 'extra_tag':{'queue': 'all'}})

        if queue_details is True:
            url2 = rabbit_url + '/api/queues'
            rabbit_queues = json.loads(lib.commonclient.httpget(__name__, url2, rabbit_auth))
            stats = ('messages', 'messages_unacknowledged', 'messages_ready',
                     'message_bytes_persistent', 'message_bytes_ram',
                     'messages_persistent', 'messages_ram')
            for index in range(len(rabbit_queues)):
                nme = str(rabbit_queues[index]['name'])
                if nme in rabbit_queues_needed and all_queues is False:
                    for stat in stats :
                        nn = 'rabbitmq_' + stat
                        name = re.sub('[^a-zA-Z0-9]', '_', str(rabbit_queues[index]['name']))
                        value = rabbit_queues[index][stat]
                        local_vars.append({'name': nn, 'timestamp': timestamp, 'value': value, 'check_type': check_type, 'extra_tag':{'queue': name}})

                if all_queues is True:
                    for stat in stats :
                        nn = 'rabbitmq_' + stat
                        name = re.sub('[^a-zA-Z0-9]', '_', str(rabbit_queues[index]['name']))
                        value = rabbit_queues[index][stat]
                        local_vars.append({'name': nn, 'timestamp': timestamp, 'value': value, 'check_type': check_type, 'extra_tag':{'queue': name}})

        return local_vars
    except Exception as e:
        lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
        pass
