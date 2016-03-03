import os, sys
import ConfigParser
import datetime
import socket

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')

zk_host = config.get('ZooKeeper', 'host')
zk_port = int(config.get('ZooKeeper', 'port'))
hostname = socket.getfqdn()
cluster_name = config.get('SelfConfig', 'cluster_name')
check_type = 'zookeeper'

buffer_size = 1024
message = "mntr"

def run_zookeeper():
    try:
        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
        push = __import__('pushdata')
        value_rate= __import__('record_rate')

        jsondata=push.JonSon()
        jsondata.create_data()
        rate=value_rate.ValueRate()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((zk_host, zk_port))
        s.send(message)
        raw_data = s.recv(buffer_size)
        s.close()
        timestamp = int(datetime.datetime.now().strftime("%s"))

        metrics=('zk_avg_latency', 'zk_max_latency', 'zk_min_latency', 'zk_packets_received', 'zk_packets_sent', 'zk_open_file_descriptor_count','zk_max_file_descriptor_count'\
                 'zk_num_alive_connections', 'zk_outstanding_requests', 'zk_znode_count', 'zk_watch_count', 'zk_ephemerals_count', 'zk_approximate_data_size')
        for line in raw_data.split('\n'):
            for searchitem in  metrics:
                if searchitem in line:
                    key=line.split('\t')[0]
                    value=int(line.split('\t')[1])
                    if searchitem == 'zk_packets_received':
                        value=rate.record_value_rate('zk_packets_received', value, timestamp)
                    if searchitem == 'zk_packets_sent':
                        value=rate.record_value_rate('zk_packets_sent', value, timestamp)
                    jsondata.gen_data(key, timestamp, value, push.hostname, check_type, cluster_name)
        jsondata.put_json()
        jsondata.truncate_data()
    except Exception as e:
        push = __import__('pushdata')
        push.print_error(__name__ , (e))
        pass
