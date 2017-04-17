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

nginx_url = config.get('NginX', 'address') + config.get('NginX', 'stats')

hostname = socket.getfqdn()

nginx_auth = config.get('NginX', 'user')+':'+config.get('NginX', 'pass')
curl_auth = config.getboolean('NginX', 'auth')
cluster_name = config.get('SelfConfig', 'cluster_name')


class buffer:
   def __init__(self):
       self.contents = ''

   def body_callback(self, buf):
       self.contents = self.contents + buf


def runcheck():
    try:
        t = buffer()
        c = pycurl.Curl()
        c.setopt(c.URL, nginx_url)
        c.setopt(c.WRITEFUNCTION, t.body_callback)
        c.setopt(c.FAILONERROR, True)
        c.setopt(pycurl.CONNECTTIMEOUT, 10)
        c.setopt(pycurl.TIMEOUT, 10)
        c.setopt(pycurl.NOSIGNAL, 5)
        if curl_auth is True:
            c.setopt(pycurl.USERPWD, nginx_auth)
        c.perform()
        c.close()

        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
        jsondata=lib.pushdata.JonSon()
        jsondata.prepare_data()
        rate=lib.record_rate.ValueRate()
        check_type = 'nginx'

        timestamp = int(datetime.datetime.now().strftime("%s"))
        connections=t.contents.splitlines()[0].split(' ')[2]
        requests=t.contents.splitlines()[2].split(' ')[3]
        handled=t.contents.splitlines()[2].split(' ')[2]
        accept=t.contents.splitlines()[2].split(' ')[1]
        reading=t.contents.splitlines()[3].split(' ')[1]
        writing=t.contents.splitlines()[3].split(' ')[3]
        waiting=t.contents.splitlines()[3].split(' ')[5]

        reqrate=rate.record_value_rate('nginx_requests', requests, timestamp)
        handelerate=rate.record_value_rate('nginx_handled', handled, timestamp)
        acceptrate=rate.record_value_rate('nginx_accept', accept, timestamp)

        jsondata.gen_data('nginx_connections', timestamp, connections, lib.pushdata.hostname, check_type, cluster_name)
        jsondata.gen_data('nginx_requests', timestamp, reqrate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')
        jsondata.gen_data('nginx_handled', timestamp, handelerate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')
        jsondata.gen_data('nginx_accept', timestamp, acceptrate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')
        jsondata.gen_data('nginx_reading', timestamp, reading, lib.pushdata.hostname, check_type, cluster_name)
        jsondata.gen_data('nginx_writing', timestamp, writing, lib.pushdata.hostname, check_type, cluster_name)
        jsondata.gen_data('nginx_waiting', timestamp, waiting, lib.pushdata.hostname, check_type, cluster_name)

        jsondata.put_json()
    except Exception as e:
        lib.pushdata.print_error(__name__ , (e))
        pass

