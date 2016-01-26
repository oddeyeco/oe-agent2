import os, sys
import datetime
import ConfigParser

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
cluster_name = config.get('SelfConfig', 'cluster_name')


def run_ipconntrack():
    try:
        max=open('/proc/sys/net/ipv4/netfilter/ip_conntrack_max', 'r').read().rstrip()
        cur=open('/proc/sys/net/ipv4/netfilter/ip_conntrack_count', 'r').read().rstrip()
        check_type = 'system'
        timestamp = int(datetime.datetime.now().strftime("%s"))
        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
        push = __import__('pushdata')
        jsondata=push.JonSon()
        jsondata.create_data()
        jsondata.gen_data('conntrack_max', timestamp, max, push.hostname, check_type, cluster_name)
        jsondata.gen_data('conntrack_cur', timestamp, cur, push.hostname, check_type, cluster_name)
        jsondata.put_json()
        jsondata.truncate_data()
    except Exception as e:
        push = __import__('pushdata')
        push.print_error(e)
        pass
