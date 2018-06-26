import lib.record_rate
import lib.getconfig
import lib.puylogger
import lib.basecheck
from pynvml import *

check_type = 'gpu'
reaction = -3

class Check(lib.basecheck.CheckBase):
    def precheck(self):
        try:
            nvmlInit()
            deviceCount = nvmlDeviceGetCount()
            for i in range(deviceCount):
                handle = nvmlDeviceGetHandleByIndex(i)
                try:
                    info = nvmlDeviceGetMemoryInfo(handle)
                    self.local_vars.append({'name': 'nvidia_memory_total', 'timestamp': self.timestamp, 'value': info.total, 'reaction': reaction, 'extra_tag': {'gpu': i}})
                    self.local_vars.append({'name': 'nvidia_memory_free', 'timestamp': self.timestamp, 'value': info.free, 'reaction': reaction, 'extra_tag': {'gpu': i}})
                    self.local_vars.append({'name': 'nvidia_memory_used', 'timestamp': self.timestamp, 'value': info.used, 'reaction': reaction, 'extra_tag': {'gpu': i}})
                except:
                    pass
                try:
                    self.local_vars.append({'name': 'nvidia_graphic_processes', 'timestamp': self.timestamp, 'value': len(nvmlDeviceGetGraphicsRunningProcesses(handle)), 'reaction': reaction, 'extra_tag': {'gpu': i}})
                except:
                    pass
                try:
                    self.local_vars.append({'name': 'nvidia_cuda_processes', 'timestamp': self.timestamp, 'value': len(nvmlDeviceGetComputeRunningProcesses(handle)), 'reaction': reaction, 'extra_tag': {'gpu': i}})
                except:
                    pass
                try:
                    ho = nvmlDeviceGetUtilizationRates(handle)
                    self.local_vars.append({'name': 'nvidia_gpu_utilizaton', 'timestamp': self.timestamp, 'value': ho.gpu, 'reaction': reaction, 'extra_tag': {'gpu': i}})
                    self.local_vars.append({'name': 'nvidia_memory_utilizaton', 'timestamp': self.timestamp, 'value': ho.memory, 'reaction': reaction, 'extra_tag': {'gpu': i}})
                except:
                    pass
                try:
                    self.local_vars.append({'name': 'nvidia_gpu_temperature', 'timestamp': self.timestamp, 'value': nvmlDeviceGetTemperature(handle, i), 'reaction': reaction, 'extra_tag': {'gpu': i}})
                except:
                    pass
                try:
                    self.local_vars.append({'name': 'nvidia_gpu_clock_info', 'timestamp': self.timestamp, 'value': nvmlDeviceGetClockInfo(handle, i), 'reaction': reaction, 'extra_tag': {'gpu': i}})
                except:
                    pass
                try:
                    b1 = nvmlDeviceGetBAR1MemoryInfo(handle)
                    self.local_vars.append({'name': 'nvidia_b1_memory_total', 'timestamp': self.timestamp, 'value': b1.bar1Total, 'reaction': reaction, 'extra_tag': {'gpu': i}})
                    self.local_vars.append({'name': 'nvidia_b1_memory_free', 'timestamp': self.timestamp, 'value': b1.bar1Free, 'reaction': reaction, 'extra_tag': {'gpu': i}})
                    self.local_vars.append({'name': 'nvidia_b1_memory_used', 'timestamp': self.timestamp, 'value': b1.bar1Used, 'reaction': reaction, 'extra_tag': {'gpu': i}})
                except:
                    pass
                try:
                    self.local_vars.append({'name': 'nvidia_fan_speed', 'timestamp': self.timestamp, 'value': nvmlDeviceGetFanSpeed(handle), 'reaction': reaction, 'extra_tag': {'gpu': i}})
                except:
                    pass
                try:
                    self.local_vars.append({'name': 'nvidia_power_usage', 'timestamp': self.timestamp, 'value': nvmlDeviceGetPowerUsage(handle), 'reaction': reaction, 'extra_tag': {'gpu': i}})
                except:
                    pass
            nvmlShutdown()
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass


