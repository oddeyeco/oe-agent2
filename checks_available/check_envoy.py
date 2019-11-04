import lib.record_rate
import lib.commonclient
import lib.getconfig
import lib.puylogger
import lib.basecheck
import re

metrics = lib.getconfig.getparam('Envoy', 'metrics')
check_type = 'envoy'
reaction = 0

meters = ('downstream_cx_total','downstream_cx_ssl_total','downstream_cx_http1_total',
        'downstream_cx_websocket_total','downstream_cx_http2_total','downstream_cx_destroy',
        'downstream_cx_destroy_remote','downstream_cx_destroy_local','downstream_cx_destroy_active_rq',
        'downstream_cx_destroy_local_active_rq','downstream_cx_destroy_remote_active_rq','downstream_cx_active',
        'downstream_cx_ssl_active','downstream_cx_http1_active','downstream_cx_websocket_active',
        'downstream_cx_http2_active','downstream_cx_protocol_error','downstream_cx_length_ms',
        'downstream_cx_rx_bytes_total','downstream_cx_rx_bytes_buffered','downstream_cx_tx_bytes_total',
        'downstream_cx_tx_bytes_buffered','downstream_cx_drain_close','downstream_cx_idle_timeout',
        'downstream_flow_control_paused_reading_total','downstream_flow_control_resumed_reading_total',
        'downstream_rq_total','downstream_rq_http1_total','downstream_rq_http2_total',
        'downstream_rq_active','downstream_rq_response_before_rq_complete','downstream_rq_rx_reset',
        'downstream_rq_tx_reset','downstream_rq_non_relative_path','downstream_rq_too_large',
        'downstream_rq_1xx','downstream_rq_2xx','downstream_rq_3xx','downstream_rq_4xx',
        'downstream_rq_5xx','downstream_rq_ws_on_non_ws_route','downstream_rq_time', 'rs_too_large')


class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            data = lib.commonclient.httpget(__name__, metrics).splitlines()
            for c in data:
                if any(x in c for x in meters) and c.startswith('envoy_') and 'admin' not in c and '_bucket' not in c:
                    o = re.split('{|} ', c.replace('"', ''))
                    tags = o[1].replace('"', '').split('=')
                    self.local_vars.append({'name': o[0], 'timestamp': self.timestamp, 'value': o[2], 'check_type': check_type, 'extra_tag': {tags[0]: tags[1]}})
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass


