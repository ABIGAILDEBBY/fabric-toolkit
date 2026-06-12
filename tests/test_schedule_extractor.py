"""Tests for tools/schedule_extractor.py

Covers:
  - Pure utility functions (trunc, fmt_time, fmt_dur, sanitize_filename)
  - Schedule parsing (parse_schedule)
  - Pipeline child detection (get_invoke_targets)
  - API helpers with mocked HTTP (get_definition_parts, get_last_run)
  - Auth helper (get_token) with mocked MSAL
"""

import base64
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Make tools/ importable without a config.py present
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the module without triggering main()
import tools.schedule_extractor as ext


# ── trunc ─────────────────────────────────────────────────────────────────────

class TestTrunc:
    def test_short_string_unchanged(self):
        assert ext.trunc('hello') == 'hello'

    def test_exact_limit_unchanged(self):
        s = 'x' * 52
        assert ext.trunc(s) == s

    def test_long_string_truncated(self):
        s = 'a' * 60
        result = ext.trunc(s)
        assert result.endswith('...')
        assert len(result) == 52

    def test_custom_limit(self):
        result = ext.trunc('hello world', n=8)
        assert result == 'hello...'
        assert len(result) == 8

    def test_empty_string(self):
        assert ext.trunc('') == ''


# ── sanitize_filename ─────────────────────────────────────────────────────────

class TestSanitizeFilename:
    def test_clean_name_unchanged(self):
        assert ext.sanitize_filename('GDW DEV') == 'GDW DEV'

    def test_forward_slash_replaced(self):
        assert ext.sanitize_filename('GDW/DEV') == 'GDW_DEV'

    def test_backslash_replaced(self):
        assert ext.sanitize_filename('GDW\\DEV') == 'GDW_DEV'

    def test_colon_replaced(self):
        assert ext.sanitize_filename('GDW:DEV') == 'GDW_DEV'

    def test_all_invalid_chars_replaced(self):
        result = ext.sanitize_filename('a/b\\c:d*e?f"g<h>i|j')
        for ch in r'/\:*?"<>|':
            assert ch not in result
        assert '_' in result

    def test_leading_trailing_spaces_stripped(self):
        assert ext.sanitize_filename('  GDW DEV  ') == 'GDW DEV'


# ── fmt_time ──────────────────────────────────────────────────────────────────

class TestFmtTime:
    def test_iso_string_with_z(self):
        result = ext.fmt_time('2024-03-15T08:30:00Z')
        assert result == '2024-03-15 08:30 UTC'

    def test_iso_string_with_offset(self):
        result = ext.fmt_time('2024-03-15T08:30:00+00:00')
        assert result == '2024-03-15 08:30 UTC'

    def test_empty_string_returns_never(self):
        assert ext.fmt_time('') == 'Never'

    def test_none_returns_never(self):
        assert ext.fmt_time(None) == 'Never'

    def test_never_passthrough(self):
        assert ext.fmt_time('Never') == 'Never'

    def test_invalid_string_returned_as_is(self):
        assert ext.fmt_time('not-a-date') == 'not-a-date'


# ── fmt_dur ───────────────────────────────────────────────────────────────────

class TestFmtDur:
    def test_seconds_only(self):
        assert ext.fmt_dur(45) == '45s'

    def test_minutes_and_seconds(self):
        assert ext.fmt_dur(125) == '2m 5s'

    def test_hours_minutes_seconds(self):
        assert ext.fmt_dur(3661) == '1h 1m 1s'

    def test_zero(self):
        assert ext.fmt_dur(0) == '0s'

    def test_exactly_one_hour(self):
        assert ext.fmt_dur(3600) == '1h 0m 0s'

    def test_float_truncated(self):
        assert ext.fmt_dur(90.9) == '1m 30s'


# ── parse_schedule ────────────────────────────────────────────────────────────

class TestParseSchedule:
    def test_active_schedule_parsed(self, schedule_part_active):
        result = ext.parse_schedule(schedule_part_active)
        assert len(result) == 1
        assert result[0]['enabled'] is True
        assert result[0]['type'] == 'Cron'
        assert result[0]['times'] == '08:00'
        assert result[0]['timezone'] == 'UTC'
        assert 'Monday' in result[0]['weekdays']
        assert result[0]['start_date'] == '2024-01-01'
        assert result[0]['end_date'] == '2099-12-31'

    def test_disabled_schedule_parsed(self, schedule_part_disabled):
        result = ext.parse_schedule(schedule_part_disabled)
        assert len(result) == 1
        assert result[0]['enabled'] is False
        assert result[0]['timezone'] == 'GMT Standard Time'

    def test_multiple_schedules(self, schedule_part_multiple):
        result = ext.parse_schedule(schedule_part_multiple)
        assert len(result) == 2
        enabled_schedules = [s for s in result if s['enabled']]
        assert len(enabled_schedules) == 1
        assert '06:00' in enabled_schedules[0]['times']
        assert '18:00' in enabled_schedules[0]['times']

    def test_empty_parts_returns_empty(self):
        assert ext.parse_schedule([]) == []

    def test_no_schedule_part_returns_empty(self):
        parts = [{'path': 'pipeline.json', 'payload': 'e30='}]
        assert ext.parse_schedule(parts) == []

    def test_schedule_without_dates(self):
        payload = base64.b64encode(json.dumps({
            'schedules': [{
                'enabled': True,
                'configuration': {'type': 'Cron', 'times': ['09:00']}
            }]
        }).encode()).decode()
        parts = [{'path': '.schedules', 'payload': payload}]
        result = ext.parse_schedule(parts)
        assert result[0]['start_date'] == ''
        assert result[0]['end_date'] == ''

    def test_invalid_base64_returns_empty(self):
        parts = [{'path': '.schedules', 'payload': 'not-valid-base64!!!'}]
        assert ext.parse_schedule(parts) == []

    def test_interval_schedule(self):
        payload = base64.b64encode(json.dumps({
            'schedules': [{
                'enabled': True,
                'configuration': {'type': 'Interval', 'interval': 30}
            }]
        }).encode()).decode()
        parts = [{'path': '.schedules', 'payload': payload}]
        result = ext.parse_schedule(parts)
        assert result[0]['interval'] == '30'


# ── get_invoke_targets ────────────────────────────────────────────────────────

class TestGetInvokeTargets:
    def test_execute_pipeline_found(self, pipeline_part_with_invoke):
        result = ext.get_invoke_targets(pipeline_part_with_invoke)
        assert 'pl_child_pipeline' in result

    def test_nested_invoke_pipeline(self, pipeline_part_nested_invoke):
        result = ext.get_invoke_targets(pipeline_part_nested_invoke)
        assert 'pl_bronze_load' in result

    def test_no_invokes_returns_empty(self):
        import base64, json
        payload = base64.b64encode(json.dumps({
            'properties': {'activities': [
                {'name': 'Copy data', 'type': 'Copy', 'typeProperties': {}}
            ]}
        }).encode()).decode()
        parts = [{'path': 'pipeline.json', 'payload': payload}]
        assert ext.get_invoke_targets(parts) == []

    def test_empty_parts(self):
        assert ext.get_invoke_targets([]) == []

    def test_deduplicates_same_child(self):
        import base64, json
        payload = base64.b64encode(json.dumps({
            'properties': {'activities': [
                {'name': 'A', 'type': 'ExecutePipeline',
                 'typeProperties': {'pipeline': {'referenceName': 'pl_same'}}},
                {'name': 'B', 'type': 'ExecutePipeline',
                 'typeProperties': {'pipeline': {'referenceName': 'pl_same'}}},
            ]}
        }).encode()).decode()
        parts = [{'path': 'pipeline.json', 'payload': payload}]
        result = ext.get_invoke_targets(parts)
        assert result.count('pl_same') == 1

    def test_skips_schedules_and_platform_paths(self):
        import base64
        parts = [
            {'path': '.schedules', 'payload': base64.b64encode(b'{}').decode()},
            {'path': 'activity.platform', 'payload': base64.b64encode(b'{}').decode()},
        ]
        assert ext.get_invoke_targets(parts) == []


# ── get_definition_parts (mocked HTTP) ───────────────────────────────────────

class TestGetDefinitionParts:
    def setup_method(self):
        ext.WORKSPACE_ID = 'ws-test-id'
        ext.FAB = {'Authorization': 'Bearer test-token'}

    @pytest.mark.integration
    def test_200_response_returns_parts(self):
        mock_parts = [{'path': '.schedules', 'payload': 'abc'}]
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'definition': {'parts': mock_parts}}

        with patch('requests.post', return_value=mock_resp):
            result = ext.get_definition_parts('item-123')

        assert result == mock_parts

    @pytest.mark.integration
    def test_202_async_returns_parts_after_poll(self):
        mock_parts = [{'path': 'pipeline.json', 'payload': 'xyz'}]

        async_resp = MagicMock()
        async_resp.status_code = 202
        async_resp.headers = {'Location': 'https://api.fabric.microsoft.com/v1/operations/op-1'}

        poll_resp = MagicMock()
        poll_resp.status_code = 200
        poll_resp.json.return_value = {'definition': {'parts': mock_parts}}

        with patch('requests.post', return_value=async_resp), \
             patch('requests.get', return_value=poll_resp), \
             patch('time.sleep'):
            result = ext.get_definition_parts('item-456')

        assert result == mock_parts

    @pytest.mark.integration
    def test_202_missing_location_header_returns_empty(self):
        async_resp = MagicMock()
        async_resp.status_code = 202
        async_resp.headers = {}

        with patch('requests.post', return_value=async_resp):
            result = ext.get_definition_parts('item-789')

        assert result == []

    @pytest.mark.integration
    def test_error_response_returns_empty(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 500

        with patch('requests.post', return_value=mock_resp):
            result = ext.get_definition_parts('item-err')

        assert result == [] or result is None

    @pytest.mark.integration
    def test_network_exception_returns_none(self):
        with patch('requests.post', side_effect=Exception('timeout')):
            result = ext.get_definition_parts('item-net')

        assert result is None


# ── get_last_run (mocked HTTP) ────────────────────────────────────────────────

class TestGetLastRun:
    def setup_method(self):
        ext.WORKSPACE_ID = 'ws-test-id'
        ext.FAB = {'Authorization': 'Bearer test-token'}

    @pytest.mark.integration
    def test_returns_last_run_time_and_status(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'value': [
            {'startTime': '2024-03-15T08:30:00Z', 'status': 'Succeeded'}
        ]}

        with patch('requests.get', return_value=mock_resp):
            run_time, status = ext.get_last_run('item-123')

        assert run_time == '2024-03-15 08:30 UTC'
        assert status == 'Succeeded'

    @pytest.mark.integration
    def test_empty_run_list_returns_never_run(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'value': []}

        with patch('requests.get', return_value=mock_resp):
            run_time, status = ext.get_last_run('item-456')

        assert run_time == 'Never run'
        assert status == 'N/A'

    @pytest.mark.integration
    def test_403_returns_no_access(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 403

        with patch('requests.get', return_value=mock_resp):
            run_time, status = ext.get_last_run('item-789')

        assert run_time == 'No access'
        assert status == 'No access'

    @pytest.mark.integration
    def test_404_returns_never_run(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 404

        with patch('requests.get', return_value=mock_resp):
            run_time, status = ext.get_last_run('item-404')

        assert run_time == 'Never run'
        assert status == 'N/A'

    @pytest.mark.integration
    def test_network_exception_returns_error(self):
        with patch('requests.get', side_effect=Exception('timeout')):
            run_time, status = ext.get_last_run('item-net')

        assert run_time == 'Error'
        assert status == 'Error'


# ── get_token ─────────────────────────────────────────────────────────────────

class TestGetToken:
    def test_silent_token_returned_if_cached(self):
        mock_app = MagicMock()
        mock_cache = MagicMock()
        mock_cache.has_state_changed = False
        mock_app.get_accounts.return_value = [{'username': 'test@example.com'}]
        mock_app.acquire_token_silent.return_value = {'access_token': 'cached-token'}

        result = ext.get_token(['scope'], mock_app, mock_cache)

        assert result == 'cached-token'
        mock_app.acquire_token_interactive.assert_not_called()

    def test_interactive_used_when_no_accounts(self):
        mock_app = MagicMock()
        mock_cache = MagicMock()
        mock_cache.has_state_changed = False
        mock_app.get_accounts.return_value = []
        mock_app.acquire_token_interactive.return_value = {'access_token': 'new-token'}

        result = ext.get_token(['scope'], mock_app, mock_cache)

        assert result == 'new-token'

    def test_device_flow_used_on_interactive_failure(self):
        mock_app = MagicMock()
        mock_cache = MagicMock()
        mock_cache.has_state_changed = False
        mock_app.get_accounts.return_value = []
        mock_app.acquire_token_interactive.side_effect = Exception('no browser')
        mock_app.initiate_device_flow.return_value = {'message': 'Go to https://aka.ms/devicelogin'}
        mock_app.acquire_token_by_device_flow.return_value = {'access_token': 'device-token'}

        result = ext.get_token(['scope'], mock_app, mock_cache)

        assert result == 'device-token'

    def test_sys_exit_on_failed_auth(self):
        mock_app = MagicMock()
        mock_cache = MagicMock()
        mock_app.get_accounts.return_value = []
        mock_app.acquire_token_interactive.return_value = {'error': 'invalid_grant'}

        with pytest.raises(SystemExit):
            ext.get_token(['scope'], mock_app, mock_cache)
