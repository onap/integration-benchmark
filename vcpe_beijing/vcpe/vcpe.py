#! /usr/bin/python
import sys
import logging
from vcpecommon import *
import soutils
from datetime import datetime
import preload
import vcpe_custom_service
import csar_parser
import config_sdnc_so
import json
import random


def config_sniro(vcpecommon, vgmux_svc_instance_uuid, vbrg_svc_instance_uuid):
    logger = logging.getLogger(__name__)

    logger.info('\n----------------------------------------------------------------------------------')
    logger.info('Start to config SNIRO homing emulator')

    preloader = preload.Preload(vcpecommon)
    template_sniro_data = vcpecommon.find_file('sniro_data', 'json', 'preload_templates')
    template_sniro_request = vcpecommon.find_file('sniro_request', 'json', 'preload_templates')

    vcperescust_csar = vcpecommon.find_file('rescust', 'csar', 'csar')
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
        logger.error('Cannot find all names from %s.', vcperescust_csar)
        sys.exit()

    preloader.preload_sniro(template_sniro_data, template_sniro_request, tunnelxconn_ar_name, vgw_name, brg_ar_name,
                            vgmux_svc_instance_uuid, vbrg_svc_instance_uuid)


def create_one_service(vcpecommon, csar_file, vnf_template_file, preload_dict, suffix, heatbridge=False):
    """
    :return:  service instance UUID
    """
    so = soutils.SoUtils(vcpecommon, 'v4')
    return so.create_entire_service(csar_file, vnf_template_file, preload_dict, suffix, heatbridge)


def deploy_brg_only():
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logger = logging.getLogger(__name__)

    vcpecommon = VcpeCommon()
    preload_dict = vcpecommon.load_preload_data()
#    name_suffix = preload_dict['${brg_bng_net}'].split('_')[-1]
#    name_suffix = datetime.now().strftime('%Y%m%d%H%M')
#    name_suffix = datetime.now().strftime('%Y%m%d%H%M%S')
    name_suffix = datetime.now().strftime('%Y%m%d%H%M%S') + random.randint(1,10000).__str__()
    # create multiple services based on the pre-determined order
    svc_instance_uuid = vcpecommon.load_object(vcpecommon.svc_instance_uuid_file)
    for keyword in ['brg']:
        heatbridge = 'gmux' == keyword
        csar_file = vcpecommon.find_file(keyword, 'csar', 'csar')
        vnf_template_file = vcpecommon.find_file(keyword, 'json', 'preload_templates')
        vcpecommon.increase_ip_address_or_vni_in_template(vnf_template_file, ['vbrgemu_private_ip_0'])
        svc_instance_uuid[keyword] = create_one_service(vcpecommon, csar_file, vnf_template_file, preload_dict,
                                                        name_suffix, heatbridge)
        if not svc_instance_uuid[keyword]:
            sys.exit()

    # Setting up SNIRO
    config_sniro(vcpecommon, svc_instance_uuid['gmux'], svc_instance_uuid['brg'])

    logger.info("vBRG instantiation success!")
    print ('vBRG instantiation success!')


def deploy_infra():
    logger = logging.getLogger(__name__)

    vcpecommon = VcpeCommon()

    # preload all networks
    network_template = vcpecommon.find_file('network', 'json', 'preload_templates')
#    name_suffix = datetime.now().strftime('%Y%m%d%H%M')
    name_suffix = datetime.now().strftime('%Y%m%d%H%M%S') + random.randint(1,10000).__str__()
    preloader = preload.Preload(vcpecommon)
    preload_dict = preloader.preload_all_networks(network_template, name_suffix)
    logger.debug('Initial preload dictionary:')
    logger.debug(json.dumps(preload_dict, indent=4, sort_keys=True))
    if not preload_dict:
        logger.error("Failed to preload networks.")
        sys.exit()
    vcpecommon.save_preload_data(preload_dict)

    # create multiple services based on the pre-determined order
    svc_instance_uuid = {}
    for keyword in ['infra', 'bng', 'gmux', 'brg']:
        heatbridge = 'gmux' == keyword
        csar_file = vcpecommon.find_file(keyword, 'csar', 'csar')
        vnf_template_file = vcpecommon.find_file(keyword, 'json', 'preload_templates')
        svc_instance_uuid[keyword] = create_one_service(vcpecommon, csar_file, vnf_template_file, preload_dict,
                                                        name_suffix, heatbridge)
        if not svc_instance_uuid[keyword]:
            sys.exit()

    vcpecommon.save_object(svc_instance_uuid, vcpecommon.svc_instance_uuid_file)
    # Setting up SNIRO
    config_sniro(vcpecommon, svc_instance_uuid['gmux'], svc_instance_uuid['brg'])

    print('----------------------------------------------------------------------------------------------------')
    print('Congratulations! The following have been completed correctly:')
    print(' - Infrastructure Service Instantiation: ')
    print('     * 4 VMs:      DHCP, AAA, DNS, Web Server')
    print('     * 2 Networks: CPE_PUBLIC, CPE_SIGNAL')
    print(' - vBNG Service Instantiation: ')
    print('     * 1 VM:       vBNG')
    print('     * 2 Networks: BRG_BNG, BNG_MUX')
    print(' - vGMUX Service Instantiation: ')
    print('     * 1 VM:       vGMUX')
    print('     * 1 Network:  MUX_GW')
    print(' - vBRG Service Instantiation: ')
    print('     * 1 VM:       vBRG')
    print(' - Adding vGMUX vServer information to AAI.')
    print(' - SNIRO Homing Emulator configuration.')


def deploy_custom_service():
    nodes = ['brg', 'mux']
    vcpecommon = VcpeCommon(nodes)
    custom_service = vcpe_custom_service.CustomService(vcpecommon)

    # clean up
    host_dic = {k: vcpecommon.hosts[k] for k in nodes}
    if True:
        if not vcpecommon.delete_vxlan_interfaces(host_dic):
            sys.exit()
        custom_service.del_all_vgw_stacks(vcpecommon.vgw_name_keyword)

    custom_service.clean_up_sdnc()

    # create new service
    csar_file = vcpecommon.find_file('rescust', 'csar', 'csar')
    vgw_template_file = vcpecommon.find_file('vgw', 'json', 'preload_templates')
    preload_dict = vcpecommon.load_preload_data()
    custom_service.create_custom_service(csar_file, vgw_template_file, preload_dict)


def closed_loop(lossrate=0):
    if lossrate > 0:
        while 'y' != raw_input('Please enter docker container "drools" in Policy VM and type "policy stop". Then enter y here: ').lower():
            continue
    nodes = ['brg', 'mux']
    logger = logging.getLogger('__name__')
    vcpecommon = VcpeCommon(nodes)
    logger.info('Cleaning up vGMUX data reporting settings')
    vcpecommon.del_vgmux_ves_mode()
    time.sleep(2)
    vcpecommon.del_vgmux_ves_collector()

    logger.info('Staring vGMUX data reporting to DCAE')
    time.sleep(2)
    vcpecommon.set_vgmux_ves_collector()

    logger.info('Setting vGMUX to report packet loss rate: %s', lossrate)
    time.sleep(2)
    vcpecommon.set_vgmux_packet_loss_rate(lossrate, vcpecommon.load_vgmux_vnf_name())
    if lossrate > 0:
        print('Please enter docker container "drools" in Policy VM and type "policy start". Then observe vGMUX being restarted.')


def init_so_sdnc():
    logger = logging.getLogger('__name__')
    vcpecommon = VcpeCommon()
    config_sdnc_so.insert_customer_service_to_so(vcpecommon)
    config_sdnc_so.insert_customer_service_to_sdnc(vcpecommon)


def tmp_sniro():
    logger = logging.getLogger(__name__)

    vcpecommon = VcpeCommon()

    svc_instance_uuid = vcpecommon.load_object(vcpecommon.svc_instance_uuid_file)
    # Setting up SNIRO
    config_sniro(vcpecommon, svc_instance_uuid['gmux'], svc_instance_uuid['brg'])

if __name__ == '__main__':
    #logging.basicConfig(level=logging.INFO, format='%(message)s')
    #logging.basicConfig(level=logging.ERROR, format='%(message)s')
    fmt = '%(asctime)s : %(message)s'
    logging.basicConfig(level=logging.INFO, format=fmt, filename='brg_only.log')
    console = logging.StreamHandler()
    console.setLevel(logging.ERROR)
    console.setFormatter(logging.Formatter(fmt))
    logging.getLogger().addHandler(console)

    print('----------------------------------------------------------------------------------------------------')
    print(' vcpe.py:            Brief info about this program')
#    print(' vcpe.py sdc:        Onboard VNFs, design and distribute vCPE services (under development)')
    print(' vcpe.py init:       Add customer service data to SDNC and SO DBs.')
    print(' vcpe.py infra:      Deploy infrastructure, including DHCP, AAA, DNS, Web Server, vBNG, vGMUX, vBRG.')
    print(' vcpe.py customer:   Deploy customer service, including vGW and VxLANs')
    print(' vcpe.py loop:       Test closed loop control')
    print('----------------------------------------------------------------------------------------------------')

    if len(sys.argv) != 2:
        sys.exit()

    if sys.argv[1] == 'sdc':
        print('Under development')
    elif sys.argv[1] == 'init':
        if 'y' == raw_input('Ready to add customer service data to SDNC and SO DBs? This is needed only once.'
                            'y/n: ').lower():
            init_so_sdnc()
    elif sys.argv[1] == 'infra':
        if 'y' == raw_input('Ready to deploy infrastructure? y/n: ').lower():
            deploy_infra()
    elif sys.argv[1] == 'customer':
        if 'y' == raw_input('Ready to deploy customer service? y/n: ').lower():
            deploy_custom_service()
    elif sys.argv[1] == 'loop':
        closed_loop(22)
    elif sys.argv[1] == 'noloss':
        closed_loop(0)
    elif sys.argv[1] == 'brg':
        deploy_brg_only()

