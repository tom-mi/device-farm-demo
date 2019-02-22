from datetime import datetime

import pytest
from unittest.mock import MagicMock
from requests_mock import Mocker

from device_farm import handler

TEST_PROJECT_NAME = 'project-name'
TEST_RESPONSE_URL = 'http://example.com/response'
TEST_PHYSICAL_RESOURCE_ID = '1235'


@pytest.fixture
def context():
    mock = MagicMock()
    mock.log_stream_name = 'stream'
    return mock


@pytest.fixture
def cf_endpoint(requests_mock: Mocker):
    requests_mock.put(TEST_RESPONSE_URL)
    return requests_mock


@pytest.fixture
def device_farm_endpoint(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr('boto3.client', MagicMock(return_value=mock))
    mock.create_project = MagicMock(return_value={
        'project': {
            'arn': TEST_PHYSICAL_RESOURCE_ID,
            'name': TEST_PROJECT_NAME,
            'defaultJobTimeoutMinutes': 123,
            'created': datetime.now(),
        },
    })
    return mock


def test_handler_create_missing_parameter(context, cf_endpoint, device_farm_endpoint):
    event = {
        'RequestType': 'Create',
        'LogicalResourceId': 'DeviceFarm',
        'RequestId': '1234',
        'ResponseURL': TEST_RESPONSE_URL,
        'StackId': 'arn:aws:cloudformation:us-east-2:namespace:stack/stack-name/guid',
        'ResourceProperties': {
        }
    }

    handler.lambda_handler(event, context)

    assert cf_endpoint.called
    assert len(cf_endpoint.request_history) == 1
    assert cf_endpoint.request_history[0].json()['PhysicalResourceId'] == 'ResourceNotCreated'
    assert cf_endpoint.request_history[0].json()['Status'] == 'FAILED'
    device_farm_endpoint.create_project.assert_not_called()
    device_farm_endpoint.update_project.assert_not_called()

def test_handler_create(context, cf_endpoint, device_farm_endpoint):
    event = {
        'RequestType': 'Create',
        'LogicalResourceId': 'DeviceFarm',
        'RequestId': '1234',
        'ResponseURL': TEST_RESPONSE_URL,
        'StackId': 'arn:aws:cloudformation:us-east-2:namespace:stack/stack-name/guid',
        'ResourceProperties': {
            'ProjectName': TEST_PROJECT_NAME,
        }
    }

    handler.lambda_handler(event, context)

    assert cf_endpoint.called
    assert len(cf_endpoint.request_history) == 1
    assert cf_endpoint.request_history[0].json()['PhysicalResourceId'] == TEST_PHYSICAL_RESOURCE_ID
    assert cf_endpoint.request_history[0].json()['Status'] == 'SUCCESS'
    device_farm_endpoint.create_project.assert_called_with(name=TEST_PROJECT_NAME)
    device_farm_endpoint.update_project.assert_not_called()


def test_handler_create_fails(context, cf_endpoint, device_farm_endpoint):
    event = {
        'RequestType': 'Create',
        'LogicalResourceId': 'DeviceFarm',
        'RequestId': '1234',
        'ResponseURL': TEST_RESPONSE_URL,
        'StackId': 'arn:aws:cloudformation:us-east-2:namespace:stack/stack-name/guid',
        'ResourceProperties': {
            'ProjectName': TEST_PROJECT_NAME,
        }
    }
    device_farm_endpoint.create_project = MagicMock(side_effect=Exception('This went wrong'))

    handler.lambda_handler(event, context)

    assert cf_endpoint.called
    assert len(cf_endpoint.request_history) == 1
    assert cf_endpoint.request_history[0].json()['PhysicalResourceId'] == 'ResourceNotCreated'
    assert cf_endpoint.request_history[0].json()['Status'] == 'FAILED'
    device_farm_endpoint.create_project.assert_called_with(name=TEST_PROJECT_NAME)
    device_farm_endpoint.update_project.assert_not_called()


def test_handler_update(context, cf_endpoint, device_farm_endpoint):
    event = {
        'RequestType': 'Update',
        'LogicalResourceId': 'DeviceFarm',
        'PhysicalResourceId': TEST_PHYSICAL_RESOURCE_ID,
        'RequestId': '1234',
        'ResponseURL': TEST_RESPONSE_URL,
        'StackId': 'arn:aws:cloudformation:us-east-2:namespace:stack/stack-name/guid',
        'ResourceProperties': {
            'ProjectName': TEST_PROJECT_NAME,
        }
    }

    handler.lambda_handler(event, context)

    assert cf_endpoint.called
    assert len(cf_endpoint.request_history) == 1
    assert cf_endpoint.request_history[0].json()['PhysicalResourceId'] == TEST_PHYSICAL_RESOURCE_ID
    assert cf_endpoint.request_history[0].json()['Status'] == 'SUCCESS'
    device_farm_endpoint.create_project.assert_not_called()
    device_farm_endpoint.update_project.assert_called_with(arn=TEST_PHYSICAL_RESOURCE_ID, name=TEST_PROJECT_NAME)


def test_handler_update_fails(context, cf_endpoint, device_farm_endpoint):
    event = {
        'RequestType': 'Update',
        'LogicalResourceId': 'DeviceFarm',
        'PhysicalResourceId': TEST_PHYSICAL_RESOURCE_ID,
        'RequestId': '1234',
        'ResponseURL': TEST_RESPONSE_URL,
        'StackId': 'arn:aws:cloudformation:us-east-2:namespace:stack/stack-name/guid',
        'ResourceProperties': {
            'ProjectName': TEST_PROJECT_NAME,
        }
    }
    device_farm_endpoint.update_project = MagicMock(side_effect=Exception('This went wrong'))

    handler.lambda_handler(event, context)

    assert cf_endpoint.called
    assert len(cf_endpoint.request_history) == 1
    assert cf_endpoint.request_history[0].json()['PhysicalResourceId'] == TEST_PHYSICAL_RESOURCE_ID
    assert cf_endpoint.request_history[0].json()['Status'] == 'FAILED'
    device_farm_endpoint.create_project.assert_not_called()
    device_farm_endpoint.update_project.assert_called_with(arn=TEST_PHYSICAL_RESOURCE_ID, name=TEST_PROJECT_NAME)


def test_handler_delete(context, cf_endpoint, device_farm_endpoint):
    event = {
        'RequestType': 'Delete',
        'LogicalResourceId': 'DeviceFarm',
        'PhysicalResourceId': TEST_PHYSICAL_RESOURCE_ID,
        'RequestId': '1234',
        'ResponseURL': TEST_RESPONSE_URL,
        'StackId': 'arn:aws:cloudformation:us-east-2:namespace:stack/stack-name/guid',
        'ResourceProperties': {
            'ProjectName': TEST_PROJECT_NAME,
        }
    }

    handler.lambda_handler(event, context)

    assert cf_endpoint.called
    assert len(cf_endpoint.request_history) == 1
    assert cf_endpoint.request_history[0].json()['PhysicalResourceId'] == TEST_PHYSICAL_RESOURCE_ID
    assert cf_endpoint.request_history[0].json()['Status'] == 'SUCCESS'
    device_farm_endpoint.create_project.assert_not_called()
    device_farm_endpoint.update_project.assert_not_called()
    device_farm_endpoint.delete_project.assert_called_with(arn=TEST_PHYSICAL_RESOURCE_ID)


def test_handler_delete_not_created(context, cf_endpoint, device_farm_endpoint):
    event = {
        'RequestType': 'Delete',
        'LogicalResourceId': 'DeviceFarm',
        'PhysicalResourceId': 'ResourceNotCreated',
        'RequestId': '1234',
        'ResponseURL': TEST_RESPONSE_URL,
        'StackId': 'arn:aws:cloudformation:us-east-2:namespace:stack/stack-name/guid',
        'ResourceProperties': {
            'ProjectName': TEST_PROJECT_NAME,
        }
    }

    handler.lambda_handler(event, context)

    assert cf_endpoint.called
    assert len(cf_endpoint.request_history) == 1
    assert cf_endpoint.request_history[0].json()['PhysicalResourceId'] == 'ResourceNotCreated'
    assert cf_endpoint.request_history[0].json()['Status'] == 'SUCCESS'
    device_farm_endpoint.create_project.assert_not_called()
    device_farm_endpoint.update_project.assert_not_called()
    device_farm_endpoint.delete_project.assert_not_called()


def test_handler_delete_fails(context, cf_endpoint, device_farm_endpoint):
    event = {
        'RequestType': 'Delete',
        'LogicalResourceId': 'DeviceFarm',
        'PhysicalResourceId': TEST_PHYSICAL_RESOURCE_ID,
        'RequestId': '1234',
        'ResponseURL': TEST_RESPONSE_URL,
        'StackId': 'arn:aws:cloudformation:us-east-2:namespace:stack/stack-name/guid',
        'ResourceProperties': {
            'ProjectName': TEST_PROJECT_NAME,
        }
    }
    device_farm_endpoint.delete_project = MagicMock(side_effect=Exception('This went wrong'))

    handler.lambda_handler(event, context)

    assert cf_endpoint.called
    assert len(cf_endpoint.request_history) == 1
    assert cf_endpoint.request_history[0].json()['PhysicalResourceId'] == TEST_PHYSICAL_RESOURCE_ID
    assert cf_endpoint.request_history[0].json()['Status'] == 'FAILED'
    device_farm_endpoint.create_project.assert_not_called()
    device_farm_endpoint.update_project.assert_not_called()
    device_farm_endpoint.delete_project.assert_called_with(arn=TEST_PHYSICAL_RESOURCE_ID)
