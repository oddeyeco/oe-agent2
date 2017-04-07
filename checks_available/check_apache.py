import pycurl
import os, sys
import ConfigParser
import datetime
import socket
import lib.pushdata
import lib.record_rate


config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/webservers.ini')

apache_url = config.get('Apache', 'url')

hostname = socket.getfqdn()

apache_auth = config.get('Apache', 'user')+':'+config.get('Apache', 'pass')
curl_auth = config.getboolean('Apache', 'auth')
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
        c.setopt(c.URL, apache_url)
        c.setopt(c.WRITEFUNCTION, t.body_callback)
        c.setopt(c.FAILONERROR, True)
        c.setopt(pycurl.CONNECTTIMEOUT, 10)
        c.setopt(pycurl.TIMEOUT, 10)
        c.setopt(pycurl.NOSIGNAL, 5)
        if curl_auth is True:
            c.setopt(pycurl.USERPWD, apache_auth)
        c.perform()
        c.close()

        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
        jsondata=lib.pushdata.JonSon()
        jsondata.prepare_data()
        rate=lib.record_rate.ValueRate()
        check_type = 'apache'
        metrics_rated=('Total Accesses', 'Total kBytes')
        metrics_stuck=('ReqPerSec', 'BytesPerSec', 'BytesPerReq', 'BusyWorkers', 'IdleWorkers')
        timestamp = int(datetime.datetime.now().strftime("%s"))
        for line in t.contents.split('\n'):
            for searchitem in  metrics_stuck:
                if searchitem in line:
                    key=line.split(' ')[0].replace(':', '')
                    value=line.split(' ')[1]
                    jsondata.gen_data('apache_'+key, timestamp, value, lib.pushdata.hostname, check_type, cluster_name)
            for searchitem in  metrics_rated:
                reaction = 0
                metr_type='Rate'
                if searchitem in line:
                    key=line.split(' ')[0]+line.split(' ')[1].replace(':', '')
                    value=line.split(' ')[2]
                    value_rate=rate.record_value_rate(key, value, timestamp)
                    jsondata.gen_data('apache_'+key, timestamp, value_rate, lib.pushdata.hostname, check_type, cluster_name, reaction, metr_type)

        jsondata.put_json()
    except Exception as e:
        lib.pushdata.print_error(__name__ , (e))
        pass


