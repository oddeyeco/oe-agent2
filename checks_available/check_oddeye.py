import lib.record_rate
import lib.puylogger
import lib.pushdata
import lib.getconfig
import lib.commonclient
import time
import datetime

check_site = 'https://api.oddeye.co/ok.txt'
cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
err_handler = int(lib.getconfig.getparam('TSDB', 'err_handler'))


def runcheck():
    local_vars = []
    try:
        timestamp = int(datetime.datetime.now().strftime("%s"))
        jsondata = lib.pushdata.JonSon()
        check_type = 'health'
        start_time = time.time()
        lib.commonclient.httpget(__name__, check_site)
        resptime = ((time.time() - start_time))
        local_vars.append({'name': 'host_alive', 'timestamp': timestamp, 'value': resptime, 'check_type': check_type})
        message = '{DURATION} without HearBeats from host'
        jsondata.send_special("HeartBeat", timestamp, resptime, message, "OK", err_handler)
        return local_vars
    except Exception as e:
        lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
        pass
