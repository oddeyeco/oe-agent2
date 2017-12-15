import lib.record_rate
import lib.getconfig
import lib.puylogger
import lib.commonclient
import lib.basecheck

memcached_host = lib.getconfig.getparam('Memcached', 'host')
memcached_port = int(lib.getconfig.getparam('Memcached', 'port'))
cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
check_type = 'memcached'
buffer_size = 2048
message = "stats\nquit"


class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            rate = lib.record_rate.ValueRate()
            raw_data = lib.commonclient.socketget(__name__, buffer_size, memcached_host, memcached_port, message)
            metrics_stuck = ('curr_connections', 'curr_items', 'rusage_user', 'rusage_system', 'get_misses', 'incr_misses', 'evictions', 'limit_maxbytes')
            metrics_rated = ('cmd_get', 'cmd_set', 'get_hits', 'set_hits', 'delete_misses', 'delete_hits', ' bytes ', 'bytes_read', 'bytes_written')
            for line in raw_data.split('\n'):
                for searchitem in metrics_stuck:
                    if searchitem in line:
                        key = line.split(' ')[1]
                        value = line.split(' ')[2].rstrip('\r')
                        self.local_vars.append({'name': 'memcached_' + key, 'timestamp': self.timestamp, 'value': value, 'check_type': check_type})
                for searchitem in metrics_rated:
                    if searchitem in line:
                        key = line.split(' ')[1]
                        value = line.split(' ')[2].rstrip('\r')
                        value_rate = rate.record_value_rate('memcached' + key, value, self.timestamp)
                        self.local_vars.append({'name': 'memcached_' + key, 'timestamp': self.timestamp, 'value': value_rate, 'check_type': check_type, 'chart_type': 'Rate'})
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass
