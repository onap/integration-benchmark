#! /usr/bin/python

import ConfigParser as cfg


config = cfg.ConfigParser()
config.read('config.ini')
for section in config.sections():
    print(section)
    print(config.options(section))

print(config.get('openstack', '--os-auth-url'))
print(config.getboolean('onap parameters', 'oom_mode'))