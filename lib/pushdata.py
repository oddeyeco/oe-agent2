import pycurl
import json
import os
import datetime
import socket
import logging
import pickle
import struct
import time
import uuid
import lib.puylogger
import lib.getconfig
import cStringIO

cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
host_group = lib.getconfig.getparam('SelfConfig', 'host_group')
maxcache = int(lib.getconfig.getparam('SelfConfig', 'max_cache'))
tsdb_type = lib.getconfig.getparam('TSDB', 'tsdtype')
tmpdir = lib.getconfig.getparam('SelfConfig', 'tmpdir')
log_file = lib.getconfig.getparam('SelfConfig', 'log_file')

hostname = socket.getfqdn()
c = pycurl.Curl()
global pycurl_response

if (tsdb_type == 'KairosDB' or tsdb_type == 'OpenTSDB'):
    tsdb_url = lib.getconfig.getparam('TSDB', 'address') + lib.getconfig.getparam('TSDB', 'datapoints')
    tsdb_auth = lib.getconfig.getparam('TSDB', 'user') + ':' + lib.getconfig.getparam('TSDB', 'pass')
    curl_auth = bool(lib.getconfig.getparam('TSDB', 'auth'))
    tsd_rest = True
else:
    tsd_rest = False

if tsdb_type == 'Carbon':
    tsd_carbon = True
    carbon_server = lib.getconfig.getparam('TSDB', 'address')
    carbon_host = carbon_server.split(':')[0]
    carbon_port = int(carbon_server.split(':')[1])
    path = hostname.replace('.', '_')
else:
    tsd_carbon = False

if tsdb_type == 'InfluxDB':
    tsd_influx = True
    influx_server = lib.getconfig.getparam('TSDB', 'address')
    influx_db = lib.getconfig.getparam('TSDB', 'database')
    influx_url = influx_server + '/write?db=' + influx_db
    curl_auth = bool(lib.getconfig.getparam('TSDB', 'auth'))
    influx_auth = lib.getconfig.getparam('TSDB', 'user') + ':' + lib.getconfig.getparam('TSDB', 'pass')
else:
    tsd_influx = False

