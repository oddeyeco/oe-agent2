import lib.record_rate
import lib.getconfig
import lib.commonclient
import lib.puylogger
import datetime

zk_host = lib.getconfig.getparam('ZooKeeper', 'host')
zk_port = int(lib.getconfig.getparam('ZooKeeper', 'port'))
cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
check_type = 'zookeeper'

buffer_size = 1024
message = "mntr"

def runcheck():
    try:
        local_vars = []
        rate = lib.record_rate.ValueRate()
        raw_data = lib.commonclient.socketget(__name__, buffer_size, zk_host, zk_port, message)
        timestamp = int(datetime.datetime.now().strftime("%s"))

        metrics = ('zk_avg_latency', 'zk_max_latency', 'zk_min_latency', 'zk_packets_received', 'zk_packets_sent', 'zk_open_file_descriptor_count','zk_max_file_descriptor_count'\
                 'zk_num_alive_connections', 'zk_outstanding_requests', 'zk_znode_count', 'zk_watch_count', 'zk_ephemerals_count', 'zk_approximate_data_size')
        if raw_data is not None:
            for line in raw_data.split('\n'):
                for searchitem in  metrics:
                    if searchitem in line:
                        key = line.split('\t')[0]
                        value = int(line.split('\t')[1])
                        if searchitem == 'zk_packets_received' or searchitem == 'zk_packets_sent':
                            value_rate = rate.record_value_rate(searchitem, value, timestamp)
                            local_vars.append({'name': searchitem, 'timestamp': timestamp, 'value': value_rate, 'chart_type': 'Rate', 'check_type': check_type})
                        else:
                            local_vars.append({'name': key, 'timestamp': timestamp, 'value': value, 'check_type': check_type})
        return local_vars
    except Exception as e:
        lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
        pass
