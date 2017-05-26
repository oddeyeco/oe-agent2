import lib.record_rate
import lib.puylogger
import lib.pushdata
import lib.getconfig
import lib.commonclient
import time
import datetime



check_site='https://barlus.oddeye.co/ok.txt'
cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
err_handler = int(lib.getconfig.getparam('TSDB', 'err_handler'))
#reaction = -3


def runcheck():
    try:


        timestamp = int(datetime.datetime.now().strftime("%s"))
        jsondata=lib.pushdata.JonSon()
        check_type = 'health'
        start_time = time.time()
        lib.commonclient.httpget(__name__, check_site)
        resptime = ((time.time() - start_time))
        jsondata.prepare_data()
        jsondata.gen_data('host_alive', timestamp, resptime, lib.pushdata.hostname, check_type, cluster_name)
        message='{DURATION} without HearBeats from host'
        jsondata.send_special("HeartBeat", timestamp, resptime, message, "OK", err_handler)
        jsondata.put_json()
    except Exception as e:
        lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
        pass
