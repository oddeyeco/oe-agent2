import logging
import time
import lib.getconfig

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

