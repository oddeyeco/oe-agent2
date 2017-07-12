import lib.puylogger

# def init():
#     global last_value
#     last_value = {}
#     return last_value

last_value = {}

class ValueRate(object):

    metrics_value_rate = 0
    def __init__(self):
        self.metrics_value_rate = 0

    def record_value_rate(self, mytype, myvalue, timestamp):
        if mytype not in last_value:
            last_value.update({mytype:myvalue, mytype+'_timestamp':timestamp})
            return 0
        else:
            try:
                value_delta = int(myvalue) - int(last_value[mytype])
                time_delta = timestamp - last_value[mytype+'_timestamp']
                metrics_rate = value_delta/time_delta
                last_value.update({mytype:myvalue})
                ValueRate.metrics_value_rate = mytype+'_timestamp'
                last_value.update({ValueRate.metrics_value_rate:timestamp})
                if lib.puylogger.debug_log:
                    lib.puylogger.print_message(__name__ + ' ' + str(mytype) + ' ' + str(last_value))
                if metrics_rate < 0:
                    metrics_rate = 1
                return metrics_rate
            except Exception as e:
                push = __import__('pushdata')
                push.print_error(__name__, (e))
                pass

    def update_timestamp(self, timestamp):
        pass



