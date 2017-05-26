import lib.record_rate
import lib.pushdata
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

        jsondata = lib.pushdata.JonSon()
        jsondata.prepare_data()
        rate = lib.record_rate.ValueRate()
        raw_data = lib.commonclient.socketget(__name__, buffer_size, zk_host, zk_port, message)
        timestamp = int(datetime.datetime.now().strftime("%s"))

        metrics=('zk_avg_latency', 'zk_max_latency', 'zk_min_latency', 'zk_packets_received', 'zk_packets_sent', 'zk_open_file_descriptor_count','zk_max_file_descriptor_count'\
                 'zk_num_alive_connections', 'zk_outstanding_requests', 'zk_znode_count', 'zk_watch_count', 'zk_ephemerals_count', 'zk_approximate_data_size')
        for line in raw_data.split('\n'):
            for searchitem in  metrics:
                if searchitem in line:
                    key=line.split('\t')[0]
                    value=int(line.split('\t')[1])
                    #if searchitem == 'zk_packets_received':
                    #    value=rate.record_value_rate('zk_packets_received', value, timestamp)
                    #if searchitem == 'zk_packets_sent':
                    #    value=rate.record_value_rate('zk_packets_sent', value, timestamp)
                    if searchitem == 'zk_packets_received' or searchitem == 'zk_packets_sent':
                        value_rate=rate.record_value_rate(searchitem, value, timestamp)
                        jsondata.gen_data(searchitem, timestamp, value_rate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')
                    else:
                        jsondata.gen_data(key, timestamp, value, lib.pushdata.hostname, check_type, cluster_name)
        jsondata.put_json()
    except Exception as e:
        lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
        pass
