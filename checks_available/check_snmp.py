import lib.getconfig
import lib.puylogger
import lib.basecheck
import os
import configparser
from pysnmp.hlapi import *
from pysnmp.entity.rfc3413.oneliner import cmdgen

config = configparser.RawConfigParser()
config_file = os.getcwd() + '/../conf/snmp.ini'
config.read(config_file)

check_type = 'snmp'

authprotos = {'MD5': usmHMACMD5AuthProtocol, 'SHA': usmHMACSHAAuthProtocol}
protocols = {'DES': usmDESPrivProtocol, '3DES': usm3DESEDEPrivProtocol,'AES128': usmAesCfb128Protocol, 'AES192': usmAesCfb192Protocol,'AES256': usmAesCfb256Protocol}
servantvalues = ['auth' ,'port', 'server', 'authprotocol', 'privprotocol', 'securityname', 'authpassphrase', 'privpassphrase']

class Check(lib.basecheck.CheckBase):

    def precheck(self):

        try:
            def getValuesF(n, oid, srv, prt, host):
                cmdGen = cmdgen.CommandGenerator()
    
                errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
                    cmdgen.CommunityData('public', mpModel=0), cmdgen.UdpTransportTarget((srv, prt)),
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
                            self.local_vars.append({'name': 'snmp_' + n, 'timestamp': self.timestamp, 'value': val, 'hostname' : host})
            def getValuesT(name, oid, srv, prt, host, authProto, privProto, SecName, AuthPass, PrivPass):
                errorIndication, errorStatus, errorIndex, varBinds = next(
                    getCmd(SnmpEngine(),
                           UsmUserData(SecName, AuthPass, PrivPass,
                                       authProtocol=authProto,
                                       privProtocol=privProto
                                       ),
                           UdpTransportTarget((srv, prt)),
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
                        self.local_vars.append({'name': 'snmp_' + name, 'timestamp': self.timestamp, 'value': value , 'hostname' : host})
    
            for t in config.sections():
                a = dict(config.items(t))
                if a['auth'] == 'True':
                    for k, v in a.items():
                        if k not in servantvalues:
                            ap = authprotos[a['authprotocol']]
                            pp = protocols[a['privprotocol']]
                            getValuesT(k, v, a['server'], a['port'], t, ap, pp, a['securityname'], a['authpassphrase'], a['privpassphrase'])
                else:
                    for k, v in a.items():
                        if k not in servantvalues:
                            getValuesF(k, v, a['server'], a['port'], t)
    
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass
    
