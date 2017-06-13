import lib.record_rate
import lib.pushdata
import lib.getconfig
import lib.puylogger
import lib.commonclient
import datetime
import json

riak_url = lib.getconfig.getparam('Riak', 'stats')
cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
check_type = 'riak'


def runcheck():
    try:
        jsondata = lib.pushdata.JonSon()
        jsondata.prepare_data()
        stats_json = json.loads(lib.commonclient.httpget(__name__, riak_url))
        metrics= ('sys_process_count', 'memory_processes', 'memory_processes_used', 'node_gets', 'node_puts', 'vnode_gets', 'vnode_puts')
        timestamp = int(datetime.datetime.now().strftime("%s"))
        for metric in metrics:
            if metric is 'node_gets':
                myvalue = stats_json[metric]/60
            elif metric is 'node_puts':
                myvalue = stats_json[metric]/60
            elif metric is 'vnode_gets':
                myvalue = stats_json[metric]/60
            elif metric is 'vnode_puts':
                myvalue = stats_json[metric]/60
            else:
                myvalue = stats_json[metric]
            jsondata.gen_data('riak_'+metric, timestamp, myvalue, lib.pushdata.hostname, check_type, cluster_name)
        jsondata.put_json()
    except Exception as e:
        lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
        pass



