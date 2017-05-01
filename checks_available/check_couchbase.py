import lib.record_rate
import lib.pushdata
import urllib2
import os, sys
import ConfigParser
import datetime
import socket
import json
import lib.puylogger
import re

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/bigdata.ini')


couchbase_url = config.get('CouchBase', 'stats')
buckets = config.get('CouchBase', 'buckets').replace(' ', '').split(',')

hostname = socket.getfqdn()
cluster_name = config.get('SelfConfig', 'cluster_name')
check_type = 'couchbase'

timestamp = int(datetime.datetime.now().strftime("%s"))

def runcheck():
    try:
        for bucket in buckets:
            couchbase_stats = urllib2.urlopen(couchbase_url+'/'+bucket, timeout=5).read()
            sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
            jsondata=lib.pushdata.JonSon()
            jsondata.prepare_data()
            stats_json = json.loads(couchbase_stats)
            stats = ('cmd_get', 'couch_docs_data_size', 'curr_items', 'curr_items_tot', 'ep_bg_fetched', 'get_hits', 'mem_used', 'ops', 'vb_replica_curr_items')
            basicstats= ('quotaPercentUsed', 'opsPerSec', 'hitRatio', 'itemCount', 'memUsed')

            for x in range(0, len(stats_json['nodes'])):
                longname=stats_json['nodes'][x]['hostname'].split(':')[0]

                def is_valid_hostname(hostname):
                    if len(hostname) > 255:
                        return False
                    if hostname[-1] == ".":
                        hostname = hostname[:-1]
                    allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
                    return all(allowed.match(x) for x in hostname.split("."))

                if is_valid_hostname(longname):
                    nodename = longname.split('.')[0]
                else:
                    nodename = longname.replace('.', '_')

                for stat in stats:
                    name = 'couchbase_' + nodename + '_' + stat
                    value = float(stats_json['nodes'][x]['interestingStats'][stat])
                    jsondata.gen_data(name, timestamp, value, lib.pushdata.hostname, check_type, cluster_name)

            for bstat in basicstats:
                name = 'couchbase_clusterwide_' + bstat
                value = float(stats_json['basicStats'][bstat])
                jsondata.gen_data(name, timestamp, value, lib.pushdata.hostname, check_type, cluster_name)

            jsondata.put_json()
    except Exception as e:
        lib.pushdata.print_error(__name__ , (e))
        pass



