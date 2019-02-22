from typing import Optional

import boto3
import traceback

from botocore.client import BaseClient

from . import cloudformation


def lambda_handler(event: dict, context):
    print(event)
    physical_resource_id = event.get('PhysicalResourceId')
    project_name = event.get('ResourceProperties', {}).get('ProjectName', None)

    try:
        if not project_name:
            cloudformation.send_response(
                event=event,
                context=context,
                status=cloudformation.Status.FAILED,
                reason='ProjectName is not set',
                physical_resource_id=cloudformation.RESOURCE_NOT_CREATED
            )
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
                    client.delete_project(arn=physical_resource_id)
                elif event['RequestType'] == 'Create':
                    client = _get_device_farm_client()
                    response = client.create_project(name=project_name)
                    physical_resource_id = response['project']['arn']
                elif event['RequestType'] == 'Update':
                    client = _get_device_farm_client()
                    client.update_project(arn=physical_resource_id, name=project_name)
                else:
                    raise ValueError('Unknown RequestType ' + event['RequestType'])

                top_devices_device_pool_arn = get_top_device_pool_arn(client, physical_resource_id)
                cloudformation.send_response(
                    event=event, context=context,
                    status=cloudformation.Status.SUCCESS,
                    physical_resource_id=physical_resource_id,
                    data={
                        'Arn': physical_resource_id,
                        'ProjectId': get_project_id(physical_resource_id),
                        'TopDevicesDevicePoolArn': top_devices_device_pool_arn,
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
