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
#import zlib


record_rate.init()

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0] + '/conf/config.ini')
cluster_name = config.get('SelfConfig', 'cluster_name')
hostname = socket.getfqdn()


tsdb_type = config.get('TSDB', 'tsdtype')

c = pycurl.Curl()

if (tsdb_type == 'KairosDB' or tsdb_type == 'OpenTSDB'):
    tsdb_url = config.get('TSDB', 'address') + config.get('TSDB', 'datapoints')
    tsdb_auth = config.get('TSDB', 'user') + ':' + config.get('TSDB', 'pass')
    host_group = config.get('SelfConfig', 'host_group')
    curl_auth = config.getboolean('TSDB', 'auth')
    tsd_rest = True
else:
    tsd_rest = False

if tsdb_type == 'Carbon':
    tsd_carbon = True
    carbon_server = config.get('TSDB', 'address')
    carbon_host = carbon_server.split(':')[0]
    carbon_port = int(carbon_server.split(':')[1])
    host_group = config.get('SelfConfig', 'host_group')
    path = hostname.replace('.', '_')
else:
    tsd_carbon = False

if tsdb_type == 'InfluxDB':
    tsd_influx = True
    influx_server = config.get('TSDB', 'address')
    influx_db = config.get('TSDB', 'database')
    influx_url = influx_server + '/write?db=' + influx_db
    host_group = config.get('SelfConfig', 'host_group')
    curl_auth = config.getboolean('TSDB', 'auth')
    influx_auth = config.get('TSDB', 'user') + ':' + config.get('TSDB', 'pass')
else:
    tsd_influx = False

if (tsdb_type == 'OddEye'):
    tsdb_url = config.get('TSDB', 'url')
    host_group = config.get('SelfConfig', 'host_group')
    oddeye_uuid = config.get('TSDB', 'uuid')
    tsd_oddeye = True
else:
    tsd_oddeye = False


class JonSon(object):

    def gen_data(self, name, timestamp, value, tag_hostname, tag_type, cluster_name, reaction=0):
        if tsdb_type == 'KairosDB':
            self.data['metric'].append({"name": name, "timestamp": timestamp * 1000, "value": value, "tags": {"host": tag_hostname, "type": tag_type, "cluster": cluster_name, "group": host_group}})
        elif tsdb_type == 'OpenTSDB':
            self.data['metric'].append({"metric": name, "timestamp": timestamp, "value": value, "tags": {"host": tag_hostname, "type": tag_type, "cluster": cluster_name, "group": host_group}})
        elif tsdb_type == 'BlueFlood':
            print 'BlueFlood is not supported yet'
        elif tsdb_type == 'Carbon':
            self.data.append((cluster_name + '.' + host_group + '.' + path + '.' + name, (timestamp, value)))
        elif tsdb_type == 'InfluxDB':
            import time
            nanotime = lambda: int(round(time.time() * 1000000000))
            str_nano = str(nanotime())
            if type(value) is int:
                value = str(value) + 'i'
            else:
                value = str(value)
            self.data.append(name + ',host=' + tag_hostname + ',cluster=' + cluster_name + ',group=' + host_group + ',type=' + tag_type + ' value=' + value + ' ' + str_nano + '\n')
        elif tsd_oddeye is True:
            self.data['metric'].append({"metric": name, "timestamp": timestamp, "value": value, "tags": {"host": tag_hostname, "type": tag_type, "cluster": cluster_name, "group": host_group, "reaction": reaction}})

        else:
            print 'Please set TSDB type'

    def create_data(self):
        if tsd_rest is True:
            self.data = {'metric': []}
        if tsd_carbon is True:
            self.data = []
        if tsd_influx is True:
            self.data = []
        if tsd_oddeye is True:
            self.data = {'metric': []}
            # self.metrics = {}

    def truncate_data(self):
        if tsd_rest is True:
            self.data.__delitem__('metric')
            self.data = {'metric': []}
        if tsd_carbon is True:
            self.data.__delitem__
        if tsd_influx is True:
            self.data.__delitem__
        if tsd_oddeye is True:
            self.data.__delitem__('metric')
            self.data = {'metric': []}
            # self.data.__delitem__
            # self.metrics.clear()

    def put_json(self):
        http_response_codes = [100, 101, 102, 200, 201, 202, 203, 204, 205, 206, 207, 208, 226, 300, 301, 302, 303, 304, 305, 306, 307, 308]

        def upload_data(data):
            try:
                c.perform()
                try:
                    response_code = int(c.getinfo(pycurl.RESPONSE_CODE))
                    response_exists = True
                except:
                    response_exists = False
                    pass

                def start_cache(data):
                    push = __import__('pushdata')
                    push.print_error(c.getinfo(pycurl.RESPONSE_CODE), 'Got non ubnormal response code, started to cache')
                    import uuid
                    tmpdir = config.get('SelfConfig', 'tmpdir')
                    filename = tmpdir + '/' + str(uuid.uuid4()) + '.cached'
                    file = open(filename, "w")
                    file.write(data)
                    file.close()

                if response_code not in http_response_codes and response_exists is True:
                    start_cache(data)

            except Exception as e:
                push = __import__('pushdata')
                push.print_error(__name__, (e))
                try:
                    import uuid
                    tmpdir = config.get('SelfConfig', 'tmpdir')
                    filename = tmpdir + '/' + str(uuid.uuid4()) + '.cached'
                    file = open(filename, "w")
                    file.write(data)
                    file.close()
                except:
                    pass

        if tsd_oddeye is True:
            json_data = json.dumps(self.data['metric'])
            c.setopt(pycurl.URL, tsdb_url)
            c.setopt(pycurl.POST, 0)
            barlus_style = 'UUID=' + oddeye_uuid + '&data='
            send_data = barlus_style + json_data
            c.setopt(pycurl.POSTFIELDS, send_data)
            c.setopt(pycurl.VERBOSE, 0)
            c.setopt(pycurl.TIMEOUT, 3)
            c.setopt(pycurl.NOSIGNAL, 5)
            c.setopt(pycurl.USERAGENT, 'PuyPuy v.01')
            c.setopt(pycurl.ENCODING, "gzip,deflate")
            c.setopt(pycurl.WRITEFUNCTION, lambda x: None)
            #zdata = zlib.compress(send_data)
            #upload_data(zdata)
            upload_data(send_data)

        if tsd_rest is True:
            json_data = json.dumps(self.data['metric'])
            if curl_auth is True:
                c.setopt(pycurl.USERPWD, tsdb_auth)
            c.setopt(pycurl.URL, tsdb_url)
            c.setopt(pycurl.POST, 0)
            c.setopt(pycurl.POSTFIELDS, json_data)
            c.setopt(pycurl.VERBOSE, 0)
            c.setopt(pycurl.TIMEOUT, 10)
            c.setopt(pycurl.NOSIGNAL, 5)
            # c.perform()
            upload_data(json_data)

        if tsd_carbon is True:
            payload = pickle.dumps(self.data, protocol=2)
            header = struct.pack("!L", len(payload))
            message = header + payload
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((carbon_host, carbon_port))
            s.send(message)
            s.close()
        if tsd_influx is True:
            line_data = '%s' % ''.join(map(str, self.data))
            #print_error(self, line_data)
            if curl_auth is True:
                c.setopt(pycurl.USERPWD, influx_auth)
            c.setopt(pycurl.URL, influx_url)
            c.setopt(pycurl.POST, 0)
            c.setopt(pycurl.POSTFIELDS, line_data)
            c.setopt(pycurl.VERBOSE, 0)
            c.setopt(pycurl.TIMEOUT, 10)
            c.setopt(pycurl.NOSIGNAL, 5)
            # c.perform()
            upload_data(line_data)

