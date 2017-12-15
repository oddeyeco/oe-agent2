import lib.record_rate
import lib.commonclient
import lib.getconfig
import lib.puylogger
import lib.pushdata
import lib.basecheck
import json

baseurl = lib.getconfig.getparam('Docker', 'stats')
detailed_mon = lib.getconfig.getparam('Docker', 'detailed')
prettynames = lib.getconfig.getparam('Docker', 'prettynames')
memstats = lib.getconfig.getparam('Docker', 'memstats')
check_type = 'docker'


class Check(lib.basecheck.CheckBase):

    def precheck(self):
            
        containers = []
        try:
            jsondata = lib.pushdata.JonSon()
            jsondata.prepare_data()
            base_json = json.loads(lib.commonclient.httpget(__name__, baseurl + '/json'))
            containers.append(base_json[0]['Id'])
            containers.append(base_json[1]['Id'])
    
            for container in containers:
                data = json.loads(lib.commonclient.httpget(__name__, baseurl + '/' + container + '/stats?logs=0&stream=0'))
                if prettynames is True:
                    container_name = data['name'].replace('/','')
                else:
                    container_name = container
                cpu_delta = data['cpu_stats']['cpu_usage']['total_usage'] - data['precpu_stats']['cpu_usage']['total_usage']
                system_delta = data['cpu_stats']['system_cpu_usage'] - data['precpu_stats']['system_cpu_usage']
    
                cpu_sage = float("{0:.3f}".format(cpu_delta / system_delta * 100))
                throttled_periods = data['cpu_stats']['throttling_data']['throttled_periods']
                throttled_time = data['cpu_stats']['throttling_data']['throttled_time']
                self.local_vars.append({'name': check_type + '_master_cpu_usage', 'timestamp': self.timestamp, 'value': cpu_sage,'chart_type': 'Percent', 'check_type': check_type,  'extra_tag':{'container': container_name}})
                self.local_vars.append({'name': check_type + '_cpu_throttled_periods', 'timestamp': self.timestamp, 'value': throttled_periods, 'check_type': check_type, 'extra_tag':{'container': container_name}})
                self.local_vars.append({'name': check_type + '_cpu_throttled_time', 'timestamp': self.timestamp, 'value': throttled_time, 'check_type': check_type, 'extra_tag':{'container': container_name}})
    
                getval = lib.record_rate.GetPrevValue()
                prev_cpu_usage = getval.return_last_value('cpu_total_usage_' + container_name, data['cpu_stats']['cpu_usage']['total_usage'])
                prev_system_usage = getval.return_last_value('cpu_system_usage_'+ container_name, data['cpu_stats']['system_cpu_usage'])
    
                cpudelta = data['cpu_stats']['cpu_usage']['total_usage'] - prev_cpu_usage
                systemdelta = data['cpu_stats']['system_cpu_usage'] - prev_system_usage
                num_cpu = len(data['precpu_stats']['cpu_usage']['percpu_usage'])
    
                cpu_percent = (cpudelta / systemdelta) * num_cpu * 100.0
                self.local_vars.append({'name': check_type + '_container_cpu_usage', 'timestamp': self.timestamp, 'value': float("{:.2f}".format(cpu_percent)), 'chart_type': 'Percent', 'check_type': check_type, 'extra_tag':{'container': container_name}})
    
                network = data['networks']
                for k, v in network.items():
                    bytes_rx = data['networks'][k]['rx_bytes']
                    bytes_tx = data['networks'][k]['tx_bytes']
                    self.local_vars.append({'name': check_type + '_bytes_rx_' + k, 'extra_tag':{'container': container_name}, 'timestamp': self.timestamp, 'value': bytes_rx, 'check_type': check_type, 'chart_type': 'Rate'})
                    self.local_vars.append({'name': check_type + '_bytes_tx_' + k, 'extra_tag':{'container': container_name}, 'timestamp': self.timestamp, 'value': bytes_tx, 'check_type': check_type, 'chart_type': 'Rate'})
                    if detailed_mon is True:
                        netchecks_stack = ('rx_errors', 'tx_errors', 'rx_dropped', 'tx_dropped')
                        netchecks_rated = ('rx_packets', 'tx_packets')
                        for netcheck_rated in netchecks_rated:
                            value = self.rate.record_value_rate(container + netcheck_rated , data['networks'][k][netcheck_rated], self.timestamp)
                            self.local_vars.append({'name': check_type + '_' + netcheck_rated + '_' + k, 'timestamp': self.timestamp, 'value': value, 'check_type': check_type, 'chart_type': 'Rate','extra_tag':{'container': container_name}})
                        for netcheck_stack in netchecks_stack:
                            value = data['networks'][k][netcheck_stack]
                            self.local_vars.append({'name': check_type + '_' + netcheck_stack + '_' + k, 'timestamp': self.timestamp, 'value': value, 'check_type': check_type, 'extra_tag':{'container': container_name}})
    
                if memstats is True:
                    mem_cur_usage = data['memory_stats']['usage']
                    mem_max_usage = data['memory_stats']['max_usage']
                    self.local_vars.append({'name': check_type + '_mem_cur_usage', 'timestamp': self.timestamp, 'value': mem_cur_usage, 'check_type': check_type, 'extra_tag':{'container': container_name}})
                    self.local_vars.append({'name': check_type + '_mem_max_usage', 'timestamp': self.timestamp, 'value': mem_max_usage, 'check_type': check_type, 'extra_tag':{'container': container_name}})
                    if detailed_mon is True:
                        memchecks = ('total_active_anon', 'total_active_file', 'total_cache',
                                     'total_inactive_anon', 'total_inactive_file', 'total_mapped_file',
                                     'total_rss', 'total_swap', 'total_unevictable')
                        for memcheck in memchecks:
                            value = data['memory_stats']['stats'][memcheck]
                            self.local_vars.append({'name': check_type + '_mem_' + memcheck, 'timestamp': self.timestamp, 'value': value, 'check_type': check_type, 'extra_tag':{'container': container_name}})
    
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass
    
    
    
