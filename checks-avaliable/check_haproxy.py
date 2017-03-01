import lib.record_rate
import lib.pushdata
import pycurl
import os, sys
import ConfigParser
import datetime
import socket

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/webservers.ini')

hostname = socket.getfqdn()
haproxy_url = config.get('HAProxy', 'url')
haproxy_auth = config.get('HAProxy', 'user')+':'+config.get('HAProxy', 'pass')
curl_auth = config.getboolean('HAProxy', 'auth')
cluster_name = config.get('SelfConfig', 'cluster_name')

haproxy_upstream = config.get('HAProxy', 'upstream').split(',')

class buffer:
   def __init__(self):
       self.contents = ''

   def body_callback(self, buf):
       self.contents = self.contents + buf

def run_haproxy():
    try:
        t = buffer()
        c = pycurl.Curl()
        c.setopt(c.URL, haproxy_url)
        c.setopt(c.WRITEFUNCTION, t.body_callback)
        c.setopt(c.FAILONERROR, True)
        c.setopt(pycurl.CONNECTTIMEOUT, 10)
        c.setopt(pycurl.TIMEOUT, 10)
        c.setopt(pycurl.NOSIGNAL, 5)
        if curl_auth is True:
            c.setopt(pycurl.USERPWD, haproxy_auth)
        c.perform()
        c.close()

        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
        jsondata=lib.pushdata.JonSon()
        jsondata.prepare_data()
        check_type = 'haproxy'
        lazy_totals=("FRONTEND", "BACKEND")
        timestamp = int(datetime.datetime.now().strftime("%s"))
        for line in t.contents.split('\n'):
            for application in haproxy_upstream:
                if application in line:
                    if not any(s in line for s in lazy_totals):
                        upstream=line.split(',')[1]
                        sessions=line.split(',')[4]
                        connrate=line.split(',')[33]
                        jsondata.gen_data('haproxy_connrate_'+upstream, timestamp, connrate, lib.pushdata.hostname, check_type, cluster_name)
                        jsondata.gen_data('haproxy_sessions_'+upstream, timestamp, sessions, lib.pushdata.hostname, check_type, cluster_name)
        jsondata.put_json()
    except Exception as e:
        lib.pushdata.print_error(__name__ , (e))
        pass


