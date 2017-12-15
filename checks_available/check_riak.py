import lib.record_rate
import lib.getconfig
import lib.puylogger
import lib.commonclient
import lib.basecheck
import json

riak_url = lib.getconfig.getparam('Riak', 'stats')
check_type = 'riak'


class Check(lib.basecheck.CheckBase):

    def precheck(self):

        try:
            stats_json = json.loads(lib.commonclient.httpget(__name__, riak_url))
            metrics= ('sys_process_count', 'memory_processes', 'memory_processes_used', 'mem_allocated',
                      'node_gets', 'node_puts', 'vnode_gets', 'vnode_puts', 'read_repairs', 'vnode_set_update')
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
                self.local_vars.append({'name': 'riak_'+metric, 'timestamp': self.timestamp, 'value': myvalue, 'check_type': check_type, 'chart_type': 'Rate'})
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass



