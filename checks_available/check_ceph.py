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
            command = 'ceph -n ' + ceph_client + ' --keyring=' + ceph_keyring + ' pg stat -f json'
            p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
            output, err = p.communicate()
            stats = json.loads(output)
    
            self.local_vars.append({'name': 'ceph_num_bytes', 'timestamp': self.timestamp, 'value': stats['num_bytes'], 'check_type': check_type})
            self.local_vars.append({'name': 'ceph_num_pgs', 'timestamp': self.timestamp, 'value': stats['num_pgs'], 'check_type': check_type})
            self.local_vars.append({'name': 'ceph_raw_bytes', 'timestamp': self.timestamp, 'value': stats['raw_bytes'], 'check_type': check_type})
            self.local_vars.append({'name': 'ceph_raw_bytes_avail', 'timestamp': self.timestamp, 'value': stats['raw_bytes_avail'], 'check_type': check_type})
            self.local_vars.append({'name': 'ceph_raw_bytes_used', 'timestamp': self.timestamp, 'value': stats['raw_bytes_used'], 'check_type': check_type})
    
    
    
            if 'io_sec' in stats:
                self.local_vars.append({'name': 'ceph_io_sec', 'timestamp': self.timestamp, 'value': stats['io_sec'], 'check_type': check_type, 'chart_type': 'Rate'})
            else:
                self.local_vars.append({'name': 'ceph_io_sec', 'timestamp': self.timestamp, 'value': 0, 'check_type': check_type, 'chart_type': 'Rate'})
            if 'read_bytes_sec' in stats:
                self.local_vars.append({'name': 'ceph_read_bytes_sec', 'timestamp': self.timestamp, 'value': stats['read_bytes_sec'], 'check_type': check_type, 'chart_type': 'Rate'})
            else:
                self.local_vars.append({'name': 'ceph_read_bytes_sec', 'timestamp': self.timestamp, 'value': 0, 'check_type': check_type, 'chart_type': 'Rate'})
            if 'write_bytes_sec' in stats:
                self.local_vars.append({'name': 'ceph_write_bytes_sec', 'timestamp': self.timestamp, 'value': stats['write_bytes_sec'], 'check_type': check_type, 'chart_type': 'Rate'})
            else:
                self.local_vars.append({'name': 'ceph_write_bytes_sec', 'timestamp': self.timestamp, 'value': 0, 'check_type': check_type, 'chart_type': 'Rate'})
    
            p.stdout.close()
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass
    
