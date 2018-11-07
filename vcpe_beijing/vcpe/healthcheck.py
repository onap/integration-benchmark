#! /usr/bin/python

import logging
import json
from vcpecommon import *
import commands


logging.basicConfig(level=logging.INFO, format='%(message)s')
common = VcpeCommon()

print('Checking vGMUX REST API from SDNC')
cmd = 'curl -u admin:admin -X GET http://10.0.101.21:8183/restconf/config/ietf-interfaces:interfaces'
ret = commands.getstatusoutput("ssh -i onap_dev root@172.30.22.59 '{0}'".format(cmd))
sz = ret[-1].split('\n')[-1]
print('\n')
print(sz)

print('\n')
print('Checking vBRG REST API from SDNC')
#cmd = 'curl -u admin:admin -X GET http://10.3.0.4:8183/restconf/config/ietf-interfaces:interfaces'
cmd = 'curl -u admin:admin -X GET http://10.3.0.5:8183/restconf/config/ietf-interfaces:interfaces'
ret = commands.getstatusoutput("ssh -i onap_dev root@172.30.22.59 '{0}'".format(cmd))
sz = ret[-1].split('\n')[-1]
print('\n')
print(sz)

print('\n')
print('Checking SDNC DB for vBRG MAC address')
mac = common.get_brg_mac_from_sdnc()
print(mac)


