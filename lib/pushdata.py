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
import time
import uuid
import puylogger
#import zlib

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0] + '/conf/config.ini')
cluster_name = config.get('SelfConfig', 'cluster_name')
host_group = config.get('SelfConfig', 'host_group')
tsdb_type = config.get('TSDB', 'tsdtype')
hostname = socket.getfqdn()
c = pycurl.Curl()
record_rate.init()


if (tsdb_type == 'KairosDB' or tsdb_type == 'OpenTSDB'):
    tsdb_url = config.get('TSDB', 'address') + config.get('TSDB', 'datapoints')
    tsdb_auth = config.get('TSDB', 'user') + ':' + config.get('TSDB', 'pass')
    curl_auth = config.getboolean('TSDB', 'auth')
    tsd_rest = True
else:
    tsd_rest = False

if tsdb_type == 'Carbon':
    tsd_carbon = True
    carbon_server = config.get('TSDB', 'address')
    carbon_host = carbon_server.split(':')[0]
    carbon_port = int(carbon_server.split(':')[1])
    path = hostname.replace('.', '_')
else:
    tsd_carbon = False

if tsdb_type == 'InfluxDB':
    tsd_influx = True
    influx_server = config.get('TSDB', 'address')
    influx_db = config.get('TSDB', 'database')
    influx_url = influx_server + '/write?db=' + influx_db
    curl_auth = config.getboolean('TSDB', 'auth')
    influx_auth = config.get('TSDB', 'user') + ':' + config.get('TSDB', 'pass')
else:
    tsd_influx = False

if (tsdb_type == 'OddEye'):
    tsdb_url = config.get('TSDB', 'url')
    oddeye_uuid = config.get('TSDB', 'uuid')
    tsd_oddeye = True
    err_handler = int(config.get('TSDB', 'err_handler'))
    negative_handler = err_handler * -1
    sandbox = config.getboolean('TSDB', 'sandbox')
    if sandbox is True:
        barlus_style = 'UUID=' + oddeye_uuid + '&sandbox=true&data='
    else:
        barlus_style = 'UUID=' + oddeye_uuid + '&data='
else:
    tsd_oddeye = False


class JonSon(object):
    def gen_data(self, name, timestamp, value, tag_hostname, tag_type, cluster_name, reaction=0, metric_type='None'):
        if tsdb_type == 'KairosDB':
            self.data['metric'].append({"name": name, "timestamp": timestamp * 1000, "value": value, "tags": {"host": tag_hostname, "type": tag_type, "cluster": cluster_name, "group": host_group}})
        elif tsdb_type == 'OpenTSDB':
            self.data['metric'].append({"metric": name, "timestamp": timestamp, "value": value, "tags": {"host": tag_hostname, "type": tag_type, "cluster": cluster_name, "group": host_group}})
        elif tsdb_type == 'BlueFlood':
            raise NotImplementedError('BlueFlood is not supported yet')
        elif tsdb_type == 'Carbon':
            self.data.append((cluster_name + '.' + host_group + '.' + path + '.' + name, (timestamp, value)))
        elif tsdb_type == 'InfluxDB':
            nanotime = lambda: int(round(time.time() * 1000000000))
            str_nano = str(nanotime())
            if type(value) is int:
                value = str(value) + 'i'
            else:
                value = str(value)
            self.data.append(name + ',host=' + tag_hostname + ',cluster=' + cluster_name + ',group=' + host_group + ',type=' + tag_type + ' value=' + value + ' ' + str_nano + '\n')
        elif tsd_oddeye is True:
            self.data['metric'].append({"metric": name, "timestamp": timestamp, "value": value, "reaction": reaction, "type": metric_type, "tags": {"host": tag_hostname, "type": tag_type, "cluster": cluster_name, "group": host_group}})

        else:
            print 'Please set TSDB type'

    def prepare_data(self):
        if tsd_rest is True:
            try:
                self.data.__delitem__('metric')
                self.data = {'metric': []}
            except:
                self.data = {'metric': []}
        if tsd_carbon is True:
            try:
                self.data.__delitem__
            except:
                self.data = []
        if tsd_influx is True:
            try:
                self.data.__delitem__
            except:
                self.data = []
        if tsd_oddeye is True:
            try:
                self.data.__delitem__('metric')
                self.data = {'metric': []}
            except:
                self.data = {'metric': []}
    # ------------------------------------------- #

    def httt_set_opt(self,url, data):
        c.setopt(pycurl.URL, url)
        c.setopt(pycurl.POST, 0)
        c.setopt(pycurl.POSTFIELDS, data)
        c.setopt(pycurl.VERBOSE, 0)
        c.setopt(pycurl.TIMEOUT, 3)
        c.setopt(pycurl.NOSIGNAL, 5)
        c.setopt(pycurl.USERAGENT, 'PuyPuy v.02')
        c.setopt(pycurl.ENCODING, "gzip,deflate")
        c.setopt(pycurl.WRITEFUNCTION, lambda x: None)

    def upload_it(self, data):
        #timestamp=datetime.datetime.now().strftime("%s")
        http_response_codes = [100, 101, 102, 200, 201, 202, 203, 204, 205, 206, 207, 208, 226, 300, 301, 302, 303, 304, 305, 306, 307, 308]
        try:
            c.perform()
            try:
                response_code = int(c.getinfo(pycurl.RESPONSE_CODE))
                response_exists = True
            except:
                response_exists = False
                pass

            def start_cache(data):
                print_error(str(c.getinfo(pycurl.RESPONSE_CODE)) + ' Got non ubnormal response code, started to cache', '')
                tmpdir = config.get('SelfConfig', 'tmpdir')
                filename = tmpdir + '/' + str(uuid.uuid4()) + '.cached'
                file = open(filename, "w")
                file.write(data)
                file.close()

            if response_code not in http_response_codes and response_exists is True:
                start_cache(data)

        except Exception as e:
            print_error(__name__, (e))
            try:
                tmpdir = config.get('SelfConfig', 'tmpdir')
                filename = tmpdir + '/' + str(uuid.uuid4()) + '.cached'
                file = open(filename, "w")
                file.write(data)
                file.close()
            except:
                pass

    def put_json(self):
        if tsd_oddeye is True:
            json_data = json.dumps(self.data['metric'])
            send_data = barlus_style + json_data
            #zdata = zlib.compress(send_data)
            self.httt_set_opt(tsdb_url, send_data)
            self.upload_it(send_data)


        if tsd_rest is True:
            json_data = json.dumps(self.data['metric'])
            if curl_auth is True:
                c.setopt(pycurl.USERPWD, tsdb_auth)
            self.httt_set_opt(tsdb_url, json_data)
            self.upload_it(json_data)

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
            if curl_auth is True:
                c.setopt(pycurl.USERPWD, influx_auth)
            self.httt_set_opt(influx_url, line_data)
            self.upload_it(line_data)

