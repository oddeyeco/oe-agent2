import lib.commonclient
import lib.getconfig
import lib.puylogger
import lib.basecheck
import json

rabbit_url = lib.getconfig.getparam('RabbitMQ', 'stats')
rabbit_user = lib.getconfig.getparam('RabbitMQ', 'user')
rabbit_pass = lib.getconfig.getparam('RabbitMQ', 'pass')
rabbit_auth = lib.getconfig.getparam('RabbitMQ', 'user')+':'+lib.getconfig.getparam('RabbitMQ', 'pass')

queue_details = lib.getconfig.getparam('RabbitMQ', 'queue_details')
check_type = 'rabbitmq'


class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            url1 = rabbit_url+'/api/overview'
            stats_json = json.loads(lib.commonclient.httpget(__name__, url1, rabbit_auth))
            message_stats = ('publish','ack','deliver_get','redeliver','deliver')
            queue_totals = ('messages','messages_ready','messages_unacknowledged')
            for stats in message_stats:
                try:
                    stats_name = 'rabbitmq_'+stats+'_rate'
                    stats_value = stats_json['message_stats'][stats+'_details']['rate']
                    self.local_vars.append({'name': stats_name, 'timestamp': self.timestamp, 'value': stats_value, 'chart_type': 'Rate', 'check_type': check_type})
                except Exception as e:
                    lib.puylogger.print_message('Cannot get stats for ' + str(e))
                    pass
    
            for queue in queue_totals:
                queue_name = 'rabbitmq_'+queue
                queue_value = stats_json['queue_totals'][queue]
                self.local_vars.append({'name': queue_name, 'timestamp': self.timestamp, 'value': queue_value, 'check_type': check_type})
    
            if queue_details is True :
                url2 = rabbit_url + '/api/queues'
                rabbit_queues = json.loads(lib.commonclient.httpget(__name__, url2, rabbit_auth))
                import re
                for name in range(len(rabbit_queues)):
                    mname = re.sub('[^a-zA-Z0-9]', '_', str(rabbit_queues[name]['name']))
                    mvalue = str(rabbit_queues[name]['messages'])
                    self.local_vars.append({'name': 'rabbitmq_perqueue_messages', 'timestamp': self.timestamp, 'value': mvalue, 'check_type': check_type, 'extra_tag':{'queue': mname}})
                    details = ('publish_details', 'deliver_details')
                    for detail in details :
                        if 'message_stats' in rabbit_queues[name]:
                            if detail in rabbit_queues[name]['message_stats']:
                                rname = 'rabbitmq_' + str(rabbit_queues[name]['name']) + '_'+ detail
                                rnamesub  = re.sub('[^a-zA-Z0-9]', '_', rname)
                                rvalue = rabbit_queues[name]['message_stats'][detail]['rate']
                                self.local_vars.append({'name': 'rabbitmq_perqueue_' + detail.replace('_details', ''), 'timestamp': self.timestamp, 'value': rvalue, 'check_type': check_type, 'extra_tag':{'queue': rnamesub}})
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass
    
