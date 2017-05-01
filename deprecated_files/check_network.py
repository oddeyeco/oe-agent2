import psutil, os, datetime, sys
import ConfigParser

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
cluster_name = config.get('SelfConfig', 'cluster_name')


def run_network():
    sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
    push = __import__('pushdata')
    value_rate= __import__('record_rate')

    raw_netstats = str(psutil.network_io_counters())
    split_netstats = raw_netstats.split('(')[-1].split(')')[0]
    check_type = 'system'

    net_list = [x.strip() for x in split_netstats.split(',')]
    jsondata=push.JonSon()
    jsondata.create_data()
    rate=value_rate.ValueRate()
    try:
        for index in range(0, len(net_list)):
            timestamp = int(datetime.datetime.now().strftime("%s"))
            ruzan=net_list[index].split('=')[0]
            if ruzan == 'bytes_sent' or ruzan == 'bytes_recv':
                mytype = 'net_'+net_list[index].split('=')[0]
                myvalue = net_list[index].split('=')[1]
                net_rate=rate.record_value_rate(mytype, myvalue, timestamp)
                jsondata.gen_data(mytype, timestamp, net_rate, push.hostname, check_type, cluster_name)
        jsondata.put_json()
        jsondata.truncate_data()
    except Exception as e:
        push = __import__('pushdata')
        push.print_error(__name__ , (e))
        pass
