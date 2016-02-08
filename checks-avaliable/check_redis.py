import os, sys
import ConfigParser
import datetime
import socket




config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')

redis_host = config.get('Redis', 'host')
redis_port = int(config.get('Redis', 'port'))
hostname = socket.getfqdn()
cluster_name = config.get('SelfConfig', 'cluster_name')
check_type = 'redis'

buffer_size = 1024
message = "INFO\r\n"

def run_redis():
    try:
        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
        push = __import__('pushdata')
        value_rate= __import__('record_rate')

        jsondata=push.JonSon()
        jsondata.create_data()
        rate=value_rate.ValueRate()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((redis_host, redis_port))
        s.send(message)
        raw_data = s.recv(buffer_size)
        s.close()
        timestamp = int(datetime.datetime.now().strftime("%s"))
        metrics=('connected_clients', 'used_memory:', 'used_memory_rss:', 'used_memory_peak:', 'changes_since_last_save', 'keyspace_hits', 'keyspace_misses', 'uptime_in_seconds', 'total_commands_processed')
        for line in raw_data.split('\n'):
            for searchitem in  metrics:
                if searchitem in line:
                    key=line.split(':')[0]
                    value=int(line.split(':')[1].rstrip('\r'))
                    if searchitem == 'total_commands_processed':
                        value=rate.record_value_rate('redis_commands_processed', value, timestamp)
                        key='commands_rate'
                    if searchitem == 'keyspace_hits':
                        value=rate.record_value_rate('redis_keyspace_hits', value, timestamp)
                    if searchitem == 'keyspace_misses':
                        value=rate.record_value_rate('redis_keyspace_misses', value, timestamp)
                    jsondata.gen_data('redis_'+key, timestamp, value, push.hostname, check_type, cluster_name)
        jsondata.put_json()
        jsondata.truncate_data()
    except Exception as e:
        push = __import__('pushdata')
        push.print_error(__name__ , (e))
        pass