# ------------------------------------------------------------------------------- #
    def send_special(self, module, timestamp, value, error_msg, mytype):
        try:
            if tsd_oddeye is True:
                error_data = []
                error_data.append({"metric": module, \
                                   "timestamp": timestamp, \
                                   "value": value, \
                                   "specialTag": 'true', \
                                   "message": error_msg, \
                                   "type": mytype, \
                                   "tags": {"host": hostname,'type' : 'SPECIAL', "cluster": cluster_name, "group": host_group}})
                send_err_msg = json.dumps(error_data)
                c.setopt(pycurl.URL, tsdb_url)
                c.setopt(pycurl.POST, 0)
                barlus_style = 'UUID=' + oddeye_uuid + '&data='
                send_error_data = barlus_style + send_err_msg
                c.setopt(pycurl.POSTFIELDS, send_error_data)
                c.setopt(pycurl.VERBOSE, 0)
                c.setopt(pycurl.TIMEOUT, 3)
                c.setopt(pycurl.NOSIGNAL, 5)
                c.setopt(pycurl.USERAGENT, 'PuyPuy v.0.2')
                c.setopt(pycurl.ENCODING, "gzip,deflate")
                c.setopt(pycurl.WRITEFUNCTION, lambda x: None)
                c.perform()
                #logging.critical(" %s : " % module + str(send_err_msg))
        except:
                logging.critical(" %s : " % module + str(send_err_msg))
# ------------------------------------------------------------------------------- #

def print_error(module, e):
    log_file = config.get('SelfConfig', 'log_file')
    logging.basicConfig(filename=log_file, level=logging.DEBUG)
    logger = logging.getLogger("PuyPuy")
    logger.setLevel(logging.DEBUG)
    def send_error_msg():
        if tsd_oddeye is True:
            cluster_name = config.get('SelfConfig', 'cluster_name')
            type = 'SPECIAL'
            #import re
            error_msg = str(e).replace('[', '').replace(']', '').replace('<', '').replace('>', '').replace('(', '').replace(')', '').replace("'", '').replace('"', '')
            #codes = int(filter(str.isdigit, error_msg))

            timestamp = int(datetime.datetime.now().strftime("%s"))
            error_data = []
            error_data.append({"metric": module, \
                               "timestamp": timestamp, \
                               "value": 16, \
                               "specialTag": 'true', \
                               "message": error_msg, \
                               "type": "ERROR", \
                               "tags": {"host": hostname, "type": type, "cluster": cluster_name, "group": host_group}})
            send_err_msg = json.dumps(error_data)
            c.setopt(pycurl.URL, tsdb_url)
            c.setopt(pycurl.POST, 0)
            barlus_style = 'UUID=' + oddeye_uuid + '&data='
            send_error_data = barlus_style + send_err_msg
            c.setopt(pycurl.POSTFIELDS, send_error_data)
            c.setopt(pycurl.VERBOSE, 0)
            c.setopt(pycurl.TIMEOUT, 3)
            c.setopt(pycurl.NOSIGNAL, 5)
            c.setopt(pycurl.USERAGENT, 'PuyPuy v.0.2')
            c.setopt(pycurl.ENCODING, "gzip,deflate")
            c.setopt(pycurl.WRITEFUNCTION, lambda x: None)
            c.perform()
            logging.critical(" %s : " % module + str(e))
        else:
            logging.critical(" %s : " % module + str(e))
            #logging.critical(" status code: %s : " % str(c.getinfo(pycurl.HTTP_CODE))+ str(error_data))
    try:
        if module == 'pushdata':
            logging.critical(" %s : " % "Cannot connect to Barlus" + str(e))
            pass
        else:
            send_error_msg()
    except Exception as err:
        logging.critical(" %s : " % "Cannot send error" + str(err))
