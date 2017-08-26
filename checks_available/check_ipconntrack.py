import lib.record_rate
import lib.getconfig
import lib.puylogger
import datetime
import os.path

check_type = 'system'

cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
reaction = -3


if os.path.exists('/proc/sys/net/ipv4/netfilter/ip_conntrack_max'):
    conntrack_max = '/proc/sys/net/ipv4/netfilter/ip_conntrack_max'
if os.path.exists('/proc/sys/net/ipv4/netfilter/ip_conntrack_count'):
    conntrack_cur = '/proc/sys/net/ipv4/netfilter/ip_conntrack_count'
if os.path.exists('/proc/sys/net/netfilter/nf_conntrack_max'):
    conntrack_max = '/proc/sys/net/netfilter/nf_conntrack_max'
if os.path.exists('/proc/sys/net/netfilter/nf_conntrack_count'):
    conntrack_cur = '/proc/sys/net/netfilter/nf_conntrack_count'

def runcheck():
    local_vars = []
    try:
        maxx = open(conntrack_max, 'r')
        curr = open(conntrack_cur, 'r')
        timestamp = int(datetime.datetime.now().strftime("%s"))
        local_vars.append({'name': 'conntrack_cur', 'timestamp': timestamp, 'value': curr.read().rstrip(), 'check_type': check_type})
        local_vars.append({'name': 'conntrack_max', 'timestamp': timestamp, 'value': maxx.read().rstrip(), 'check_type': check_type, 'reaction': reaction})
        maxx.close()
        curr.close()
        return local_vars
    except Exception as e:
        lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
        pass
