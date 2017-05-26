import lib.record_rate
import lib.pushdata
import lib.getconfig
import datetime


cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
reaction = -3


def runcheck():
    try:
        maxx = open('/proc/sys/net/ipv4/netfilter/ip_conntrack_max', 'r')
        curr = open('/proc/sys/net/ipv4/netfilter/ip_conntrack_count', 'r')

        #max = open('/proc/sys/net/ipv4/netfilter/ip_conntrack_max', 'r').read().rstrip()
        #cur = open('/proc/sys/net/ipv4/netfilter/ip_conntrack_count', 'r').read().rstrip()

        check_type = 'system'
        timestamp = int(datetime.datetime.now().strftime("%s"))
        jsondata=lib.pushdata.JonSon()
        jsondata.prepare_data()
        jsondata.gen_data('conntrack_max', timestamp, maxx.read().rstrip(), lib.pushdata.hostname, check_type, cluster_name, reaction)
        jsondata.gen_data('conntrack_cur', timestamp, curr.read().rstrip(), lib.pushdata.hostname, check_type, cluster_name)
        jsondata.put_json()
        maxx.close()
        curr.close()
    except Exception as e:
        lib.pushdata.print_error(__name__ , (e))
        pass
