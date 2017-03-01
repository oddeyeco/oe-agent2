import os, datetime, sys, glob
import ConfigParser
import lib.pushdata
import lib.record_rate

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
cluster_name = config.get('SelfConfig', 'cluster_name')

check_localhost = False
rated = True


def run_network_bytes():
    sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')

    check_type = 'system'
    jsondata=lib.pushdata.JonSon()
    jsondata.prepare_data()
    rate=lib.record_rate.ValueRate()
    timestamp = int(datetime.datetime.now().strftime("%s"))
    try:
        ifaces=glob.glob("/sys/class/net/*")
        iflist=[]
        for index in range(0, len(ifaces)):
            if check_localhost is False:
                iface = ifaces[index].split('/')[4]
                if "/lo" not in ifaces[index]:
                    iflist.append(iface)
            else:
                iface = ifaces[index].split('/')[4]
                iflist.append(iface)

        for nic in iflist:
            rx = int(open("/sys/class/net/" + nic + "/statistics/rx_bytes", "r").read())
            tx = int(open("/sys/class/net/" + nic + "/statistics/tx_bytes", "r").read())
            if rx is not 0 or tx is not 0:
                txname = 'bytes_tx_' + nic
                rxname = 'bytes_rx_' + nic
                if rated is True:
                    rxrate = rate.record_value_rate(rxname, rx, timestamp)
                    txrate = rate.record_value_rate(txname, tx, timestamp)
                    jsondata.gen_data(txname, timestamp, txrate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')
                    jsondata.gen_data(rxname, timestamp, rxrate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')
                else:
                    jsondata.gen_data(txname, timestamp, tx, lib.pushdata.hostname, check_type, cluster_name, 0, 'Counter')
                    jsondata.gen_data(rxname, timestamp, rx, lib.pushdata.hostname, check_type, cluster_name, 0, 'Counter')
        jsondata.put_json()

    except Exception as e:
        lib.pushdata.print_error(__name__ , (e))
        pass