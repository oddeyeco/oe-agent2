import subprocess
import lib.getconfig
import lib.basecheck
import lib.puylogger

lizahost = lib.getconfig.getparam('LizardFS', 'host')
lizaport = lib.getconfig.getparam('LizardFS', 'port')
diskstats = lib.getconfig.getparam('LizardFS', 'diskstats')
chunkstats = lib.getconfig.getparam('LizardFS', 'chunkstats')

check_type = 'lizardfs'
reaction = 0
info_names = ('memory_uage', 'total_space', 'available_space', 'trash_space', 'trash_files', 'reserved_space', 'reserved_files', 'fs_objects', 'directories', 'files', 'chunks', 'chunk_copies')

class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            command1 = 'lizardfs-admin info --porcelain ' + lizahost + ' ' + lizaport
            cmd_info = subprocess.Popen(command1, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
            output1, err = cmd_info.communicate()
            infostats = output1.split()
            for info_name in info_names:
                value=infostats[info_names.index(info_name) + 1]
                self.local_vars.append({'name': 'lizardfs_info_' + info_name, 'timestamp': self.timestamp, 'value': value, 'reaction': reaction})
            if chunkstats is True:
                command2 = 'lizardfs-admin list-chunkservers --porcelain ' + lizahost + ' ' + lizaport
                cmd_cunksrv = subprocess.Popen(command2, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
                output, err = cmd_cunksrv.communicate()
                for x in output.split('\n'):
                    if len(x) > 0:
                        a = (x.split())
                        self.local_vars.append({'name': 'lizardfs_chunksrv_used_space', 'timestamp': self.timestamp, 'value': a[3], 'reaction': reaction, 'extra_tag': {'chunkserver': a[0].split(':')[0]}})
                        self.local_vars.append({'name': 'lizardfs_chunksrv_total_space', 'timestamp': self.timestamp, 'value': a[4], 'reaction': reaction, 'extra_tag': {'chunkserver': a[0].split(':')[0]}})
                        self.local_vars.append({'name': 'lizardfs_chunksrv_chunks_mfr', 'timestamp': self.timestamp, 'value': a[5], 'reaction': reaction, 'extra_tag': {'chunkserver': a[0].split(':')[0]}})
                        self.local_vars.append({'name': 'lizardfs_chunksrv_space_mfr', 'timestamp': self.timestamp, 'value': a[6], 'reaction': reaction, 'extra_tag': {'chunkserver': a[0].split(':')[0]}})
                        self.local_vars.append({'name': 'lizardfs_chunksrv_errors', 'timestamp': self.timestamp, 'value': a[7], 'reaction': reaction, 'extra_tag': {'chunkserver': a[0].split(':')[0]}})
            if diskstats is True:
                command3 = 'lizardfs-admin list-disks --porcelain --verbose ' + lizahost + ' ' + lizaport
                cmd_diskstats = subprocess.Popen(command3, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
                output, err = cmd_diskstats.communicate()
                for y in output.split('\n'):
                    if len(y) > 0:
                        b = (y.split())
                        self.local_vars.append({'name': 'lizardfs_disk_total_space', 'timestamp': self.timestamp, 'value': b[7], 'reaction': reaction, 'extra_tag': {'chunkserver': b[0].split(':')[0], 'datadir': b[1].strip('/').replace('/', '_')}})
                        self.local_vars.append({'name': 'lizardfs_disk_used_space', 'timestamp': self.timestamp, 'value': b[8], 'reaction': reaction, 'extra_tag': {'chunkserver': b[0].split(':')[0], 'datadir': b[1].strip('/').replace('/', '_')}})
                        self.local_vars.append({'name': 'lizardfs_disk_chunks', 'timestamp': self.timestamp, 'value': b[9], 'reaction': reaction, 'extra_tag': {'chunkserver': b[0].split(':')[0], 'datadir': b[1].strip('/').replace('/', '_')}})
                        self.local_vars.append({'name': 'lizardfs_read_bytes', 'timestamp': self.timestamp, 'value': b[10], 'reaction': reaction, 'extra_tag': {'chunkserver': b[0].split(':')[0], 'datadir': b[1].strip('/').replace('/', '_')}})
                        self.local_vars.append({'name': 'lizardfs_write_bytes', 'timestamp': self.timestamp, 'value': b[11], 'reaction': reaction, 'extra_tag': {'chunkserver': b[0].split(':')[0], 'datadir': b[1].strip('/').replace('/', '_')}})
                        self.local_vars.append({'name': 'lizardfs_max_read_time', 'timestamp': self.timestamp, 'value': b[12], 'reaction': reaction, 'extra_tag': {'chunkserver': b[0].split(':')[0], 'datadir': b[1].strip('/').replace('/', '_')}})
                        self.local_vars.append({'name': 'lizardfs_max_write_time', 'timestamp': self.timestamp, 'value': b[13], 'reaction': reaction, 'extra_tag': {'chunkserver': b[0].split(':')[0], 'datadir': b[1].strip('/').replace('/', '_')}})
                        self.local_vars.append({'name': 'lizardfs_max_fsync_time', 'timestamp': self.timestamp, 'value': b[14], 'reaction': reaction, 'extra_tag': {'chunkserver': b[0].split(':')[0], 'datadir': b[1].strip('/').replace('/', '_')}})
                        self.local_vars.append({'name': 'lizardfs_read_ops', 'timestamp': self.timestamp, 'value': b[15], 'reaction': reaction, 'extra_tag': {'chunkserver': b[0].split(':')[0], 'datadir': b[1].strip('/').replace('/', '_')}})
                        self.local_vars.append({'name': 'lizardfs_write_ops', 'timestamp': self.timestamp, 'value': b[16], 'reaction': reaction, 'extra_tag': {'chunkserver': b[0].split(':')[0], 'datadir': b[1].strip('/').replace('/', '_')}})
                        self.local_vars.append({'name': 'lizardfs_fsync_ops', 'timestamp': self.timestamp, 'value': b[17], 'reaction': reaction, 'extra_tag': {'chunkserver': b[0].split(':')[0], 'datadir': b[1].strip('/').replace('/', '_')}})

        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass
