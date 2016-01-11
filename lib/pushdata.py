import pycurl
import json
import os
import ConfigParser
import datetime
import socket
import logging
import pickle
import struct

import record_rate
record_rate.init()

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')


hostname = socket.getfqdn()


tsdb_type= config.get('TSDB', 'tsdtype')


if (tsdb_type == 'KairosDB' or tsdb_type == 'OpenTSDB'):
    tsdb_url = config.get('TSDB', 'address') + config.get('TSDB', 'datapoints')
    tsdb_auth = config.get('TSDB', 'user')+':'+config.get('TSDB', 'pass')
    host_group= config.get('SelfConfig', 'host_group')
    curl_auth = config.getboolean('TSDB', 'auth')
    tsd_rest = True
else:
    tsd_rest = False

if tsdb_type == 'Carbon':
    tsd_carbon = True
    carbon_server = config.get('TSDB', 'address')
    carbon_host=carbon_server.split(':')[0]
    carbon_port=int(carbon_server.split(':')[1])
    host_group= config.get('SelfConfig', 'host_group')
    #hostname = hostname.split('.')
    #hostname.reverse()
    #path=".".join(hostname)
    path=hostname.replace('.' , '_')
else:
    tsd_carbon = False


class JonSon(object):
    def gen_data(self, name,timestamp, value, tag_hostname, tag_type, cluster_name):
        if tsdb_type == 'KairosDB':
            self.data['metric'].append({"name":name,"timestamp":timestamp*1000, "value":value, "tags":{"host":tag_hostname,"type":tag_type, "cluster":cluster_name, "group":host_group} })
        elif tsdb_type == 'OpenTSDB':
            self.data['metric'].append({"metric":name,"timestamp":timestamp, "value":value, "tags":{"host":tag_hostname,"type":tag_type, "cluster":cluster_name, "group":host_group} })
        elif tsdb_type == 'BlueFlood':
            print 'BlueFlood is not supported yet'
        elif tsdb_type == 'Carbon':
            self.data.append((cluster_name+'.'+host_group+'.'+path+'.'+name, (timestamp, value)))
        else:
            print 'Please set TSDB type'

    def create_data(self):
        if tsd_rest is True:
            self.data = {'metric': []}
        if tsd_carbon is True:
            self.data = []

    def truncate_data(self):
        if tsd_rest is True:
            self.data.__delitem__('metric')
            self.data = {'metric': []}
        if tsd_carbon is True:
            self.data.__delitem__

    def put_json(self):
        if tsd_rest is True:
            json_data = json.dumps(self.data['metric'])
            c = pycurl.Curl()
            if curl_auth is True:
                c.setopt(pycurl.USERPWD, tsdb_auth)
            c.setopt(pycurl.URL, tsdb_url)
            c.setopt(pycurl.POST, 0)
            c.setopt(pycurl.POSTFIELDS, json_data)
            c.setopt(pycurl.VERBOSE, 0)
            c.setopt(pycurl.TIMEOUT, 10)
            c.setopt(pycurl.NOSIGNAL, 5)
            c.perform()
            c.close()
            #print len(json_data)
            #print " \n "
            #print json_data
        if tsd_carbon is True:
            payload = pickle.dumps(self.data, protocol=2)
            header = struct.pack("!L", len(payload))
            message = header + payload
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((carbon_host, carbon_port))
            s.send(message)
            s.close()
            #print message



def print_error(e):
    log_file = config.get('SelfConfig', 'log_file')
    logging.basicConfig(filename=log_file, level=logging.DEBUG)
    logger = logging.getLogger("TSD Client")
    logger.setLevel(logging.DEBUG)
    logging.critical(" %s : " % str(e) + os.path.realpath(__file__))
