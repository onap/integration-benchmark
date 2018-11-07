#!/usr/bin/env python

import http.client

conn = http.client.HTTPConnection("localhost:8774")
print ("Connected.")
conn.request("GET", "/v2.1/b45461e4b03547db8f2869d2c9f9e29e")
r1 = conn.getresponse()
print (r1.status)

conn.request("GET", "/v2.1/")
r2 = conn.getresponse()
print (r2.status)

conn.request("GET", "/v2.1/b45461e4b03547db8f2869d2c9f9e29e/servers/detail")
r3 = conn.getresponse()
print (r3.status)

data3 = r3.read().decode()
data2 = r2.read().decode()
data1 = r1.read().decode()
print("This is first response:")
print("-------------------------------")
print(data1)
print("This is second response:")
print("-------------------------------")
print(data2)
print("This is third response:")
print("-------------------------------")
print(data3)
