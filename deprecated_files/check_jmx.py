import lib.record_rate
import lib.pushdata
import lib.puylogger
# Requires jpype, Please install it (apt-get install python-jpype)
import os, sys
import ConfigParser
import datetime
import socket

import jpype
from jpype import java
from jpype import javax

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/java.ini')

HOST= config.get('JMX', 'host')
PORT= config.get('JMX', 'port')
USER= config.get('JMX', 'user')
PASS= config.get('JMX', 'pass')
JAVA= config.get('JMX', 'java_home')
URL = 'service:jmx:rmi:///jndi/rmi://'+HOST+':'+PORT+'/jmxrmi'

hostname = socket.getfqdn()
cluster_name = config.get('SelfConfig', 'cluster_name')
check_type = 'jmx'

if config.has_option('JMX', 'gctype'):
    TYPE = config.get('JMX', 'gctype')
else:
    TYPE=None

if TYPE == 'G1':
    CMS=False
    G1=True
elif TYPE == 'CMS':
    CMS=True
    G1=False
else:
    CMS=False
    G1=False

os.environ['JAVA_HOME'] = JAVA

JAVA = config.get('JMX', 'java_home')


def init_jvm():
    if jpype.isJVMStarted():
        return
    else:
        #jpype.startJVM(jpype.getDefaultJVMPath())
        #jvmArgs = ['-verbose:gc -Xloggc:/tmp/puypuyJ.log  -Dcom.sun.management.jmxremote.port=12345 -Dcom.sun.management.jmxremote.rmi.port=12345 -Dcom.sun.management.jmxremote.ssl=false -Dcom.sun.management.jmxremote.authenticate=false']
        jpype.startJVM((jpype.getDefaultJVMPath()), ['-Xmx128m','-verbose:gc'])
        if not jpype.isThreadAttachedToJVM():
            jpype.attachThreadToJVM()

init_jvm()


def try_connection():
    try:
        os.environ['JAVA_HOME'] = JAVA
        jhash = java.util.HashMap()
        jarray = jpype.JArray(java.lang.String)([USER, PASS])
        jhash.put(javax.management.remote.JMXConnector.CREDENTIALS, jarray);
        jmxurl = javax.management.remote.JMXServiceURL(URL)
        jmxsoc = javax.management.remote.JMXConnectorFactory.connect(jmxurl, jhash)
        global connection
        connection = jmxsoc.getMBeanServerConnection();
    except Exception as e:
        connection = None
        lib.pushdata.print_error(__name__, (e))
        pass

try_connection()


# def g_c():
#     lib.puylogger.print_message('Before GC')
#     jpype.java.lang.System.gc()
#     lib.puylogger.print_message('After GC')
#

def runcheck():
    def run_all(connection):
        try:
            sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
            rate=lib.record_rate.ValueRate()
            jsondata=lib.pushdata.JonSon()
            jsondata.prepare_data()
            timestamp = int(datetime.datetime.now().strftime("%s"))

            object = 'java.lang:type=Memory'
            attribute = 'HeapMemoryUsage'
            attr = connection.getAttribute(javax.management.ObjectName(object), attribute)

            heap_attributes=('used', 'committed', 'init', 'max')
            for heap in heap_attributes:
                value = str(attr.contents.get(heap))
                jsondata.gen_data('jmx_heap_'+ heap, timestamp, value, lib.pushdata.hostname, check_type, cluster_name)

            threads_bean = 'java.lang:type=Threading'
            threads_mbeans=('PeakThreadCount', 'DaemonThreadCount', 'ThreadCount')
            for mbean in threads_mbeans:
                value = str(connection.getAttribute(javax.management.ObjectName(threads_bean), mbean))
                jsondata.gen_data('jmx_'+ mbean, timestamp, value, lib.pushdata.hostname, check_type, cluster_name)

            if CMS is True:
                object = 'java.lang:type=GarbageCollector,name=ConcurrentMarkSweep'
                GcCount = 'CollectionCount'
                ColCount = str(connection.getAttribute(javax.management.ObjectName(object), GcCount))
                jsondata.gen_data('jmx_CMSGcCount', timestamp, ColCount, lib.pushdata.hostname, check_type, cluster_name)

                GcTime = 'CollectionTime'
                ColTime = connection.getAttribute(javax.management.ObjectName(object), GcTime)

                GcTime_rate = rate.record_value_rate('jmx_CMSGcTime', ColTime.value, timestamp)
                jsondata.gen_data('jmx_CMSGcTime', timestamp, GcTime_rate, lib.pushdata.hostname, check_type, cluster_name)
                try:
                    object = 'java.lang:type=GarbageCollector,name=ParNew'
                    PnGcCount = 'CollectionCount'
                    PnColCount = connection.getAttribute(javax.management.ObjectName(object), PnGcCount)

                    PnGcTime = 'CollectionTime'
                    PnColTime = connection.getAttribute(javax.management.ObjectName(object), PnGcTime)
                    PnColTime_value=str(PnColTime.value)
                    strPnColCount=str(PnColCount)
                    jsondata.gen_data('jmx_' + 'ParNewGcCount', timestamp, strPnColCount, lib.pushdata.hostname, check_type, cluster_name)
                    GcTime_rate = rate.record_value_rate('jmx_ParNewGcTime', PnColTime_value, timestamp)
                    jsondata.gen_data('jmx_ParNewGcTime', timestamp, GcTime_rate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')

                except Exception as e:
                    lib.pushdata.print_error(__name__, (e))

            if G1 is True:
                object = 'java.lang:type=GarbageCollector,name=G1 Old Generation'
                OldGcCount = 'CollectionCount'
                OldColCount = str(connection.getAttribute(javax.management.ObjectName(object), OldGcCount))

                OldGcTime = 'CollectionTime'
                OldColTime = connection.getAttribute(javax.management.ObjectName(object), OldGcTime)

                jsondata.gen_data('jmx_G1_' + 'OldGcCount', timestamp, OldColCount, lib.pushdata.hostname, check_type, cluster_name)
                OldGcTime_rate = rate.record_value_rate('jmx_G1_OldGcTime', OldColTime.value, timestamp)
                jsondata.gen_data('jmx_G1_OldGcTime', timestamp, str(OldGcTime_rate), lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')

                object = 'java.lang:type=GarbageCollector,name=G1 Young Generation'
                YoungGcCount = 'CollectionCount'
                YoungColCount = connection.getAttribute(javax.management.ObjectName(object), YoungGcCount)

                YoungGcTime = 'CollectionTime'
                YoungColTime = connection.getAttribute(javax.management.ObjectName(object), YoungGcTime)

                jsondata.gen_data('jmx_G1_' + 'YoungGcCount', timestamp, str(YoungColCount), lib.pushdata.hostname, check_type, cluster_name)
                YoungColTime_rate = rate.record_value_rate('jmx_G1_YoungColTime', YoungColTime.value, timestamp)
                jsondata.gen_data('jmx_G1_YoungGcTime', timestamp, YoungColTime_rate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')

            jsondata.put_json()
        except Exception as e:
            lib.pushdata.print_error(__name__, (e, java.rmi.ConnectException))
            try_connection()
            pass
    run_all(connection)
