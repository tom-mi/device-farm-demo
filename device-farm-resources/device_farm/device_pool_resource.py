from typing import Optional

import boto3
import traceback

from botocore.client import BaseClient

from . import cloudformation

KNOWN_PROPERTIES = {'Name', 'Rules', 'ProjectArn', 'Description', 'MaxDevices', 'ServiceToken'}


def lambda_handler(event: dict, context):
    print(event)
    physical_resource_id = event.get('PhysicalResourceId')
    project_arn = event.get('ResourceProperties', {}).get('ProjectArn', None)
    name = event.get('ResourceProperties', {}).get('Name', None)
    rules = event.get('ResourceProperties', {}).get('Rules', None)
    description = event.get('ResourceProperties', {}).get('Description', None)
    max_devices = event.get('ResourceProperties', {}).get('MaxDevices', None)
    extra_properties = set(event.get('ResourceProperties', {}).keys()).difference(KNOWN_PROPERTIES)

    def send_error(reason):
        cloudformation.send_response(
            event=event,
            context=context,
            status=cloudformation.Status.FAILED,
            reason=reason,
            physical_resource_id=cloudformation.RESOURCE_NOT_CREATED
        )

    def send_missing_property_response(property_name: str):
        send_error(f'Required property {property_name} not set')

    try:
        if not project_arn:
            send_missing_property_response('ProjectArn')
        elif not name:
            send_missing_property_response('Name')
        elif not rules:
            send_missing_property_response('Rules')
        elif extra_properties:
            send_error(f'Unknown properties found: {", ".join(extra_properties)}')
        else:
            if event['RequestType'] == 'Delete' and physical_resource_id == cloudformation.RESOURCE_NOT_CREATED:
                cloudformation.send_response(
                    event=event, context=context,
                    status=cloudformation.Status.SUCCESS,
                    physical_resource_id=physical_resource_id
                )
            else:
                if event['RequestType'] == 'Delete':
                    client = _get_device_farm_client()
                    client.delete_device_pool(arn=physical_resource_id)
                elif event['RequestType'] == 'Create':
                    client = _get_device_farm_client()
                    params = {
                        'projectArn': project_arn,
                        'name': name,
                        'rules': rules,
                    }
                    if description is not None:
                        params['description'] = description
                    if max_devices is not None:
                        params['maxDevices'] = max_devices
                    response = client.create_device_pool(**params)
                    physical_resource_id = response['devicePool']['arn']
                elif event['RequestType'] == 'Update':
                    client = _get_device_farm_client()
                    params = {
                        'arn': physical_resource_id,
                        'projectArn': project_arn,
                        'name': name,
                        'rules': rules,
                    }
                    if max_devices is not None:
                        params['maxDevices'] = max_devices
                    else:
                        params['clearMaxDevices'] = True
                    if description is not None:
                        params['description'] = description
                    client.update_device_pool(**params)
                else:
                    raise ValueError('Unknown RequestType ' + event['RequestType'])

                cloudformation.send_response(
                    event=event, context=context,
                    status=cloudformation.Status.SUCCESS,
                    physical_resource_id=physical_resource_id,
                    data={
                        'Arn': physical_resource_id,
                    },
                )

    except Exception as e:
        print(e)
        traceback.print_exc()
        physical_resource_id = physical_resource_id or cloudformation.RESOURCE_NOT_CREATED
        cloudformation.send_response(
            event=event,
            context=context,
            status=cloudformation.Status.FAILED,
            reason=str(e),
            physical_resource_id=physical_resource_id,
        )

    print('Finished')
    return 'ok'


def get_top_device_pool_arn(client: BaseClient, project_arn: str) -> Optional[str]:
    paginator = client.get_paginator('list_device_pools')
    for page in paginator.paginate(arn=project_arn, type='CURATED'):
        for device_pool in page['devicePools']:
            if device_pool['name'] == 'Top Devices':
                return device_pool['arn']
    print('Top Devices device pool not found')
    return None


def get_project_id(project_arn: str) -> str:
    arn_parts = project_arn.split(':')
    return arn_parts[-1]


def _get_device_farm_client() -> BaseClient:
    return boto3.client('devicefarm', region_name='us-west-2')
