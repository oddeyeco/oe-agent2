import lib.record_rate
import lib.getconfig
import lib.commonclient
import lib.puylogger
import datetime


redis_host = lib.getconfig.getparam('Redis', 'host')
redis_port = int(lib.getconfig.getparam('Redis', 'port'))
cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
check_type = 'redis'

buffer_size = 4096
message = "INFO\r\n"

def runcheck():
    try:
        local_vars = []
        rate = lib.record_rate.ValueRate()
        raw_data = lib.commonclient.socketget(__name__, buffer_size, redis_host, redis_port, message)
        timestamp = int(datetime.datetime.now().strftime("%s"))

        ms = ('connected_clients', 'used_memory', 'used_memory_rss','used_memory_peak' ,
            'keyspace_hits', 'keyspace_misses', 'uptime_in_seconds','mem_fragmentation_ratio',
            'rdb_changes_since_last_save', 'rdb_bgsave_in_progress', 'rdb_last_bgsave_time_sec', 'rdb_current_bgsave_time_sec')

        ms_rated = ('total_commands_processed', 'expired_keys', 'evicted_keys', 'total_net_input_bytes', 'total_net_output_bytes')

        datadict = {}
        for line in raw_data.splitlines():
            if ':' in line:
                line2 = line.split(":")
                datadict.update({line2[0]: line2[1]})

        for key, value in list(datadict.items()):
            if key in ms:
                try:
                    value = int(value)
                except:
                    pass
                local_vars.append({'name': 'redis_' + key, 'timestamp': timestamp, 'value': value, 'check_type': check_type})
            if key in ms_rated:
                vrate = rate.record_value_rate('redis_' + key , value, timestamp)
                local_vars.append({'name':'redis_' + key, 'timestamp': timestamp, 'value': value, 'check_type': check_type, 'chart_type': 'Rate'})

        return local_vars
    except Exception as e:
        lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
        pass