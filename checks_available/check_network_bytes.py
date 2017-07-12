import datetime
import glob
import lib.getconfig
import lib.pushdata
import lib.record_rate
import lib.puylogger

cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
check_localhost = False
rated = True
check_type = 'system'
rate = lib.record_rate.ValueRate()


def runcheck():
    local_vars = []
    timestamp = int(datetime.datetime.now().strftime("%s"))
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
                txname = 'bytes_tx_' + nic
                rxname = 'bytes_rx_' + nic
                if rated is True:
                    rxrate = rate.record_value_rate(rxname, rx, timestamp)
                    txrate = rate.record_value_rate(txname, tx, timestamp)
                    local_vars.append({'name':rxname, 'timestamp': timestamp, 'value':rxrate, 'chart_type': 'Rate', 'check_type': check_type, 'reaction': 0})
                    local_vars.append({'name':txname, 'timestamp': timestamp, 'value':txrate, 'chart_type': 'Rate', 'check_type': check_type, 'reaction': 0})
                else:
                    local_vars.append({'name':rxname, 'timestamp': timestamp, 'value':rxrate, 'chart_type': 'Counter', 'check_type': check_type, 'reaction': 0})
                    local_vars.append({'name':txname, 'timestamp': timestamp, 'value':txrate, 'chart_type': 'Counter', 'check_type': check_type, 'reaction': 0})

            rxb.close()
            txb.close()
        return local_vars
    except Exception as e:
        lib.pushdata.print_error(__name__ , (e))
        pass