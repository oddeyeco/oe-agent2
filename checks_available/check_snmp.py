import lib.record_rate
import lib.getconfig
import lib.puylogger
import datetime
import os
from pysnmp.hlapi import *
from pysnmp.entity.rfc3413.oneliner import cmdgen

check_type = 'snmp'
cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
server = lib.getconfig.getparam('SNMP', 'server')
port = lib.getconfig.getparam('SNMP', 'port')
auth_protocol = lib.getconfig.getparam('SNMP', 'authProtocol')
priv_protocol = lib.getconfig.getparam('SNMP', 'privProtocol')
AuthPassphrase = lib.getconfig.getparam('SNMP', 'AuthPassphrase')
PrivPassphrase = lib.getconfig.getparam('SNMP', 'PrivPassphrase')
SecurityName = lib.getconfig.getparam('SNMP', 'SecurityName')
auth = lib.getconfig.getparam('SNMP', 'auth')

mibsfile = os.getcwd() + '/../conf/snmpmibs.txt'
reaction = -3


authprotos = {'MD5': usmHMACMD5AuthProtocol,
              'SHA': usmHMACSHAAuthProtocol}
protocols = {'DES': usmDESPrivProtocol,
             '3DES': usm3DESEDEPrivProtocol,
             'AES128': usmAesCfb128Protocol,
             'AES192': usmAesCfb192Protocol,
             'AES256': usmAesCfb256Protocol}

if auth_protocol in authprotos:
    authProtocol = authprotos[auth_protocol]

if priv_protocol in protocols:
    privProtocol = protocols[priv_protocol]


def nonblank_lines(f):
    for l in f:
        line = l.rstrip()
        if line:
            yield line

mibo = {}

with open(mibsfile) as f_in:
    for line in nonblank_lines(f_in):
        if not line.strip().startswith('#'):
            (key, val) = line.split()
            mibo[key] = val

f_in.close()


def runcheck():
    local_vars = []

    timestamp = int(datetime.datetime.now().strftime("%s"))
    try:
        def getValuesF(n, oid):
            cmdGen = cmdgen.CommandGenerator()

            errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
                cmdgen.CommunityData('public', mpModel=0), cmdgen.UdpTransportTarget((server, port)),
                cmdgen.MibVariable(oid),
            )

            if errorIndication:
                print(errorIndication)
            else:
                if errorStatus:
                    print('%s at %s' % (
                        errorStatus.prettyPrint(),
                        errorIndex and varBinds[int(errorIndex) - 1] or '?'
                    )
                          )
                else:
                    for name, val in varBinds:
                        local_vars.append({'name': 'snmp_' + n, 'timestamp': timestamp, 'value': val})
        def getValuesT(name, oid):
            errorIndication, errorStatus, errorIndex, varBinds = next(
                getCmd(SnmpEngine(),
                       UsmUserData(SecurityName, AuthPassphrase, PrivPassphrase,
                                   authProtocol=authProtocol,
                                   privProtocol=privProtocol
                                   ),
                       UdpTransportTarget((server, port)),
                       ContextData(),
                       ObjectType(ObjectIdentity(oid)))
            )

            if errorIndication:
                print(errorIndication)
            elif errorStatus:
                print('%s at %s' % (errorStatus.prettyPrint(), errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
            else:
                for varBind in varBinds:
                    value = str(varBind.prettyPrint()).replace(' ', '').split('=')[1]
                    local_vars.append({'name': 'snmp_' + name, 'timestamp': timestamp, 'value': value})

        for k, v in mibo.items():
            if auth is True:
                getValuesT(k, v)
            else:
                getValuesF(k, v)
        return local_vars
    except Exception as e:
        lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
        pass







