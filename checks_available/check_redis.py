import lib.record_rate
import lib.pushdata
import os, sys
import ConfigParser
import datetime
import socket

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/sql_cache.ini')

redis_host = config.get('Redis', 'host')
redis_port = int(config.get('Redis', 'port'))
hostname = socket.getfqdn()
cluster_name = config.get('SelfConfig', 'cluster_name')
check_type = 'redis'

buffer_size = 4096
message = "INFO\r\n"

def runcheck():
    try:
        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')

        jsondata=lib.pushdata.JonSon()
        jsondata.prepare_data()
        rate=lib.record_rate.ValueRate()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((redis_host, redis_port))
        s.send(message)
        raw_data = s.recv(buffer_size)
        s.close()
        timestamp = int(datetime.datetime.now().strftime("%s"))

        ms=('connected_clients', 'used_memory', 'used_memory_rss','used_memory_peak' ,
            'keyspace_hits', 'keyspace_misses', 'uptime_in_seconds','mem_fragmentation_ratio',
            'rdb_changes_since_last_save', 'rdb_bgsave_in_progress', 'rdb_last_bgsave_time_sec', 'rdb_current_bgsave_time_sec'
            )
        ms_rated=('total_commands_processed', 'expired_keys', 'evicted_keys', 'total_net_input_bytes', 'total_net_output_bytes')

        datadict={}
        for line in raw_data.splitlines():
            if ':' in line:
                line2=line.split(":")
                datadict.update({line2[0]: line2[1]})

        for key, value in datadict.iteritems():
            if key in ms:
                try:
                    value = int(value)
                except:
                    pass
                jsondata.gen_data('redis_' + key, timestamp, value, lib.pushdata.hostname, check_type, cluster_name)
            if key in ms_rated:
                vrate = rate.record_value_rate('redis_' + key , value, timestamp)
                jsondata.gen_data('redis_' + key, timestamp, vrate, lib.pushdata.hostname, check_type, cluster_name)

        jsondata.put_json()
    except Exception as e:
        lib.pushdata.print_error(__name__ , (e))
        pass