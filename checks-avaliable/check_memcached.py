import lib.record_rate
import lib.pushdata
import os, sys
import ConfigParser
import datetime
import socket

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/sql_cache.ini')

memcached_host = config.get('Memcached', 'host')
memcached_port = int(config.get('Memcached', 'port'))
hostname = socket.getfqdn()
cluster_name = config.get('SelfConfig', 'cluster_name')
check_type = 'memcached'

buffer_size = 1024
message = "stats\nquit"

def run_memcached():
    try:
        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')

        jsondata=lib.pushdata.JonSon()
        jsondata.prepare_data()
        rate=lib.record_rate.ValueRate()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((memcached_host, memcached_port))
        s.send(message)
        raw_data = s.recv(buffer_size)
        s.close()
        timestamp = int(datetime.datetime.now().strftime("%s"))
        metrics_stuck=('curr_connections', 'curr_items', 'rusage_user', 'rusage_system')
        metrics_rated=('cmd_get', 'cmd_set', 'get_hits', 'set_hits', 'delete_misses', 'delete_hits', 'bytes')
        for line in raw_data.split('\n'):
            for searchitem in  metrics_stuck:
                if searchitem in line:
                    key=line.split(' ')[1]
                    value=line.split(' ')[2].rstrip('\r')
                    jsondata.gen_data('memcached_'+key, timestamp, value, lib.pushdata.hostname, check_type, cluster_name)
            for searchitem in  metrics_rated:
                if searchitem in line:
                    key=line.split(' ')[1]
                    value=line.split(' ')[2].rstrip('\r')
                    value_rate=rate.record_value_rate(key, value, timestamp)
                    jsondata.gen_data('memcached_'+key, timestamp, value_rate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')
        jsondata.put_json()
    except Exception as e:
        lib.pushdata.print_error(__name__ , (e))
        pass
