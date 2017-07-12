# import os
# import ConfigParser
import logging
import time
import lib.getconfig
# import datetime
# import json
# import pushdata

# config = ConfigParser.RawConfigParser()
# config.read(os.path.split(os.path.dirname(__file__))[0] + '/conf/config.ini')
# tsdb_url = config.get('TSDB', 'url')
#c = pycurl.Curl()

cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
host_group = lib.getconfig.getparam('SelfConfig', 'host_group')
debug_log = lib.getconfig.getparam('SelfConfig', 'debug_log')
tsdb_type = lib.getconfig.getparam('TSDB', 'tsdtype')
log_file = lib.getconfig.getparam('SelfConfig', 'log_file')

def print_message(message):
    logger = logging.getLogger("PuyPuy")
    logger.setLevel(logging.INFO)
    logging.basicConfig(filename=log_file, level=logging.INFO)
    logging.info(str(time.strftime(" [%F %H %M:%S] ")) + message)

# def print_error(module, e):
#     def send_error_msg():
#         if pushdata.tsd_oddeye is True:
#             cluster_name = config.get('SelfConfig', 'cluster_name')
#             error_msg = str(e).replace('[', '').replace(']', '').replace('<', '').replace('>', '').replace('(', '').replace(')', '').replace("'", '').replace('"', '')
#             timestamp = int(datetime.datetime.now().strftime("%s"))
#             error_data = []
#             error_data.append({"metric": module,
#                                "timestamp": timestamp,
#                                "value": 16,
#                                "message": error_msg,
#                                "status": "ERROR",
#                                "type": "Special",
#                                "reaction": pushdata.negative_handler,
#                                "tags": {"host": pushdata.hostname, "cluster": cluster_name, "group": host_group}})
#             send_err_msg = json.dumps(error_data)
#             if pushdata.sandbox is True:
#                 barlus_style = 'UUID=' + pushdata.oddeye_uuid + '&sandbox=true&data='
#             else:
#                 barlus_style = 'UUID=' + pushdata.oddeye_uuid + '&data='
#
#             send_error_data = barlus_style + send_err_msg
#
#             jonson=pushdata.JonSon()
#
#             def httt_set_opt(url, data):
#                 c.setopt(pycurl.URL, url)
#                 c.setopt(pycurl.POST, 0)
#                 c.setopt(pycurl.POSTFIELDS, data)
#                 c.setopt(pycurl.VERBOSE, 0)
#                 c.setopt(pycurl.TIMEOUT, 3)
#                 c.setopt(pycurl.NOSIGNAL, 5)
#                 c.setopt(pycurl.USERAGENT, 'PuyPuy v.03')
#                 c.setopt(pycurl.ENCODING, "gzip,deflate")
#                 c.setopt(pycurl.WRITEFUNCTION, lambda x: None)
#
#             httt_set_opt(pushdata.tsdb_url, send_error_data)
#             c.setopt(pycurl.POSTFIELDS, send_error_data)
#             c.perform()
#             print_message(" %s : " % module + str(e))
#         else:
#             print_message(" %s : " % module + str(e))
#     try:
#         if module == 'pushdata':
#             print_message(" %s : " % "Cannot connect to Barlus" + str(e))
#             pass
#         else:
#             send_error_msg()
#     except Exception as err:
#         print_message(" %s : " % "Cannot send error" + str(err))

