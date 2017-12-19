import lib.record_rate
import lib.puylogger
import lib.pushdata
import lib.getconfig
import lib.commonclient
import lib.basecheck
import time

check_site = 'https://api.oddeye.co/ok.txt'
cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')


class Check(lib.basecheck.CheckBase):

    def precheck(self):

        try:
            check_type = 'health'
            start_time = time.time()
            lib.commonclient.httpget(__name__, check_site)
            resptime = ((time.time() - start_time))
            self.local_vars.append({'name': 'host_alive', 'timestamp': self.timestamp, 'value': resptime, 'check_type': check_type})
            message = '{DURATION} without HearBeats from host'
            self.jsondata.send_special("HeartBeat", self.timestamp, resptime, message, "OK", self.error_handler)
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass
