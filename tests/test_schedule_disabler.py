"""Tests for tools/schedule_disabler.py

Covers:
  - Stage detection (detect_stage)
  - Fabric definition API disable (disable_fabric_schedule)
  - Power BI schedule disable (disable_pbi_schedule)
  - get_parts / push_parts API helpers
  - get_token auth helper
"""

import base64
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import tools.schedule_disabler as dis


# ── detect_stage ─────────────────────────────────────────────────────────────

class TestDetectStage:
    def test_dev_workspace(self):
        assert dis.detect_stage('GDW-DEV') == 'DEV'

    def test_dev_lowercase(self):
        assert dis.detect_stage('my workspace dev') == 'DEV'

    def test_uat_workspace(self):
        assert dis.detect_stage('GDW-UAT') == 'UAT'

    def test_staging_maps_to_uat(self):
        assert dis.detect_stage('Analytics Staging') == 'UAT'

    def test_preprod_maps_to_uat(self):
        assert dis.detect_stage('Data-PreProd') == 'UAT'

    def test_prod_workspace(self):
        assert dis.detect_stage('GDW-PROD') == 'PROD'

    def test_production_workspace(self):
        assert dis.detect_stage('Analytics Production') == 'PROD'

    def test_prd_abbreviation(self):
        assert dis.detect_stage('GDW-PRD') == 'PROD'

    def test_unknown_defaults_to_dev(self):
        assert dis.detect_stage('My Workspace') == 'DEV'

    def test_case_insensitive(self):
        assert dis.detect_stage('GDW-Prod') == 'PROD'


# ── get_parts (mocked HTTP) ───────────────────────────────────────────────────

class TestGetParts:
    def setup_method(self):
        dis.WORKSPACE_ID = 'ws-test-id'
        dis.FAB = {'Authorization': 'Bearer test-token'}

    @pytest.mark.integration
    def test_200_returns_parts(self):
        mock_parts = [{'path': '.schedules', 'payload': 'abc'}]
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.ok = True
        mock_resp.json.return_value = {'definition': {'parts': mock_parts}}

        with patch('requests.post', return_value=mock_resp):
            result = dis.get_parts('item-123')

        assert result == mock_parts

    @pytest.mark.integration
    def test_202_polls_until_result(self):
        mock_parts = [{'path': '.schedules', 'payload': 'xyz'}]

        async_resp = MagicMock()
        async_resp.status_code = 202
        async_resp.headers = {'Location': 'https://api.example.com/ops/1'}

        poll_resp = MagicMock()
        poll_resp.status_code = 200
        poll_resp.json.return_value = {'definition': {'parts': mock_parts}}

        with patch('requests.post', return_value=async_resp), \
             patch('requests.get', return_value=poll_resp), \
             patch('time.sleep'):
            result = dis.get_parts('item-456')

        assert result == mock_parts

    @pytest.mark.integration
    def test_202_missing_location_returns_empty(self):
        async_resp = MagicMock()
        async_resp.status_code = 202
        async_resp.headers = {}

        with patch('requests.post', return_value=async_resp):
            result = dis.get_parts('item-789')

        assert result == []

    @pytest.mark.integration
    def test_non_ok_response_returns_empty(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.ok = False

        with patch('requests.post', return_value=mock_resp):
            result = dis.get_parts('item-500')

        assert result == []


# ── disable_fabric_schedule (mocked HTTP) ─────────────────────────────────────

class TestDisableFabricSchedule:
    def setup_method(self):
        dis.WORKSPACE_ID = 'ws-test-id'
        dis.FAB = {'Authorization': 'Bearer test-token'}

    def _make_parts(self, schedules):
        payload = base64.b64encode(
            json.dumps({'schedules': schedules}).encode()
        ).decode()
        return [{'path': '.schedules', 'payload': payload}]

    @pytest.mark.integration
    def test_active_schedule_disabled_successfully(self):
        parts = self._make_parts([{'enabled': True, 'configuration': {}}])

        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.ok = True
        mock_get_resp.json.return_value = {'definition': {'parts': parts}}

        mock_push_resp = MagicMock()
        mock_push_resp.status_code = 200
        mock_push_resp.ok = True

        with patch('requests.post') as mock_post:
            mock_post.side_effect = [mock_get_resp, mock_push_resp]
            ok, msg = dis.disable_fabric_schedule('item-active')

        assert ok is True
        assert msg == 'Disabled'

    @pytest.mark.integration
    def test_already_disabled_returns_true(self):
        parts = self._make_parts([{'enabled': False, 'configuration': {}}])

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.ok = True
        mock_resp.json.return_value = {'definition': {'parts': parts}}

        with patch('requests.post', return_value=mock_resp):
            ok, msg = dis.disable_fabric_schedule('item-disabled')

        assert ok is True
        assert msg == 'Already disabled'

    @pytest.mark.integration
    def test_empty_parts_returns_error(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.ok = True
        mock_resp.json.return_value = {'definition': {'parts': []}}

        with patch('requests.post', return_value=mock_resp):
            ok, msg = dis.disable_fabric_schedule('item-empty')

        assert ok is False
        assert 'Could not fetch' in msg

    @pytest.mark.integration
    def test_push_failure_returns_api_error(self):
        parts = self._make_parts([{'enabled': True, 'configuration': {}}])

        get_resp = MagicMock()
        get_resp.status_code = 200
        get_resp.ok = True
        get_resp.json.return_value = {'definition': {'parts': parts}}

        push_resp = MagicMock()
        push_resp.status_code = 400
        push_resp.ok = False

        with patch('requests.post') as mock_post:
            mock_post.side_effect = [get_resp, push_resp]
            ok, msg = dis.disable_fabric_schedule('item-push-fail')

        assert ok is False
        assert 'API error' in msg

    @pytest.mark.integration
    def test_multiple_schedules_all_disabled(self):
        parts = self._make_parts([
            {'enabled': True, 'configuration': {}},
            {'enabled': True, 'configuration': {}},
        ])

        get_resp = MagicMock()
        get_resp.status_code = 200
        get_resp.ok = True
        get_resp.json.return_value = {'definition': {'parts': parts}}

        push_resp = MagicMock()
        push_resp.status_code = 200
        push_resp.ok = True

        with patch('requests.post') as mock_post:
            mock_post.side_effect = [get_resp, push_resp]
            ok, msg = dis.disable_fabric_schedule('item-multi')

        assert ok is True
        assert msg == 'Disabled'


# ── disable_pbi_schedule (mocked HTTP) ────────────────────────────────────────

class TestDisablePbiSchedule:
    def setup_method(self):
        dis.PBI = {'Authorization': 'Bearer test-token'}

    @pytest.mark.integration
    def test_active_schedule_disabled(self):
        endpoint = 'https://api.powerbi.com/v1.0/myorg/groups/ws/datasets/ds/refreshSchedule'

        get_resp = MagicMock()
        get_resp.ok = True
        get_resp.json.return_value = {'enabled': True, 'times': ['08:00'], 'days': ['Monday']}

        patch_resp = MagicMock()
        patch_resp.ok = True

        with patch('requests.get', return_value=get_resp), \
             patch('requests.patch', return_value=patch_resp):
            ok, msg = dis.disable_pbi_schedule(endpoint)

        assert ok is True
        assert msg == 'Disabled'

    @pytest.mark.integration
    def test_already_disabled_returns_true(self):
        endpoint = 'https://api.powerbi.com/v1.0/myorg/groups/ws/datasets/ds/refreshSchedule'

        get_resp = MagicMock()
        get_resp.ok = True
        get_resp.json.return_value = {'enabled': False}

        with patch('requests.get', return_value=get_resp):
            ok, msg = dis.disable_pbi_schedule(endpoint)

        assert ok is True
        assert msg == 'Already disabled'

    @pytest.mark.integration
    def test_fetch_failure_returns_error(self):
        endpoint = 'https://api.powerbi.com/v1.0/myorg/groups/ws/datasets/ds/refreshSchedule'

        get_resp = MagicMock()
        get_resp.ok = False
        get_resp.status_code = 403

        with patch('requests.get', return_value=get_resp):
            ok, msg = dis.disable_pbi_schedule(endpoint)

        assert ok is False
        assert '403' in msg

    @pytest.mark.integration
    def test_patch_failure_returns_api_error(self):
        endpoint = 'https://api.powerbi.com/v1.0/myorg/groups/ws/datasets/ds/refreshSchedule'

        get_resp = MagicMock()
        get_resp.ok = True
        get_resp.json.return_value = {'enabled': True}

        patch_resp = MagicMock()
        patch_resp.ok = False
        patch_resp.status_code = 500

        with patch('requests.get', return_value=get_resp), \
             patch('requests.patch', return_value=patch_resp):
            ok, msg = dis.disable_pbi_schedule(endpoint)

        assert ok is False
        assert '500' in msg

    @pytest.mark.integration
    def test_patch_receives_disabled_flag(self):
        endpoint = 'https://api.powerbi.com/v1.0/myorg/groups/ws/datasets/ds/refreshSchedule'

        get_resp = MagicMock()
        get_resp.ok = True
        get_resp.json.return_value = {'enabled': True, 'times': ['12:00']}

        patch_resp = MagicMock()
        patch_resp.ok = True

        with patch('requests.get', return_value=get_resp), \
             patch('requests.patch', return_value=patch_resp) as mock_patch:
            dis.disable_pbi_schedule(endpoint)

        patched_body = mock_patch.call_args.kwargs.get('json') or mock_patch.call_args[1]['json']
        assert patched_body['value']['enabled'] is False


# ── get_token ─────────────────────────────────────────────────────────────────

class TestGetToken:
    def test_cached_token_returned(self):
        mock_app = MagicMock()
        mock_cache = MagicMock()
        mock_cache.has_state_changed = False
        mock_app.get_accounts.return_value = [{'username': 'test@example.com'}]
        mock_app.acquire_token_silent.return_value = {'access_token': 'cached-token'}

        result = dis.get_token(['scope'], mock_app, mock_cache)
        assert result == 'cached-token'

    def test_interactive_fallback(self):
        mock_app = MagicMock()
        mock_cache = MagicMock()
        mock_cache.has_state_changed = False
        mock_app.get_accounts.return_value = []
        mock_app.acquire_token_interactive.return_value = {'access_token': 'new-token'}

        result = dis.get_token(['scope'], mock_app, mock_cache)
        assert result == 'new-token'

    def test_device_flow_on_no_browser(self):
        mock_app = MagicMock()
        mock_cache = MagicMock()
        mock_cache.has_state_changed = False
        mock_app.get_accounts.return_value = []
        mock_app.acquire_token_interactive.side_effect = Exception('headless')
        mock_app.initiate_device_flow.return_value = {'message': 'Visit https://aka.ms/devicelogin'}
        mock_app.acquire_token_by_device_flow.return_value = {'access_token': 'device-token'}

        result = dis.get_token(['scope'], mock_app, mock_cache)
        assert result == 'device-token'

    def test_exits_on_device_flow_error(self):
        mock_app = MagicMock()
        mock_cache = MagicMock()
        mock_app.get_accounts.return_value = []
        mock_app.acquire_token_interactive.side_effect = Exception('no browser')
        mock_app.initiate_device_flow.return_value = {
            'error': 'invalid_request', 'error_description': 'Client not found'
        }

        with pytest.raises(SystemExit):
            dis.get_token(['scope'], mock_app, mock_cache)

    def test_exits_on_missing_access_token(self):
        mock_app = MagicMock()
        mock_cache = MagicMock()
        mock_app.get_accounts.return_value = []
        mock_app.acquire_token_interactive.return_value = {'error': 'invalid_grant'}

        with pytest.raises(SystemExit):
            dis.get_token(['scope'], mock_app, mock_cache)
