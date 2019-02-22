import enum
import json
import logging
from typing import Optional

import requests

logger = logging.getLogger()

RESOURCE_NOT_CREATED = 'ResourceNotCreated'


class Status(enum.Enum):
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'


def send_response(event: dict, context, status: Status, reason: Optional[str] = None,
                  data=None, physical_resource_id: Optional[str] = None,
                  no_echo: bool = False) -> None:
    if data is None:
        data = {}
    logger.debug(f'Try to send Cloudformation response for resource {event["LogicalResourceId"]} '
                 f'in stack {event["StackId"]}. Status is {status.name}')

    response_body = {
        'Status': status.name,
        'Reason': reason or 'See the details in CloudWatch Log Stream: ' + context.log_stream_name,
        'PhysicalResourceId': physical_resource_id or RESOURCE_NOT_CREATED,
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'Data': data,
        'NoEcho': no_echo
    }

    response = requests.put(url=event['ResponseURL'],
                            data=json.dumps(response_body).encode('utf-8'))
    logger.info('CloudFormation response sent. HTTP status was ' + str(response.status_code))
