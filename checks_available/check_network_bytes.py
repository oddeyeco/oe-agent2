import datetime
import glob
import lib.getconfig
import lib.pushdata
import lib.record_rate
import lib.puylogger
import lib.basecheck

# cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
check_localhost = False
rated = True
check_type = 'system'
# rate = lib.record_rate.ValueRate()


class Check(lib.basecheck.CheckBase):
    
    def precheck(self):
        local_vars = []
        # timestamp = int(datetime.datetime.now().strftime("%s"))
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

                if rx is not 0 or tx is not 0:
                    txname = 'bytes_tx'
                    rxname = 'bytes_rx'
                    if rated is True:
                        rxrate = self.rate.record_value_rate(rxname + nic, rx, self.timestamp)
                        txrate = self.rate.record_value_rate(txname + nic, tx, self.timestamp)
                        self.local_vars.append({'name':rxname, 'timestamp': self.timestamp, 'value':rxrate, 'chart_type': 'Rate', 'check_type': check_type, 'reaction': 0, 'extra_tag':{'device': nic}})
                        self.local_vars.append({'name':txname, 'timestamp': self.timestamp, 'value':txrate, 'chart_type': 'Rate', 'check_type': check_type, 'reaction': 0, 'extra_tag':{'device': nic}})
                    else:
                        self.local_vars.append({'name':rxname, 'timestamp': self.timestamp, 'value':rxrate, 'chart_type': 'Counter', 'check_type': check_type, 'reaction': 0, 'extra_tag':{'device': nic}})
                        self.local_vars.append({'name':txname, 'timestamp': self.timestamp, 'value':txrate, 'chart_type': 'Counter', 'check_type': check_type, 'reaction': 0, 'extra_tag':{'device': nic}})

                rxb.close()
                txb.close()
            # return local_vars
        except Exception as e:
            lib.pushdata.print_error(__name__ , (e))
            pass