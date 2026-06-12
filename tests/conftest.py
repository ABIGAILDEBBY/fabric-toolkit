"""Shared pytest fixtures for fabric-toolkit tests."""

import base64
import json
import pytest


def make_schedule_payload(schedules):
    """Return a base64-encoded .schedules part payload from a list of schedule dicts."""
    data = {'schedules': schedules}
    return base64.b64encode(json.dumps(data).encode('utf-8')).decode('utf-8')


def make_pipeline_payload(activities):
    """Return a base64-encoded pipeline.json part payload."""
    data = {'properties': {'activities': activities}}
    return base64.b64encode(json.dumps(data).encode('utf-8')).decode('utf-8')


@pytest.fixture
def schedule_part_active():
    """Single enabled daily schedule at 08:00 UTC, Mon-Fri."""
    payload = make_schedule_payload([{
        'enabled': True,
        'configuration': {
            'type': 'Cron',
            'times': ['08:00'],
            'localTimeZoneId': 'UTC',
            'weekDays': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
            'startDateTime': '2024-01-01T00:00:00',
            'endDateTime': '2099-12-31T23:59:59',
        }
    }])
    return [{'path': '.schedules', 'payload': payload}]


@pytest.fixture
def schedule_part_disabled():
    """Single disabled schedule."""
    payload = make_schedule_payload([{
        'enabled': False,
        'configuration': {
            'type': 'Cron',
            'times': ['06:00'],
            'localTimeZoneId': 'GMT Standard Time',
            'weekDays': [],
        }
    }])
    return [{'path': '.schedules', 'payload': payload}]


@pytest.fixture
def schedule_part_multiple():
    """Two schedules: one active, one disabled."""
    payload = make_schedule_payload([
        {
            'enabled': True,
            'configuration': {
                'type': 'Cron',
                'times': ['06:00', '18:00'],
                'localTimeZoneId': 'UTC',
                'weekDays': ['Monday', 'Wednesday', 'Friday'],
                'startDateTime': '2024-06-01T00:00:00',
                'endDateTime': '2099-12-31T23:59:59',
            }
        },
        {
            'enabled': False,
            'configuration': {
                'type': 'Cron',
                'times': ['12:00'],
                'localTimeZoneId': 'UTC',
                'weekDays': [],
            }
        }
    ])
    return [{'path': '.schedules', 'payload': payload}]


@pytest.fixture
def pipeline_part_with_invoke():
    """Pipeline definition containing an ExecutePipeline activity."""
    payload = make_pipeline_payload([{
        'name': 'Invoke Child',
        'type': 'ExecutePipeline',
        'typeProperties': {
            'pipeline': {'referenceName': 'pl_child_pipeline'}
        }
    }])
    return [
        {'path': 'pipeline.json', 'payload': payload},
        {'path': '.platform', 'payload': ''},
    ]


@pytest.fixture
def pipeline_part_nested_invoke():
    """Pipeline with nested activities inside an IfCondition."""
    payload = make_pipeline_payload([{
        'name': 'Check Condition',
        'type': 'IfCondition',
        'typeProperties': {
            'ifTrueActivities': [{
                'name': 'Run Bronze',
                'type': 'InvokePipeline',
                'typeProperties': {
                    'pipeline': {'referenceName': 'pl_bronze_load'}
                }
            }],
            'ifFalseActivities': []
        }
    }])
    return [{'path': 'pipeline.json', 'payload': payload}]
