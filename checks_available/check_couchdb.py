import lib.record_rate
import lib.pushdata
import urllib2
import os, sys
import ConfigParser
import datetime
import socket
import json
import lib.puylogger
import lib.record_rate


config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/bigdata.ini')


couchdb_url = config.get('CouchDB', 'stats')

hostname = socket.getfqdn()
cluster_name = config.get('SelfConfig', 'cluster_name')
check_type = 'couchdb'

timestamp = int(datetime.datetime.now().strftime("%s"))

def runcheck():
    try:
        stats = urllib2.urlopen(couchdb_url, timeout=5).read()
        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
        stats_json = json.loads(stats)

        jsondata = lib.pushdata.JonSon()
        jsondata.prepare_data()
        rate = lib.record_rate.ValueRate()
        timestamp = int(datetime.datetime.now().strftime("%s"))

        sections = ('couchdb', 'httpd_request_methods', 'httpd_status_codes', 'httpd')
        couchdb_stats = ('auth_cache_misses', 'database_writes', 'open_databases', 'auth_cache_hits', 'request_time', 'database_reads', 'open_os_files')
        httpd_methods = ('GET', 'PUT', 'COPY', 'DELETE', 'POST', 'HEAD')
        httpd_codes = ('200', '201', '202', '301', '304', '400', '401', '403', '404', '405', '409', '412', '500')
        httpd_stats = ('clients_requesting_changes', 'temporary_view_reads', 'requests', 'bulk_requests', 'view_reads')

        for cs in couchdb_stats:
            if stats_json[sections[0]][cs]['current'] is not None:
                csvalue= stats_json[sections[0]][cs]['current']
                csrate = rate.record_value_rate('couch_'+cs, csvalue, timestamp)
                jsondata.gen_data('couchdb_' + cs, timestamp, csrate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')

        for hm in httpd_methods:
            if stats_json[sections[1]][hm]['current'] is not None:
                hmrate = rate.record_value_rate('couch_' + hm, stats_json[sections[1]][hm]['current'], timestamp)
                jsondata.gen_data('couchdb_' + hm.lower(), timestamp, hmrate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')

        for hc in httpd_codes:
            hc=str(hc)
            if stats_json[sections[2]][hc]['current'] is not None:
                hcrate = rate.record_value_rate('couch_' + hc, stats_json[sections[2]][hc]['current'], timestamp)
                jsondata.gen_data('couchdb_code' + hc, timestamp, hcrate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')

        for hs in httpd_stats:
            if stats_json[sections[3]][hs]['current'] is not None:
                hsrate = rate.record_value_rate('couch_' + hs, stats_json[sections[3]][hs]['current'], timestamp)
                jsondata.gen_data('couchdb_' + hs, timestamp, hsrate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')

        jsondata.put_json()
    except Exception as e:
        lib.pushdata.print_error(__name__, (e))
        pass



