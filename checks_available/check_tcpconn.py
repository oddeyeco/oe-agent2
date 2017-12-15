import lib.record_rate
import lib.getconfig
import lib.basecheck
import lib.puylogger
check_type = 'system'

reaction = -3

class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            to = []
            with open('/proc/net/tcp') as f:
                lineno = 0
                sockets = []
                for line in f:
                    lineno += 1
                    if lineno == 1:
                        continue
                    ln = line.strip()
                    sockets.append(ln)
            f.close()

            for t in sockets:
                to.append((t.split()[3]))

            enums = {
                '01': 'tcp_established', '02': 'tcp_syn_sent', '03': 'tcp_syn_recv', '04': 'tcp_syn_recv',
                '05': 'tcp_fin_wait1', '06': 'tcp_fin_wait2', '07': 'tcp_time_wait',
                '08': 'tcp_close', '09': 'tcp_close_wait', '0A': 'tcp_last_ack',
                '0B': 'tcp_listen', '0C': 'tcp_closing', '0D': 'tcp_new_syn_recv', '0E': 'tcp_max_states'
            }

            flags = ('01', '02', '03', '04', '05', '06', '07', '08', '09', '0A', '0B', '0C', '0D', '0E')

            for u in flags:
                self.local_vars.append({'name': u.replace(u, enums[u]), 'timestamp': self.timestamp, 'value': to.count(u), 'check_type': check_type})
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass

