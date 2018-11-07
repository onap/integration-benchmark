#!/usr/bin/env python
"""
Usage::
    ./server.py [<port>]

Send a GET request::
    curl http://localhost:port_number
Send a HEAD request::
    curl -I http://localhost:port_number
Send a POST request::
    curl -d "foo=bar&bin=baz" http://localhost:port_number

    ./8774-client.py
    ./5000-client.py
    python3 client-8004.py

To change IP address:
    ./server.py <port> <new ip addr>
    
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import date
from datetime import datetime,timedelta
import random
import string
import json

class MockServer(BaseHTTPRequestHandler): 
    def robot_gettime(self):
        '''
        return a list of formatted time: [issue_at,expire_at]
        format same as openstack date/time.
        expire time is 1 hour later than issue time.
        '''
        date_ymd = date.today()
        time_ms = datetime.now().time()
        issue_time = "{}T{}Z".format(date_ymd,time_ms)
        expire_ms = datetime.now() + timedelta(hours=1)
        expire_time = "{}T{}Z".format(date_ymd,expire_ms.time())
        tlist = [issue_time,expire_time]
        return tlist

    def gettime(self):
        '''
        return a list of formatted time: [creation_time,updated_time]
        format same as openstack date/time.
        expire time is 1 second later than issue time.
        '''
        date_ymd = date.today()
        time_ms = datetime.now().strftime("%H:%M:%S")
        creation_time = "{}T{}Z".format(date_ymd,time_ms)
        expire_ms = datetime.now() + timedelta(seconds=1)
        updated = "{}T{}Z".format(date_ymd,expire_ms.time().strftime("%H:%M:%S"))
        tlist = [creation_time,updated]
        return tlist

    def random_id(self):
        '''
        randomly generate a 36 character id:
        8-4-4-4-12
        -------------------
        TODO: format of letters and digits?
        -------------------
        '''
        chars = string.digits + "abcdef"
        first = ''.join(random.choice(chars) for _ in range(8))
        snd = ''.join(random.choice(chars) for _ in range(4))
        thd = ''.join(random.choice(chars) for _ in range(4))
        foth = ''.join(random.choice(chars) for _ in range(4))
        fifth = ''.join(random.choice(chars) for _ in range(12))
        return "{}-{}-{}-{}-{}".format(first,snd,thd,foth,fifth)

    def random_token(self):
        '''
        In response 201 from 5000 port, X-Subject-Token is sent.
        The following resquests forward to port 8774,
        need to include this token in header as X-Auth-Token.
        e.g. 9450e620b7a24648bf54425047e59aae
             295ea4b0d2e5447a9f2575692d2dc2ee

        '''
        chars = string.digits + "abcdef"
        tok = ''.join(random.choice(chars) for _ in range(32))
        return tok

    def get_5000_res(self):
        '''
        FOR PORT 5000:
            respond 300 Multiple choice to GET
        '''
        self.send_response(300)
        self.send_header('Vary', 'X-Auth-Token')
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-length', 595)
        #self.send_header('Date',self.date_time_string())
        self.end_headers()
        json_data = open('respond-300.json')
        jdata = json.load(json_data)
        self.wfile.write(json.dumps(jdata).encode())


    def post_8004_res(self,name_str):
        '''
        FOR PORT 8004:
            respond 201 to POST
            use name_str to construct href
        '''
        #r_id = "5325f4e6-f266-49d6-9bcb-0f085b83497d"
        r_id = self.random_id()
        global addr_str
        result = "http://{}:8004/v1/b45461e4b03547db8f2869d2c9f9e29e/stacks/{}/{}".format(addr_str,name_str,r_id)
        json_data = open('so-201.json')
        jdata = json.load(json_data)
        jdata["stack"]["id"] = r_id
        jdata["stack"]["links"][0]["href"] = result
        to_write = json.dumps(jdata).encode()
        self.send_response(201)
        self.send_header('Location', result)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-length', len(to_write))
        req_id = "req-{}".format(self.random_id())
        self.send_header('X-Openstack-Request-Id', req_id)
        #self.send_header('Date',self.date_time_string())
        self.end_headers()
        self.wfile.write(to_write)

    def respond_404(self):
        '''
        FOR PORT 8774:
            send 404 to first GET
        '''
        self.send_response(404)
        self.send_header('Content-length', 112)
        self.send_header('Content-type', 'application/json; charset=UTF-8')
        req_id = "req-{}".format(self.random_id())
        self.send_header('X-Compute-Request-Id', req_id)
        #self.send_header('Date',self.date_time_string())
        self.end_headers()
        json_msg = {
            "message": "The resource could not be found.<br /><br />\n\n\n",
            "code": "404 Not Found",
            "title": "Not Found"
        }
        self.wfile.write(json.dumps(json_msg).encode())

    def respond_404_so(self,path):
        '''
        send 404 to short GET(port 8004) - vbrg
        and 404 to vgw
        '''
        json_data = open('404-so.json')
        json_msg = json.load(json_data)
        error_msg = "The Stack ({}) could not be found.".format(path.split("/")[-1])
        json_msg["error"]["message"] = error_msg
        to_write = json.dumps(json_msg).encode()
        self.send_response(404)
        self.send_header('Content-type', 'application/json; charset=UTF-8')
        self.send_header('Content-length', len(to_write))
        req_id = "req-{}".format(self.random_id())
        self.send_header('X-Openstack-Request-Id', req_id)
        self.end_headers()
        self.wfile.write(to_write)


    def post_5000_res(self):
        '''
        FOR PORT 5000:
            respond 201 to POST
        '''
        json_data = open('respond-201.json')
        jdata = json.load(json_data)
        time_now = self.robot_gettime()
        jdata["token"]["issued_at"] = time_now[0]
        jdata["token"]["expires_at"] = time_now[1]
        global IP_FLAG
        if IP_FLAG == True:
            global addr_str
            url_new = "http://{}:8774/v2.1/b45461e4b03547db8f2869d2c9f9e29e".format(addr_str)
            jdata["token"]["catalog"][11]["endpoints"][0]["url"] = url_new
            jdata["token"]["catalog"][11]["endpoints"][1]["url"] = url_new
            jdata["token"]["catalog"][11]["endpoints"][2]["url"] = url_new
        '''
        ----------------------------------
        "audit_ids" varies, fixed as:
            ItFVIpXGTYC776YSQ4AIoQ
        -----------------------------------
        '''
        self.send_response(201)
        self.send_header('Vary', 'X-Auth-Token')
        self.send_header('Content-type', 'application/json')
        to_write = json.dumps(jdata).encode()
        self.send_header('Content-length', len(to_write))
        req_id = "req-{}".format(self.random_id())
        self.send_header('X-Openstack-Request-Id', req_id)
        self.send_header('X-Subject-Token', self.random_token())
        #self.send_header('Date',self.date_time_string())
        self.end_headers()
        self.wfile.write(to_write)

    def post_5000_so(self):
        json_data = open('so_post_5000.json')
        jdata = json.load(json_data)
        time_now = self.robot_gettime()
        jdata["access"]["token"]["issued_at"] = time_now[0]
        jdata["access"]["token"]["expires"] = time_now[1]
        
        #TODO: jdata["access"]["token"]['id']+['audit id']

        global IP_FLAG
        if IP_FLAG == True:
            global addr_str
            url_new = "http://{}:8004/v1/b45461e4b03547db8f2869d2c9f9e29e".format(addr_str)
            jdata["access"]["serviceCatalog"][11]["endpoints"][0]["adminURL"] = url_new
            jdata["access"]["serviceCatalog"][11]["endpoints"][0]["internalURL"] = url_new
            jdata["access"]["serviceCatalog"][11]["endpoints"][0]["publicURL"] = url_new
        to_write = json.dumps(jdata).encode()
        self.send_response(200)
        self.send_header('Vary', 'X-Auth-Token')
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-length', len(to_write))
        #self.send_header('Server', 'gunicorn/19.7.1')
        req_id = "req-{}".format(self.random_id())
        self.send_header('x-openstack-request-id', req_id)
        #self.send_header('Date',self.date_time_string())
        self.end_headers()
        self.wfile.write(to_write)

    def respond_200_s(self):
        '''
        FOR PORT 8774:
            send short 200 to second GET
        '''
        self.send_response(200)
        self.send_header('Content-length', 385)
        self.send_header('Content-type', 'application/json')
        self.send_header('Openstack-Api-Version', 'compute 2.1')
        self.send_header('X-Openstack-Nova-Api-Version', '2.1')
        self.send_header('Vary', 'OpenStack-API-Version')
        self.send_header('Vary', 'X-OpenStack-Nova-API-Version')
        req_id = "req-{}".format(self.random_id())
        self.send_header('X-Compute-Request-Id', req_id)
        #self.send_header('Date',self.date_time_string())
        self.end_headers()
        json_data = open('respond-200-s.json')
        jdata = json.load(json_data)
        self.wfile.write(json.dumps(jdata).encode())

    def respond_200_l(self):
        '''
        FOR PORT 8774:
            send long 200 to third GET
        ---------
        TODO:
            how to change long 200 respond??
        -----------
        '''''''''
        self.send_response(200)
        self.send_header('Content-length', 211749)
        self.send_header('Content-type', 'application/json')
        self.send_header('Openstack-Api-Version', 'compute 2.38')
        self.send_header('X-Openstack-Nova-Api-Version', '2.38')
        self.send_header('Vary', 'OpenStack-API-Version')
        self.send_header('Vary', 'X-OpenStack-Nova-API-Version')
        req_id = "req-{}".format(self.random_id())
        self.send_header('X-Compute-Request-Id', req_id)
        #self.send_header('Date',self.date_time_string())
        self.end_headers()
        json_data = open('respond-200-l.json')
        jdata = json.load(json_data)
        self.wfile.write(json.dumps(jdata).encode())
        

    def respond_200(self,path,count):
        global TIME, INFO, addr_str
        get_list = path.split("/")
        c_id = get_list[-1]
        #print("path is {}".format(path))
        stack_name = get_list[-2]
        #print("stack name is {}".format(stack_name))
        #print("name suffix is {}".format(name_suffix))
        info_list = INFO[stack_name]
        '''
        list for vgw:
        ["vgw_name_0","vf_module_id","vgw_private_ip_1",
        "vgw_private_ip_0","vg_vgmux_tunnel_vni","vgw_private_ip_2","vnf_id"]

        list for vbrg:
        ["vbrgemu_name_0",vf_module_id","vbrgemu_private_ip_0","vnf_id"]
        '''
        if 'vcpe_vgw' in stack_name:
            json_data = open('vgw-200.json')
            json_msg = json.load(json_data)
            json_msg["stack"]["parameters"]["OS::stack_name"] = stack_name
            json_msg["stack"]["parameters"]["OS::stack_id"] = c_id
            json_msg["stack"]["parameters"]["vf_module_id"] = info_list[1]
            json_msg["stack"]["parameters"]["vgw_name_0"] = info_list[0]
            json_msg["stack"]["parameters"]["vgw_private_ip_1"] = info_list[2]
            json_msg["stack"]["parameters"]["vgw_private_ip_0"] = info_list[3]
            json_msg["stack"]["parameters"]["vg_vgmux_tunnel_vni"] = info_list[4]
            json_msg["stack"]["parameters"]["vgw_private_ip_2"] = info_list[5]
            json_msg["stack"]["parameters"]["vnf_id"] = info_list[6]
            json_msg["stack"]["stack_name"] = stack_name
            json_msg["stack"]["creation_time"] = TIME[path][0]
            json_msg["stack"]["links"][0]["href"] = "http://{}:8004{}".format(addr_str,path)
            json_msg["stack"]["updated_time"] = TIME[path][1]
            json_msg["stack"]["id"] = c_id
            '''
            "stack_user_project_id"
            '''
        else:
            json_data = open('so-200.json')
            json_msg = json.load(json_data)
            json_msg["stack"]["parameters"]["OS::stack_name"] = stack_name
            json_msg["stack"]["parameters"]["OS::stack_id"] = c_id
            #json_msg["stack"]["parameters"]["vbrgemu_private_ip_0"] = info_list[2]
            json_msg["stack"]["parameters"]["vbrgemu_name_0"] = info_list[0]
            json_msg["stack"]["parameters"]["vnf_id"] = info_list[2]
            json_msg["stack"]["parameters"]["vf_module_id"] = info_list[1]
            json_msg["stack"]["stack_name"] = stack_name
            json_msg["stack"]["creation_time"] = TIME[path][0]
            json_msg["stack"]["links"][0]["href"] = "http://{}:8004{}".format(addr_str,path)
            json_msg["stack"]["updated_time"] = TIME[path][1]
            json_msg["stack"]["id"] = c_id        
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=UTF-8')
        req_id = "req-{}".format(self.random_id())
        self.send_header('X-Openstack-Request-Id', req_id)
        #self.send_header('Date',self.date_time_string())
        if count == 3:
            json_msg["stack"]["stack_status_reason"] = "Stack CREATE completed successfully"
            json_msg["stack"]["stack_status"] = "CREATE_COMPLETE"
            INFO.pop(stack_name)
            TIME.pop(path)
            to_send = json.dumps(json_msg)
            self.send_header('Content-length', len(to_send))
            self.end_headers()
            self.wfile.write(to_send.encode())
        else:
            to_send = json.dumps(json_msg)
            self.send_header('Content-length', len(to_send))
            self.end_headers()
            self.wfile.write(to_send.encode())

    def get_8774_res(self):
        request_path = self.path
        #print('Recieved a request: {}'.format(request_path))
        if request_path.endswith("b45461e4b03547db8f2869d2c9f9e29e"):
            self.respond_404()
        elif request_path.endswith("detail"):
            self.respond_200_l()
        elif request_path.endswith("v2.1/"):
            self.respond_200_s()
        else:
            print('Wrong format.')

        
    def do_GET(self):
        global APORT
        if APORT == 5000:
            self.get_5000_res()
        elif APORT == 8774:
            self.get_8774_res()
        else:
            request_path = self.path
            urllength = len(request_path)
#            print('Recieved a request: {}'.format(request_path))
#            print("*****************urllength is {}".format(urllength))
#            print(request_path)
            if urllength <= 98:
                self.respond_404_so(request_path)
            else:
                global CLIENTS, TIME
                ret = CLIENTS.get(request_path,0) + 1
                if ret == 1:
                    CLIENTS[request_path] = 1
                    TIME[request_path] = self.gettime()
                elif ret == 2:
                    CLIENTS[request_path] = ret
                else:
                    CLIENTS.pop(request_path)
                self.respond_200(request_path,ret)

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json') 
        #self.send_header('Date',self.date_time_string())
        self.end_headers()
        
    def do_POST(self):
        global APORT,INFO
        if APORT == 5000:
            if self.path == '/v3/auth/tokens':
                self.post_5000_res()
            else:
                self.post_5000_so()
    
        else:
            content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
            post_data = self.rfile.read(content_length)
            jdata = json.loads(post_data.decode())
            name_str = jdata["stack_name"]
            if "vcpe_vgw" in name_str:
                vwg_0 = jdata["parameters"]["vgw_name_0"]
                vwg_1 = jdata["parameters"]["vf_module_id"]
                vwg_2 = jdata["parameters"]["vgw_private_ip_1"]
                vwg_3 = jdata["parameters"]["vgw_private_ip_0"]
                vwg_4 = jdata["parameters"]["vg_vgmux_tunnel_vni"]
                vwg_5 = jdata["parameters"]["vgw_private_ip_2"]
                vwg_6 = jdata["parameters"]["vnf_id"]
                INFO[name_str] = [vwg_0,vwg_1,vwg_2,vwg_3,vwg_4,vwg_5,vwg_6]
            else:
                vwg_0 = jdata["parameters"]["vbrgemu_name_0"]
                vwg_1 = jdata["parameters"]["vf_module_id"]
#               vwg_2 = jdata["parameters"]["vbrgemu_private_ip_0"]
                vwg_3 = jdata["parameters"]["vnf_id"]
#               INFO[name_str] = [vwg_0,vwg_1,vwg_2,vwg_3]
                INFO[name_str] = [vwg_0,vwg_1,vwg_3]
            self.post_8004_res(name_str)


def run(ip_addr = '127.0.0.1'):
    print('http server is starting...')
    global APORT  
    server_address = (ip_addr, APORT)
    httpd = HTTPServer(server_address, MockServer)  
    print("http server {}:{} is running...".format(ip_addr,APORT))  
    try:
        httpd.serve_forever()  
    except KeyboardInterrupt:
        print('Server is shutting down...')

if __name__ == "__main__":
    from sys import argv
    global CLIENTS, TIME, APORT,IP_FLAG, addr_str, INFO
    if len(argv) == 2:
        addr_str = '127.0.0.1'
        IP_FLAG = False
        APORT = int(argv[1])
        CLIENTS = {}
        TIME = {}
        INFO = {}
        run()
    elif len(argv) == 3:
        addr_str = argv[2]
        IP_FLAG = True
        APORT = int(argv[1])
        CLIENTS = {}
        TIME = {}
        INFO = {}
        run(addr_str)
    else:
        print('need to declare port number!')
