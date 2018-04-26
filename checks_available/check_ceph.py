import subprocess
import json
import lib.getconfig
import lib.basecheck
import lib.puylogger

ceph_client = lib.getconfig.getparam('Ceph', 'client')
ceph_keyring = lib.getconfig.getparam('Ceph', 'keyring')
check_type = 'ceph'

lo = ['read_bytes_sec', 'write_bytes_sec' ,'degraded_objects' ,'degraded_ratio','degraded_total',
      'recovering_bytes_per_sec', 'num_objects_recovered', 'recovering_keys_per_sec',
      'bytes_avail', 'bytes_total', 'bytes_used', 'data_bytes', 'num_pgs']

class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            command1 = 'ceph00 ceph -n ' + ceph_client + ' --keyring=' + ceph_keyring + ' -s -f json'
            command2 = 'ceph00 ceph -n ' + ceph_client + ' --keyring=' + ceph_keyring + ' pg stat -f json'

            p1 = subprocess.Popen(command1, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
            output1, err = p1.communicate()
            s1 = json.loads(output1)
            stats=s1['pgmap']
            health = s1['health']

            p2 = subprocess.Popen(command2, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
            output2, err = p2.communicate()
            pgstats = json.loads(output2)

            if health['overall_status'] == 'HEALTH_OK':
                health_value = 0
                err_type = 'OK'
            elif health['overall_status'] == 'HEALTH_WARN':
                health_value = 9
                err_type = 'WARNING'
            else:
                health_value = 16
                err_type = 'ERROR'

            message = health['overall_status']
            for item in health['summary']:
                message = message + ', ' + item['summary'].replace('%', ' Percent')

            self.jsondata.send_special("Ceph-Health", self.timestamp, health_value, message, err_type)

            if 'io_sec' in pgstats:
                self.local_vars.append({'name': 'ceph_io_sec', 'timestamp': self.timestamp, 'value': pgstats['io_sec'], 'check_type': check_type, 'chart_type': 'Rate'})
            else:
                self.local_vars.append({'name': 'ceph_io_sec', 'timestamp': self.timestamp, 'value': 0, 'check_type': check_type, 'chart_type': 'Rate'})

            for t in lo:
                if t in stats:
                    self.local_vars.append({'name': 'ceph_' + t, 'timestamp': self.timestamp, 'value': stats[t], 'check_type': check_type})
                else:
                    self.local_vars.append({'name': 'ceph_' + t, 'timestamp': self.timestamp, 'value': 0, 'check_type': check_type})

        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass


