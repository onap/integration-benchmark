#! /usr/bin/python

import logging
from vcpecommon import *
import csar_parser


def insert_customer_service_to_sdnc(vcpecommon):
    """
    INSERT INTO SERVICE_MODEL (`service_uuid`, `model_yaml`,`invariant_uuid`,`version`,`name`,`description`,`type`,`category`,`ecomp_naming`,`service_instance_name_prefix`,`filename`,`naming_policy`) values ('7e319b6f-e710-440e-bbd2-63c1004949ef', null, 'a99ace8a-6e3b-447d-b2ff-4614e4234eea',null,'vCPEService', 'vCPEService', 'Service','Network L1-3', 'N', 'vCPEService', 'vCpeResCust110701/service-Vcperescust110701-template.yml',null);
    INSERT INTO ALLOTTED_RESOURCE_MODEL (`customization_uuid`,`model_yaml`,`invariant_uuid`,`uuid`,`version`,`naming_policy`,`ecomp_generated_naming`,`depending_service`,`role`,`type`,`service_dependency`,`allotted_resource_type`)  VALUES ( '7e40b664-d7bf-47ad-8f7c-615631d53cd7', NULL,  'f51b0aae-e24a-4cff-b190-fe3daf3d15ee', 'f3137496-1605-40e9-b6df-64aa0f8e91a0', '1.0', NULL,'Y',NULL,NULL,'TunnelXConnect',NULL, 'TunnelXConnect');
    INSERT INTO ALLOTTED_RESOURCE_MODEL (`customization_uuid`,`model_yaml`,`invariant_uuid`,`uuid`,`version`,`naming_policy`,`ecomp_generated_naming`,`depending_service`,`role`,`type`,`service_dependency`,`allotted_resource_type`)  VALUES ( 'e46097e1-6a0c-4cf3-a7e5-c39ed407e65e', NULL,  'aa60f6ba-541b-48d6-a5ff-3b0e1f0ad9bf', '0e157d52-b945-422f-b3a8-ab685c2be079', '1.0', NULL,'Y',NULL,NULL,'BRG',NULL, 'TunnelXConnect');
    INSERT INTO VF_MODEL (`customization_uuid`,`model_yaml`,`invariant_uuid`,`uuid`,`version`,`name`,`naming_policy`,`ecomp_generated_naming`,`avail_zone_max_count`,`nf_function`,`nf_code`,`nf_type`,`nf_role`,`vendor`,`vendor_version`)  VALUES ( '3768afa5-cf9e-4071-bb25-3a2e2628dd87', NULL,  '5f56893b-d026-4672-b785-7f5ffeb498c6', '7cf28b23-5719-485b-9ab4-dae1a2fa0e07', '1.0', 'vspvgw111601',NULL,'Y',1,NULL,NULL,NULL,NULL,'vCPE','1.0');
    INSERT INTO VF_MODULE_MODEL (`customization_uuid`,`model_yaml`,`invariant_uuid`,`uuid`,`version`,`vf_module_type`,`availability_zone_count`,`ecomp_generated_vm_assignments`)  VALUES ( '17a9c7d1-6f8e-4930-aa83-0d323585184f', NULL,  'd772ddd1-7623-40b4-a2a5-ec287916cb51', '6e1a0652-f5e9-4caa-bff8-39bf0c8589a3', '1.0', 'Base',NULL,NULL);

    :return:
    """
    logger = logging.getLogger('__name__')
    logger.info('Inserting customer service data to SDNC DB')
    csar_file = vcpecommon.find_file('rescust', 'csar', 'csar')
    parser = csar_parser.CsarParser()
    parser.parse_csar(csar_file)
    cmds = []

    #if False:
    if True:
        cmds.append("INSERT INTO SERVICE_MODEL (`service_uuid`, `model_yaml`,`invariant_uuid`,`version`,`name`," \
                "`description`,`type`,`category`,`ecomp_naming`,`service_instance_name_prefix`,`filename`," \
                "`naming_policy`) values ('{0}', null, '{1}',null,'{2}', 'vCPEService', 'Service','Network L1-3'," \
                "'N', 'vCPEService', '{3}/{4}',null);".format(parser.svc_model['modelVersionId'],
                                                              parser.svc_model['modelInvariantId'],
                                                              parser.svc_model['modelName'],
                                                              parser.svc_model['modelName'],
                                                              parser.svc_model['modelName']))

    for model in parser.vnf_models:
        if 'tunnel' in model['modelCustomizationName'].lower() or 'brg' in model['modelCustomizationName'].lower():
            if True:
                cmds.append("INSERT INTO ALLOTTED_RESOURCE_MODEL (`customization_uuid`,`model_yaml`,`invariant_uuid`," \
                        "`uuid`,`version`,`naming_policy`,`ecomp_generated_naming`,`depending_service`,`role`,`type`," \
                        "`service_dependency`,`allotted_resource_type`) VALUES ('{0}',NULL,'{1}','{2}','1.0'," \
                        "NULL,'Y', NULL,NULL,'TunnelXConnect'," \
                        "NULL, 'TunnelXConnect');".format(model['modelCustomizationId'], model['modelInvariantId'],
                                                          model['modelVersionId']))
            cmds.append("UPDATE ALLOTTED_RESOURCE_MODEL SET `ecomp_generated_naming`='Y' " \
                    "WHERE `customization_uuid`='{0}'".format(model['modelCustomizationId']))
        else:
            if True:
                cmds.append("INSERT INTO VF_MODEL (`customization_uuid`,`model_yaml`,`invariant_uuid`,`uuid`,`version`," \
                        "`name`,`naming_policy`,`ecomp_generated_naming`,`avail_zone_max_count`,`nf_function`," \
                        "`nf_code`,`nf_type`,`nf_role`,`vendor`,`vendor_version`) VALUES ('{0}',NULL,'{1}','{2}'," \
                        "'1.0', '{3}',NULL,'Y',1,NULL,NULL,NULL,NULL,'vCPE'," \
                        "'1.0');".format(model['modelCustomizationId'], model['modelInvariantId'],
                                         model['modelVersionId'], model['modelCustomizationName'].split()[0]))
            cmds.append("UPDATE VF_MODEL SET `ecomp_generated_naming`='Y' " \
                        "WHERE `customization_uuid`='{0}'".format(model['modelCustomizationId']))

    if True:
        model = parser.vfmodule_models[0]
        cmds.append("INSERT INTO VF_MODULE_MODEL (`customization_uuid`,`model_yaml`,`invariant_uuid`,`uuid`,`version`," \
                    "`vf_module_type`,`availability_zone_count`,`ecomp_generated_vm_assignments`) VALUES ('{0}', NULL," \
                    "'{1}', '{2}', '1.0', 'Base',NULL,NULL)" \
                    ";".format(model['modelCustomizationId'], model['modelInvariantId'], model['modelVersionId']))

    print('\n'.join(cmds))
    vcpecommon.execute_cmds_sdnc_db(cmds)


def insert_customer_service_to_so(vcpecommon):
    logger = logging.getLogger('__name__')
    logger.info('Inserting neutron HEAT template to SO DB and creating a recipe for customer service')
    cmds = []
    #if False:
    if True:
        csar_file = vcpecommon.find_file('rescust', 'csar', 'csar')
        parser = csar_parser.CsarParser()
        parser.parse_csar(csar_file)
        cmds.append("INSERT INTO `service_recipe` (`ACTION`, `VERSION_STR`, `DESCRIPTION`, `ORCHESTRATION_URI`, " \
                    "`SERVICE_PARAM_XSD`, `RECIPE_TIMEOUT`, `SERVICE_TIMEOUT_INTERIM`, `CREATION_TIMESTAMP`, " \
                    "`SERVICE_MODEL_UUID`) VALUES ('createInstance','1','{0}'," \
                    "'/mso/async/services/CreateVcpeResCustService',NULL,181,NULL, NOW()," \
                    "'{1}');".format(parser.svc_model['modelName'], parser.svc_model['modelVersionId']))

    cmds.append("delete from `heat_template_params` where"
                "`HEAT_TEMPLATE_ARTIFACT_UUID`='efee1d84-b8ec-11e7-abc4-cec278b6b50a';")
    cmds.append("delete from `heat_template` where ARTIFACT_UUID='efee1d84-b8ec-11e7-abc4-cec278b6b50a';")
    network_tempalte_file = vcpecommon.find_file('neutron', 'yaml', 'preload_templates')
    with open(network_tempalte_file, 'r') as fin:
        lines = fin.readlines()
        longtext = '\n'.join(lines)
        cmds.append("INSERT INTO `heat_template`(`ARTIFACT_UUID`, `NAME`, `VERSION`, `BODY`, `TIMEOUT_MINUTES`, " \
                    "`DESCRIPTION`, `CREATION_TIMESTAMP`, `ARTIFACT_CHECKSUM`) VALUES(" \
                    "'efee1d84-b8ec-11e7-abc4-cec278b6b50a', 'Generic NeutronNet', '1', '{0}', 10, " \
                    "'Generic Neutron Template', NOW(), 'MANUAL RECORD');".format(longtext))

    cmds.append("INSERT INTO `heat_template_params`(`HEAT_TEMPLATE_ARTIFACT_UUID`, `PARAM_NAME`, `IS_REQUIRED`, " \
                "`PARAM_TYPE`, `PARAM_ALIAS`) VALUES('efee1d84-b8ec-11e7-abc4-cec278b6b50a', 'shared', 0, " \
                "'string', NULL);")

    print('\n'.join(cmds))
    vcpecommon.execute_cmds_so_db(cmds)

