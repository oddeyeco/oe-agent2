import lib.record_rate
import lib.pushdata
import urllib2
import time
import os, sys
import datetime
import ConfigParser


check_site='https://barlus.oddeye.co/ok.txt'
config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
cluster_name = config.get('SelfConfig', 'cluster_name')
err_handler = int(config.get('TSDB', 'err_handler'))
#reaction = -3


def run_oddeye():
    try:
        timestamp = int(datetime.datetime.now().strftime("%s"))
        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
        jsondata=lib.pushdata.JonSon()
        check_type = 'health'
        start_time = time.time()
        response = urllib2.urlopen(check_site, timeout=15)
        resptime = ((time.time() - start_time))
        jsondata.prepare_data()
        jsondata.gen_data('host_alive', timestamp, resptime, lib.pushdata.hostname, check_type, cluster_name)
        message='{DURATION} without HearBeats from host'
        jsondata.send_special("HeartBeat", timestamp, resptime, message, "OK", err_handler)
        jsondata.put_json()
    except Exception as e:
        import logging
        log_file = config.get('SelfConfig', 'log_file')
        logging.basicConfig(filename=log_file, level=logging.DEBUG)
        logger = logging.getLogger("PuyPuy")
        logger.setLevel(logging.DEBUG)
        logging.critical(" %s : " % "Cannot connect to Barlus" + str(e))
        pass
