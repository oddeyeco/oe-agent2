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

phpfpm_url = config.get('PhpFPM', 'address') + config.get('PhpFPM', 'stats')

hostname = socket.getfqdn()

phpfpm_auth = config.get('PhpFPM', 'user')+':'+config.get('PhpFPM', 'pass')
curl_auth = config.getboolean('PhpFPM', 'auth')
cluster_name = config.get('SelfConfig', 'cluster_name')
check_type = 'php-fpm'

class buffer:
   def __init__(self):
       self.contents = ''
   def body_callback(self, buf):
       self.contents = self.contents + buf


def run_phpfpm():
    try:
        t = buffer()
        c = pycurl.Curl()
        c.setopt(c.URL, phpfpm_url)
        c.setopt(c.WRITEFUNCTION, t.body_callback)
        c.setopt(c.FAILONERROR, True)
        c.setopt(pycurl.CONNECTTIMEOUT, 5)
        c.setopt(pycurl.TIMEOUT, 5)
        c.setopt(pycurl.NOSIGNAL, 2)
        if curl_auth is True:
            c.setopt(pycurl.USERPWD, phpfpm_auth)
        c.perform()
        c.close()
        #uptime=t.contents.splitlines()[3].split(':')[1].replace(" ", "")
        connections=t.contents.splitlines()[4].split(':')[1].replace(" ", "")

        proc_idle=t.contents.splitlines()[8].split(':')[1].replace(" ", "")
        proc_active=t.contents.splitlines()[9].split(':')[1].replace(" ", "")
        proc_total=t.contents.splitlines()[10].split(':')[1].replace(" ", "")
        max_active=t.contents.splitlines()[11].split(':')[1].replace(" ", "")
        max_children=t.contents.splitlines()[12].split(':')[1].replace(" ", "")
        slow_request=t.contents.splitlines()[13].split(':')[1].replace(" ", "")
        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
        jsondata=lib.pushdata.JonSon()
        jsondata.prepare_data()
        rate=lib.record_rate.ValueRate()
        timestamp = int(datetime.datetime.now().strftime("%s"))
        conns_per_sec=rate.record_value_rate('phpfpm_connections', connections, timestamp)
        jsondata.gen_data('phpfpm_conns_per_sec', timestamp, conns_per_sec, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')
        jsondata.gen_data('phpfpm_proc_idle', timestamp, proc_idle, lib.pushdata.hostname, check_type, cluster_name)
        jsondata.gen_data('phpfpm_proc_active', timestamp, proc_active, lib.pushdata.hostname, check_type, cluster_name)
        jsondata.gen_data('phpfpm_proc_total', timestamp, proc_total, lib.pushdata.hostname, check_type, cluster_name)
        jsondata.gen_data('phpfpm_max_active', timestamp, max_active, lib.pushdata.hostname, check_type, cluster_name)
        jsondata.gen_data('phpfpm_max_children', timestamp, max_children, lib.pushdata.hostname, check_type, cluster_name)
        jsondata.gen_data('phpfpm_slow_request', timestamp, slow_request, lib.pushdata.hostname, check_type, cluster_name)
        jsondata.put_json()
    except Exception as e:
        lib.pushdata.print_error(__name__ , (e))
        pass


