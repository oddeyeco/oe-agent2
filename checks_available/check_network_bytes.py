import glob
import lib.getconfig
import lib.pushdata
import lib.record_rate
import lib.puylogger
import lib.basecheck

check_type = 'system'
check_localhost = lib.getconfig.getparam('Network Stats', 'localhost')
rated = lib.getconfig.getparam('Network Stats', 'rated')


class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            ifaces = glob.glob("/sys/class/net/*")
            iflist = []
            for index in range(0, len(ifaces)):
                if check_localhost is False:
                    iface = ifaces[index].split('/')[4]
                    if "/lo" not in ifaces[index]:
                        iflist.append(iface)
                else:
                    iface = ifaces[index].split('/')[4]
                    iflist.append(iface)

            for nic in iflist:
                rxb = open("/sys/class/net/" + nic + "/statistics/rx_bytes", "r")
                txb = open("/sys/class/net/" + nic + "/statistics/tx_bytes", "r")
                rx = int(rxb.read())
                tx = int(txb.read())

                rx_last = self.last.return_last_value('network_rx_last' + nic, rx)
                tx_last = self.last.return_last_value('network_tx_last' + nic, tx)

                if rx > rx_last or tx > tx_last:
                    txname = 'bytes_tx'
                    rxname = 'bytes_rx'
                    if rated is True:
                        rxrate = self.rate.record_value_rate(rxname + nic, rx, self.timestamp)
                        txrate = self.rate.record_value_rate(txname + nic, tx, self.timestamp)
                        self.local_vars.append({'name':rxname, 'timestamp': self.timestamp, 'value':rxrate, 'chart_type': 'Rate', 'check_type': check_type, 'reaction': 0, 'extra_tag':{'interface': nic}})
                        self.local_vars.append({'name':txname, 'timestamp': self.timestamp, 'value':txrate, 'chart_type': 'Rate', 'check_type': check_type, 'reaction': 0, 'extra_tag':{'interface': nic}})
                    else:
                        self.local_vars.append({'name':rxname, 'timestamp': self.timestamp, 'value':rxrate, 'chart_type': 'Counter', 'check_type': check_type, 'reaction': 0, 'extra_tag':{'interface': nic}})
                        self.local_vars.append({'name':txname, 'timestamp': self.timestamp, 'value':txrate, 'chart_type': 'Counter', 'check_type': check_type, 'reaction': 0, 'extra_tag':{'interface': nic}})

                rxb.close()
                txb.close()
        except Exception as e:
            lib.pushdata.print_error(__name__ , (e))
            pass