# ------------------------------------------------------------------------------- #
    def send_special(self, module, timestamp, value, error_msg, mytype, reaction=0):
        try:
            #if tsd_oddeye is True and module is not 'lib.pushdata':
            if tsd_oddeye is True:
                error_data = []
                error_data.append({"metric": module, \
                                   "timestamp": timestamp, \
                                   "value": value, \
                                   "message": error_msg, \
                                   "type": "Special", \
                                   "status": mytype, \
                                   "reaction": reaction, \
                                   "tags": {"host": hostname,"cluster": cluster_name, "group": host_group}})
                send_err_msg = json.dumps(error_data)
                send_error_data = barlus_style + send_err_msg
                self.httt_set_opt(tsdb_url, send_error_data)
                self.upload_it(send_error_data)
                if puylogger.debug_log:
                    puylogger.print_message(send_error_data)
                    #logging.critical(" %s : " % module + str(module))
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
            #if tsd_oddeye is True and module is not 'lib.pushdqata':
            logging.critical(module)
            cluster_name = config.get('SelfConfig', 'cluster_name')
            error_msg = str(e).replace('[', '').replace(']', '').replace('<', '').replace('>', '').replace('(', '').replace(')', '').replace("'", '').replace('"', '')
            timestamp = int(datetime.datetime.now().strftime("%s"))
            error_data = []
            error_data.append({"metric": module,
                               "timestamp": timestamp,
                               "value": 16,
                               "message": error_msg,
                               "status": "ERROR",
                               "type": "Special",
                               "reaction": negative_handler,
                               "tags": {"host": hostname, "cluster": cluster_name, "group": host_group}})
            try:
                send_err_msg = json.dumps(str(error_data))
            except Exception as  dddd:
                logging.critical(" %s : " % str(dddd))
                pass

            if sandbox is True:
                barlus_style = 'UUID=' + oddeye_uuid + '&sandbox=true&data='
            else:
                barlus_style = 'UUID=' + oddeye_uuid + '&data='

            send_error_data = barlus_style + send_err_msg
            jonson=JonSon()
            jonson.httt_set_opt(tsdb_url, send_error_data)
            c.setopt(pycurl.POSTFIELDS, send_error_data)
            c.perform()
        else:
            logging.critical(" %s : " % module + str(e))
    try:
        if module == 'lib.pushdata':
            logging.critical(" %s : " % "Failed to connect to Barlus" + str(e))
            pass
        else:
            #logging.critical(" %s : " % "Cannot connect to Barlus" + str(e))
            send_error_msg()

    except Exception as err:
        logging.critical(" %s : " % "Cannot send error" + str(err))