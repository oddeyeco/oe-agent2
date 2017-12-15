import lib.record_rate
import lib.getconfig
import lib.pushdata
import lib.puylogger
import datetime


class CheckBase:
    check_type = 'base'
    values_type = 'none'
    local_vars = []
    rate = lib.record_rate.ValueRate()
    last = lib.record_rate.GetPrevValue()
    jsondata = lib.pushdata.JonSon()
    metrics = []

    def __init__(self):
        self.cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
        self.host_group = lib.getconfig.getparam('SelfConfig', 'host_group')
        self.location = lib.getconfig.getparam('SelfConfig', 'location')
        self.timestamp = int(datetime.datetime.now().strftime("%s"))

    def info(self):
        for t in self.local_vars:
            lib.puylogger.print_message(self.__module__ + ' : ' + str(t))

    def precheck(self):
        pass

    def runcheck(self):
        self.local_vars = []
        self.precheck()
        # self.info()
        for k in self.local_vars:
            if 'host' not in k:
                k['host']=lib.pushdata.hostname
        return self.local_vars

