import lib.record_rate
import lib.getconfig
import lib.puylogger
import lib.basecheck
import os.path

check_type = 'system'
reaction = -3

if os.path.exists('/proc/sys/net/ipv4/netfilter/ip_conntrack_max'):
    conntrack_max = '/proc/sys/net/ipv4/netfilter/ip_conntrack_max'
if os.path.exists('/proc/sys/net/ipv4/netfilter/ip_conntrack_count'):
    conntrack_cur = '/proc/sys/net/ipv4/netfilter/ip_conntrack_count'
if os.path.exists('/proc/sys/net/netfilter/nf_conntrack_max'):
    conntrack_max = '/proc/sys/net/netfilter/nf_conntrack_max'
if os.path.exists('/proc/sys/net/netfilter/nf_conntrack_count'):
    conntrack_cur = '/proc/sys/net/netfilter/nf_conntrack_count'

class Check(lib.basecheck.CheckBase):
    def precheck(self):
        try:
            maxx = open(conntrack_max, 'r')
            curr = open(conntrack_cur, 'r')
            self.local_vars.append({'name': 'conntrack_cur', 'timestamp': self.timestamp, 'value': curr.read().rstrip(), 'check_type': check_type})
            self.local_vars.append({'name': 'conntrack_max', 'timestamp': self.timestamp, 'value': maxx.read().rstrip(), 'check_type': check_type, 'reaction': reaction})
            maxx.close()
            curr.close()
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass
