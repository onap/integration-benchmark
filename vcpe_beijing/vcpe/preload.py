#! /usr/bin/python

import requests
import json
import sys
from datetime import datetime
from vcpecommon import *
import csar_parser
import logging
import base64


class Preload:
    def __init__(self, vcpecommon):
        self.logger = logging.getLogger(__name__)
        self.vcpecommon = vcpecommon

    def replace(self, sz, replace_dict):
        for old_string, new_string in replace_dict.items():
            sz = sz.replace(old_string, new_string)
        if self.vcpecommon.template_variable_symbol in sz:
            self.logger.error('Error! Cannot find a value to replace ' + sz)
        return sz

    def generate_json(self, template_file, replace_dict):
        with open(template_file) as json_input:
            json_data = json.load(json_input)
            stk = [json_data]
            while len(stk) > 0:
                data = stk.pop()
                for k, v in data.items():
                    if type(v) is dict:
                        stk.append(v)
                    elif type(v) is list:
                        stk.extend(v)
                    elif type(v) is str or type(v) is unicode:
                        if self.vcpecommon.template_variable_symbol in v:
                            data[k] = self.replace(v, replace_dict)
                    else:
                        self.logger.warning('Unexpected line in template: %s. Look for value %s', template_file, v)
        return json_data

    def reset_sniro(self):
        self.logger.debug('Clearing SNIRO data')
        r = requests.post(self.vcpecommon.sniro_url + '/reset', headers=self.vcpecommon.sniro_headers)
        if 2 != r.status_code / 100:
            self.logger.debug(r.content)
            self.logger.error('Clearing SNIRO date failed.')
            sys.exit()

    def preload_sniro(self, template_sniro_data, template_sniro_request, tunnelxconn_ar_name, vgw_name, vbrg_ar_name,
                      vgmux_svc_instance_uuid, vbrg_svc_instance_uuid):
        self.reset_sniro()
        self.logger.info('Preloading SNIRO for homing service')
        replace_dict = {'${tunnelxconn_ar_name}': tunnelxconn_ar_name,
                        '${vgw_name}': vgw_name,
                        '${brg_ar_name}': vbrg_ar_name,
                        '${vgmux_svc_instance_uuid}': vgmux_svc_instance_uuid,
                        '${vbrg_svc_instance_uuid}': vbrg_svc_instance_uuid
                        }
        sniro_data = self.generate_json(template_sniro_data, replace_dict)
        self.logger.debug('SNIRO data:')
        self.logger.debug(json.dumps(sniro_data, indent=4, sort_keys=True))

        base64_sniro_data = base64.b64encode(json.dumps(sniro_data))
        self.logger.debug('SNIRO data: 64')
        self.logger.debug(base64_sniro_data)
        replace_dict = {'${base64_sniro_data}': base64_sniro_data, '${sniro_ip}': self.vcpecommon.hosts['robot']}
        sniro_request = self.generate_json(template_sniro_request, replace_dict)
        self.logger.debug('SNIRO request:')
        self.logger.debug(json.dumps(sniro_request, indent=4, sort_keys=True))

        r = requests.post(self.vcpecommon.sniro_url, headers=self.vcpecommon.sniro_headers, json=sniro_request)
        if 2 != r.status_code / 100:
            response = r.json()
            self.logger.debug(json.dumps(response, indent=4, sort_keys=True))
            self.logger.error('SNIRO preloading failed.')
            sys.exit()

        return True

    def preload_network(self, template_file, network_role, subnet_start_ip, subnet_gateway, common_dict, name_suffix):
        """
        :param template_file:
        :param network_role: cpe_signal, cpe_public, brg_bng, bng_mux, mux_gw
        :param subnet_start_ip:
        :param subnet_gateway:
        :param name_suffix: e.g. '201711201311'
        :return:
        """
        network_name = '_'.join([self.vcpecommon.instance_name_prefix['network'], network_role.lower(), name_suffix])
        subnet_name = self.vcpecommon.network_name_to_subnet_name(network_name)
        common_dict['${' + network_role+'_net}'] = network_name
        common_dict['${' + network_role+'_subnet}'] = subnet_name
        replace_dict = {'${network_role}': network_role,
                        '${service_type}': 'vCPE',
                        '${network_type}': 'Generic NeutronNet',
                        '${network_name}': network_name,
                        '${subnet_start_ip}': subnet_start_ip,
                        '${subnet_gateway}': subnet_gateway
                        }
        self.logger.info('Preloading network ' + network_role)
        return self.preload(template_file, replace_dict, self.vcpecommon.sdnc_preload_network_url)

    def preload(self, template_file, replace_dict, url):
        json_data = self.generate_json(template_file, replace_dict)
        self.logger.debug(json.dumps(json_data, indent=4, sort_keys=True))
        r = requests.post(url, headers=self.vcpecommon.sdnc_headers, auth=self.vcpecommon.sdnc_userpass, json=json_data)
        response = r.json()

	self.logger.info('response from requests.post() in preload() is: ')
	self.logger.info(json.dumps(response, indent=4, sort_keys=True))

        if int(response.get('output', {}).get('response-code', 0)) != 200:
            self.logger.debug(json.dumps(response, indent=4, sort_keys=True))
            self.logger.error('Preloading failed.')
            return False
        return True

    def preload_vgw(self, template_file, brg_mac, commont_dict, name_suffix):
        replace_dict = {'${brg_mac}': brg_mac,
                        '${suffix}': name_suffix
                        }
        replace_dict.update(commont_dict)
        self.logger.info('Preloading vGW')
        return self.preload(template_file, replace_dict, self.vcpecommon.sdnc_preload_vnf_url)

    def preload_vfmodule(self, template_file, service_instance_id, vnf_model, vfmodule_model, common_dict, name_suffix):
        """
        :param template_file:
        :param service_instance_id:
        :param vnf_model:  parsing results from csar_parser
        :param vfmodule_model:  parsing results from csar_parser
        :param common_dict:
        :param name_suffix:
        :return:
        """

        # examples:
        # vfmodule_model['modelCustomizationName']: "Vspinfra111601..base_vcpe_infra..module-0",
        # vnf_model['modelCustomizationName']: "vspinfra111601 0",

        vfmodule_name = '_'.join([self.vcpecommon.instance_name_prefix['vfmodule'],
                                  vfmodule_model['modelCustomizationName'].split('..')[0].lower(), name_suffix])

        # vnf_type and generic_vnf_type are identical
        replace_dict = {'${vnf_type}': vfmodule_model['modelCustomizationName'],
                        '${generic_vnf_type}': vfmodule_model['modelCustomizationName'],
                        '${service_type}': service_instance_id,
                        '${generic_vnf_name}': vnf_model['modelCustomizationName'],
                        '${vnf_name}': vfmodule_name,
                        '${suffix}': name_suffix}
        replace_dict.update(common_dict)
        self.logger.info('Preloading VF Module ' + vfmodule_name)
        return self.preload(template_file, replace_dict, self.vcpecommon.sdnc_preload_vnf_url)

    def preload_all_networks(self, template_file, name_suffix):
        common_dict = {'${' + k + '}': v for k, v in self.vcpecommon.common_preload_config.items()}
        for network, v in self.vcpecommon.preload_network_config.items():
            subnet_start_ip, subnet_gateway_ip = v
            if not self.preload_network(template_file, network, subnet_start_ip, subnet_gateway_ip,
                                        common_dict, name_suffix):
                return None
        return common_dict

    def test(self):
        # this is for testing purpose
        name_suffix = datetime.now().strftime('%Y%m%d%H%M')
        vcpecommon = VcpeCommon()
        preloader = Preload(vcpecommon)

        network_dict = {'${' + k + '}': v for k, v in self.vcpecommon.common_preload_config.items()}
        template_file = 'preload_templates/template.network.json'
        for k, v in self.vcpecommon.preload_network_config.items():
            if not preloader.preload_network(template_file, k, v[0], v[1], network_dict, name_suffix):
                break

        print('---------------------------------------------------------------')
        print('Network related replacement dictionary:')
        print(json.dumps(network_dict, indent=4, sort_keys=True))
        print('---------------------------------------------------------------')

        keys = ['infra', 'bng', 'gmux', 'brg']
        for key in keys:
            csar_file = self.vcpecommon.find_file(key, 'csar', 'csar')
            template_file = self.vcpecommon.find_file(key, 'json', 'preload_templates')
            if csar_file and template_file:
                parser = csar_parser.CsarParser()
                parser.parse_csar(csar_file)
                service_instance_id = 'test112233'
                preloader.preload_vfmodule(template_file, service_instance_id, parser.vnf_models[0],
                                           parser.vfmodule_models[0], network_dict, name_suffix)

    def test_sniro(self):
        template_sniro_data = self.vcpecommon.find_file('sniro_data', 'json', 'preload_templates')
        template_sniro_request = self.vcpecommon.find_file('sniro_request', 'json', 'preload_templates')

        vcperescust_csar = self.vcpecommon.find_file('rescust', 'csar', 'csar')
        parser = csar_parser.CsarParser()
        parser.parse_csar(vcperescust_csar)
        tunnelxconn_ar_name = None
        brg_ar_name = None
        vgw_name = None
        for model in parser.vnf_models:
            if 'tunnel' in model['modelCustomizationName']:
                tunnelxconn_ar_name = model['modelCustomizationName']
            elif 'brg' in model['modelCustomizationName']:
                brg_ar_name = model['modelCustomizationName']
            elif 'vgw' in model['modelCustomizationName']:
                vgw_name = model['modelCustomizationName']

        if not (tunnelxconn_ar_name and brg_ar_name and vgw_name):
            self.logger.error('Cannot find all names from %s.', vcperescust_csar)
            sys.exit()

        vgmux_svc_instance_uuid = '88888888888888'
        vbrg_svc_instance_uuid = '999999999999999'

        self.preload_sniro(template_sniro_data, template_sniro_request, tunnelxconn_ar_name, vgw_name, brg_ar_name,
                           vgmux_svc_instance_uuid, vbrg_svc_instance_uuid)
