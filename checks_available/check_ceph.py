import subprocess
import json
import lib.getconfig
import lib.basecheck
import lib.puylogger

ceph_client = lib.getconfig.getparam('Ceph', 'client')
ceph_keyring = lib.getconfig.getparam('Ceph', 'keyring')
check_type = 'ceph'


class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            command = 'ceph -n ' + ceph_client + ' --keyring=' + ceph_keyring + ' -s -f json'

            p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
            output, err = p.communicate()
            s = json.loads(output)
            pgstats=s['pgmap']
            health = s['health']


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

            self.local_vars.append({'name': 'ceph_bytes_avail', 'timestamp': self.timestamp, 'value': pgstats['bytes_avail'], 'check_type': check_type})
            self.local_vars.append({'name': 'ceph_bytes_total', 'timestamp': self.timestamp, 'value': pgstats['bytes_total'], 'check_type': check_type})
            self.local_vars.append({'name': 'ceph_bytes_used', 'timestamp': self.timestamp, 'value': pgstats['bytes_used'], 'check_type': check_type})
            self.local_vars.append({'name': 'ceph_data_bytes', 'timestamp': self.timestamp, 'value': pgstats['data_bytes'], 'check_type': check_type})
            self.local_vars.append({'name': 'ceph_num_pgs', 'timestamp': self.timestamp, 'value': pgstats['num_pgs'], 'check_type': check_type})

            if 'read_bytes_sec' in pgstats:
                self.local_vars.append({'name': 'ceph_read_bytes_sec', 'timestamp': self.timestamp, 'value': pgstats['read_bytes_sec'], 'check_type': check_type, 'chart_type': 'Rate'})
            else:
                self.local_vars.append({'name': 'ceph_read_bytes_sec', 'timestamp': self.timestamp, 'value': 0, 'check_type': check_type, 'chart_type': 'Rate'})
            if 'write_bytes_sec' in pgstats:
                self.local_vars.append({'name': 'ceph_write_bytes_sec', 'timestamp': self.timestamp, 'value': pgstats['write_bytes_sec'], 'check_type': check_type, 'chart_type': 'Rate'})
            else:
                self.local_vars.append({'name': 'ceph_write_bytes_sec', 'timestamp': self.timestamp, 'value': 0, 'check_type': check_type, 'chart_type': 'Rate'})
            if 'degraded_objects' in pgstats:
                self.local_vars.append({'name': 'ceph_degraded_objects', 'timestamp': self.timestamp, 'value': pgstats['degraded_objects'], 'check_type': check_type})
            else:
                self.local_vars.append({'name': 'ceph_degraded_objects', 'timestamp': self.timestamp, 'value': 0, 'check_type': check_type})
            if 'degraded_ratio' in pgstats:
                self.local_vars.append({'name': 'ceph_degraded_ratio', 'timestamp': self.timestamp, 'value': pgstats['degraded_ratio'], 'check_type': check_type})
            else:
                self.local_vars.append({'name': 'ceph_degraded_ratio', 'timestamp': self.timestamp, 'value': 0.0, 'check_type': check_type})
            if 'degraded_total' in pgstats:
                self.local_vars.append({'name': 'ceph_degraded_total', 'timestamp': self.timestamp, 'value': pgstats['degraded_total'], 'check_type': check_type})
            else:
                self.local_vars.append({'name': 'ceph_degraded_total', 'timestamp': self.timestamp, 'value': 0, 'check_type': check_type})
            if 'recovering_bytes_per_sec' in pgstats:
                self.local_vars.append({'name': 'ceph_recovering_bytes_per_sec', 'timestamp': self.timestamp, 'value': pgstats['recovering_bytes_per_sec'], 'check_type': check_type})
            else:
                self.local_vars.append({'name': 'ceph_recovering_bytes_per_sec', 'timestamp': self.timestamp, 'value': 0, 'check_type': check_type})
            if 'num_objects_recovered' in pgstats:
                self.local_vars.append({'name': 'ceph_num_objects_recovered', 'timestamp': self.timestamp, 'value': pgstats['num_objects_recovered'], 'check_type': check_type})
            else:
                self.local_vars.append({'name': 'ceph_num_objects_recovered', 'timestamp': self.timestamp, 'value': 0, 'check_type': check_type})
            if 'recovering_keys_per_sec' in pgstats:
                self.local_vars.append({'name': 'ceph_recovering_keys_per_sec', 'timestamp': self.timestamp, 'value': pgstats['recovering_keys_per_sec'], 'check_type': check_type})
            else:
                self.local_vars.append({'name': 'ceph_recovering_keys_per_sec', 'timestamp': self.timestamp, 'value': 0, 'check_type': check_type})

        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass

