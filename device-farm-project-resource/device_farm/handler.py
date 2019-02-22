import boto3
import traceback
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

                cloudformation.send_response(
                    event=event, context=context,
                    status=cloudformation.Status.SUCCESS,
                    physical_resource_id=physical_resource_id
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
            physical_resource_id=physical_resource_id
        )

    print('Finished')
    return 'ok'


def _get_device_farm_client():
    return boto3.client('devicefarm', region_name='us-west-2')
