import lib.record_rate
import lib.pushdata
import os, sys
import datetime
import ConfigParser


config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
cluster_name = config.get('SelfConfig', 'cluster_name')
reaction = -3


def runcheck():
    try:
        max=open('/proc/sys/net/ipv4/netfilter/ip_conntrack_max', 'r').read().rstrip()
        cur=open('/proc/sys/net/ipv4/netfilter/ip_conntrack_count', 'r').read().rstrip()
        check_type = 'system'
        timestamp = int(datetime.datetime.now().strftime("%s"))
        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
        jsondata=lib.pushdata.JonSon()
        jsondata.prepare_data()
        jsondata.gen_data('conntrack_max', timestamp, max, lib.pushdata.hostname, check_type, cluster_name, reaction)
        jsondata.gen_data('conntrack_cur', timestamp, cur, lib.pushdata.hostname, check_type, cluster_name)
        jsondata.put_json()
    except Exception as e:
        lib.pushdata.print_error(__name__ , (e))
        pass
