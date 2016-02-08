import pycurl
import os, sys
import ConfigParser
import datetime
import socket

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')

haproxy_url = config.get('HAProxy', 'url')

hostname = socket.getfqdn()

haproxy_auth = config.get('HAProxy', 'user')+':'+config.get('HAProxy', 'pass')
haproxy_upstream = config.get('HAProxy', 'upstream')
curl_auth = config.getboolean('HAProxy', 'auth')
cluster_name = config.get('SelfConfig', 'cluster_name')


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
        push = __import__('pushdata')
        jsondata=push.JonSon()
        jsondata.create_data()
        check_type = 'haproxy'
        lazy_totals=("FRONTEND", "BACKEND")
        timestamp = int(datetime.datetime.now().strftime("%s"))
        for line in t.contents.split('\n'):
            if haproxy_upstream in line:
                if not any(s in line for s in lazy_totals):
                    upstream=line.split(',')[1]
                    sessions=line.split(',')[4]
                    connrate=line.split(',')[33]
                    jsondata.gen_data('haproxy_connrate_'+upstream, timestamp, connrate, push.hostname, check_type, cluster_name)
                    jsondata.gen_data('haproxy_sessions_'+upstream, timestamp, sessions, push.hostname, check_type, cluster_name)
        jsondata.put_json()
        jsondata.truncate_data()
    except Exception as e:
        push = __import__('pushdata')
        push.print_error(__name__ , (e))
        pass


