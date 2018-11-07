#!/usr/bin/env python

import http.client
import json

conn = http.client.HTTPConnection("localhost:8004")
print ("Connected.")

conn.request("GET", "/v1/b45461e4b03547db8f2869d2c9f9e29e/stacks/vcpe_vfmodule_vcpevspvbrg20180628a_201807200645")
r1 = conn.getresponse()
print ("first GET request response:")
print ("----------------------------------------")
print (r1.status)
print (r1.read().decode())

header = { "Content-type": "application/json" }
fd = open('post.json')
to_send = json.load(fd)
data_send = json.dumps(to_send)
conn.request("POST","/v1/b45461e4b03547db8f2869d2c9f9e29e/stacks",data_send,header)
r0 = conn.getresponse()
print ("POST request response:")
print ("----------------------------------------")
print (r0.status)
jdata = json.loads(r0.read())
print(jdata)
random_key = jdata["stack"]["id"]
result = "/v1/b45461e4b03547db8f2869d2c9f9e29e/stacks/vcpe_vfmodule_vcpevspvbrg20180628a_201807200718/{}".format(random_key)

conn.request("GET", result)
r2 = conn.getresponse()
print ("second GET request response:")
print ("----------------------------------------")
print (r2.status)
print (r2.read().decode())

conn.request("GET", result)
r3 = conn.getresponse()
print ("third GET request response:")
print ("----------------------------------------")
print (r3.status)
print (r3.read().decode())

conn.request("GET", result)
r4 = conn.getresponse()
print ("fourth GET request response:")
print ("----------------------------------------")
print (r4.status)
print (r4.read().decode())




