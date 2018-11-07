#!/usr/bin/env python

import http.client

conn = http.client.HTTPConnection("localhost:5000")
print ("Connected.")
conn.request("GET", "/")
r1 = conn.getresponse()
print (r1.status)

conn.request("POST", "/v3/auth/tokens")
r2 = conn.getresponse()
print (r2.status)

conn.request("POST", "/v2.0/tokens")
r3 = conn.getresponse()
print (r3.status)

data1 = r1.read().decode()
data2 = r2.read().decode()
data3 = r3.read().decode()
print("This is first response:")
print("-------------------------------")
print(data1)
print("This is second response:")
print("-------------------------------")
print(data2)
print("This is third response:")
print("-------------------------------")
print(data3)
