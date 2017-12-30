import lib.getconfig
import lib.pushdata
import lib.puylogger
import lib.basecheck
from subprocess import Popen, PIPE

cfgs = lib.getconfig.getsection('Nagios')
nagcfgs = {}

for cfg in cfgs:
    nagcfgs[cfg] = lib.getconfig.getparam('Nagios', cfg)
check_type = 'nagios'

backend = lib.getconfig.getparam('TSDB', 'tsdtype')


class Check(lib.basecheck.CheckBase):

    def precheck(self):
        if backend == 'OddEye':
            try:
                for k, v in nagcfgs.items():
                    p = Popen(v.split(), stdout=PIPE)
                    (output, err) = p.communicate()
                    exit_code = p.wait()
                    health_message = output.decode("utf-8").replace('\n', '').replace(':', ' ').replace(',', ' ').replace(';', '|').replace('%', ' Percent')
                    if exit_code is 0:
                        health_value = 0
                        err_type = 'OK'
                        self.jsondata.send_special('Nagios', self.timestamp, health_value, health_message, err_type)
                    if exit_code is 1:
                        health_value = 8
                        err_type = 'WARNING'
                        self.jsondata.send_special('Nagios', self.timestamp, health_value, health_message, err_type)
                    else:
                        health_value = 16
                        err_type = 'ERROR'
                        self.jsondata.send_special('Nagios', self.timestamp, health_value, health_message, err_type)

            except Exception as e:
                lib.pushdata.print_error(__name__ , (e))
                pass