if (tsdb_type == 'OddEye'):
    tsdb_url = lib.getconfig.getparam('TSDB', 'url')
    oddeye_uuid = lib.getconfig.getparam('TSDB', 'uuid')
    tsd_oddeye = True
    err_handler = int(lib.getconfig.getparam('TSDB', 'err_handler'))
    negative_handler = err_handler * -1
    sandbox = bool(lib.getconfig.getparam('TSDB', 'sandbox'))
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
                self.data = {'metric': []}
            except:
                lib.puylogger.print_message('Recreating data in except block')
                self.data = {'metric': []}
        if tsd_carbon is True:
            try:
                self.data = []
            except:
                lib.puylogger.print_message('Recreating data in except block')
                self.data = []
        if tsd_influx is True:
            try:
                self.data = []
            except:
                lib.puylogger.print_message('Recreating data in except block')
                self.data = []
        if tsd_oddeye is True:
            try:
                self.data = {'metric': []}
            except:
                lib.puylogger.print_message('Recreating data in except block')
                self.data = {'metric': []}

    def httt_set_opt(self,url, data):
        pycurl_response = cStringIO.StringIO()
        c.setopt(pycurl.URL, url)
        c.setopt(pycurl.POST, 0)
        c.setopt(pycurl.POSTFIELDS, data)
        c.setopt(pycurl.VERBOSE, 0)
        c.setopt(pycurl.TIMEOUT, 3)
        c.setopt(pycurl.NOSIGNAL, 5)
        c.setopt(pycurl.USERAGENT, 'PuyPuy v.02')
        c.setopt(pycurl.ENCODING, "gzip,deflate")
        if tsd_oddeye is True:
            c.setopt(pycurl.WRITEFUNCTION, pycurl_response.write)
        else:
            c.setopt(pycurl.WRITEFUNCTION, lambda x: None)


    def upload_it(self, data):
        http_response_codes = [100, 101, 102, 200, 201, 202, 203, 204, 205, 206, 207, 208, 226, 300, 301, 302, 303, 304, 305, 306, 307, 308]
        http_oddeye_errors = [406, 411, 415, 424]
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
                if len(os.listdir(tmpdir)) > maxcache:
                    logging.critical('Too many cached files')
                else:
                    filename = tmpdir + '/' + str(uuid.uuid4()) + '.cached'
                    file = open(filename, "w")
                    file.write(data)
                    file.close()

            if response_code not in http_response_codes and response_exists is True:
                if response_code in http_oddeye_errors:
                    logging.critical(" %s : " % "OddEye Error" + str(response_code) + pycurl_response.getvalue().replace('\n',''))
                else:
                    start_cache(data)

        except Exception as e:
            print_error(__name__, (e))
            try:
                if len(os.listdir(tmpdir)) > maxcache:
                    logging.critical('Too many cached files')
                else:
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
            self.httt_set_opt(tsdb_url, send_data)
            self.upload_it(send_data)
            if lib.puylogger.debug_log:
                lib.puylogger.print_message('\n' + send_data)
            del self.data
            self.data = None
            del send_data
            del json_data


        if tsd_rest is True:
            json_data = json.dumps(self.data['metric'])
            if curl_auth is True:
                c.setopt(pycurl.USERPWD, tsdb_auth)
            self.httt_set_opt(tsdb_url, json_data)
            self.upload_it(json_data)
            if lib.puylogger.debug_log:
                lib.puylogger.print_message('\n' + json_data)


        if tsd_carbon is True:
            payload = pickle.dumps(self.data, protocol=2)
            header = struct.pack("!L", len(payload))
            message = header + payload
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((carbon_host, carbon_port))
            s.send(message)
            s.close()
            if lib.puylogger.debug_log:
                lib.puylogger.print_message('\n' + message)

        if tsd_influx is True:
            line_data = '%s' % ''.join(map(str, self.data))
            if curl_auth is True:
                c.setopt(pycurl.USERPWD, influx_auth)
            self.httt_set_opt(influx_url, line_data)
            self.upload_it(line_data)
            if lib.puylogger.debug_log:
                lib.puylogger.print_message('\n' + line_data)

    def send_special(self, module, timestamp, value, error_msg, mytype, reaction=0):
        try:
            if tsd_oddeye is True:
                error_data = []
                error_data.append({"metric": module,
                                   "timestamp": timestamp,
                                   "value": value,
                                   "message": error_msg,
                                   "type": "Special",
                                   "status": mytype,
                                   "reaction": reaction,
                                   "tags": {"host": hostname,"cluster": cluster_name, "group": host_group}})
                send_err_msg = json.dumps(error_data)
                send_error_data = barlus_style + send_err_msg
                self.httt_set_opt(tsdb_url, send_error_data)
                self.upload_it(send_error_data)
                if lib.puylogger.debug_log:
                    lib.puylogger.print_message(send_error_data)
                del error_data
                del send_err_msg
        except:
                logging.critical(" %s : " % module + str(send_err_msg))


def print_error(module, e):
    logging.basicConfig(filename=log_file, level=logging.DEBUG)
    logger = logging.getLogger("PuyPuy")
    logger.setLevel(logging.DEBUG)
    def send_error_msg():
        if tsd_oddeye is True:
            logging.critical(module)
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
            if lib.puylogger.debug_log:
                lib.puylogger.print_message(str(error_data))
            try:
                send_err_msg = json.dumps(error_data)
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
            del error_msg
            del error_data
            del send_error_data
        else:
            logging.critical(" %s : " % module + str(e))
    try:
        if module == 'lib.pushdata':
            logging.critical(" %s : " % "Failed to connect to Barlus" + str(e))
            pass
        else:
            send_error_msg()

    except Exception as err:
        logging.critical(" %s : " % "Cannot send error" + str(err))