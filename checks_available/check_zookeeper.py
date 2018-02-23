import lib.record_rate
import lib.getconfig
import lib.commonclient
import lib.puylogger
import lib.basecheck

zk_host = lib.getconfig.getparam('ZooKeeper', 'host')
zk_port = int(lib.getconfig.getparam('ZooKeeper', 'port'))
check_type = 'zookeeper'

buffer_size = 2048
message = 'mntr'

class Check(lib.basecheck.CheckBase):

    def precheck(self):

        try:
            rate = lib.record_rate.ValueRate()
            raw_data = lib.commonclient.socketget(__name__, buffer_size, zk_host, zk_port, message)
            if raw_data is not None:
                for line in raw_data.splitlines():
                    key = line.split('\t')[0]
                    value = line.split('\t')[1]
                    if value.isdigit():
                        if key == 'zk_packets_received' or key == 'zk_packets_sent':
                            value_rate = rate.record_value_rate(key, value, self.timestamp)
                            self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': value_rate, 'chart_type': 'Rate', 'check_type': check_type})
                        else:
                            self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': value, 'check_type': check_type})
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass
