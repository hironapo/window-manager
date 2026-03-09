"""
tests/test_config_mgr.py - ConfigManager のユニットテスト

実行方法:
  py -3 -m pytest tests/ -v
  または
  py -3 -m pytest tests/test_config_mgr.py -v
"""

import json
import os
import sys
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

# パスを通す
sys.path.insert(0, str(Path(__file__).parent.parent))

from config_mgr import ConfigManager, DEFAULT_CONFIG


# ─── フィクスチャ ───────────────────────────────────────────
@pytest.fixture
def tmp_config(tmp_path):
    """一時ディレクトリに config.json を作成する ConfigManager"""
    config_path = tmp_path / "config.json"
    with patch.object(ConfigManager, '__init__', lambda self: None):
        mgr = ConfigManager.__new__(ConfigManager)
        mgr.config_path = config_path
        mgr.on_change = None
        mgr._load()
    return mgr


@pytest.fixture
def preset_data():
    return {
        "name": "横並び2分割",
        "hotkey": "ctrl+alt+1",
        "windows": [
            {"app": "chrome",   "layout": {"x": 0.0, "y": 0.0, "w": 0.5, "h": 1.0}},
            {"app": "notepad",  "layout": {"x": 0.5, "y": 0.0, "w": 0.5, "h": 1.0}},
        ]
    }


# ─── 初期化テスト ───────────────────────────────────────────
class TestInit:
    def test_creates_config_file_if_not_exists(self, tmp_path):
        config_path = tmp_path / "config.json"
        assert not config_path.exists()

        with patch.object(ConfigManager, '__init__', lambda self: None):
            mgr = ConfigManager.__new__(ConfigManager)
            mgr.config_path = config_path
            mgr.on_change = None
            mgr._load()

        assert config_path.exists()

    def test_default_popup_hotkey(self, tmp_config):
        assert tmp_config.get('popup_hotkey') == 'ctrl+alt+w'

    def test_default_presets_empty(self, tmp_config):
        assert tmp_config.get_presets() == []

    def test_loads_existing_config(self, tmp_path):
        config_path = tmp_path / "config.json"
        config_data = {"popup_hotkey": "ctrl+alt+q", "presets": []}
        config_path.write_text(json.dumps(config_data), encoding='utf-8')

        with patch.object(ConfigManager, '__init__', lambda self: None):
            mgr = ConfigManager.__new__(ConfigManager)
            mgr.config_path = config_path
            mgr.on_change = None
            mgr._load()

        assert mgr.get('popup_hotkey') == 'ctrl+alt+q'


# ─── get / set テスト ──────────────────────────────────────
class TestGetSet:
    def test_get_existing_key(self, tmp_config):
        assert tmp_config.get('popup_hotkey') == 'ctrl+alt+w'

    def test_get_missing_key_returns_default(self, tmp_config):
        assert tmp_config.get('missing_key', 'fallback') == 'fallback'

    def test_get_missing_key_returns_none(self, tmp_config):
        assert tmp_config.get('missing_key') is None

    def test_set_persists_to_file(self, tmp_config):
        tmp_config.set('popup_hotkey', 'ctrl+alt+p')
        data = json.loads(tmp_config.config_path.read_text(encoding='utf-8'))
        assert data['popup_hotkey'] == 'ctrl+alt+p'

    def test_set_calls_on_change(self, tmp_config):
        called = []
        tmp_config.on_change = lambda: called.append(True)
        tmp_config.set('popup_hotkey', 'ctrl+shift+w')
        assert len(called) == 1


# ─── プリセットCRUD ─────────────────────────────────────────
class TestPresetCRUD:
    def test_add_preset_assigns_uuid(self, tmp_config, preset_data):
        preset_id = tmp_config.add_preset(preset_data)
        assert preset_id is not None
        # UUID形式か確認
        uuid.UUID(preset_id)

    def test_add_preset_stores_correctly(self, tmp_config, preset_data):
        tmp_config.add_preset(preset_data)
        presets = tmp_config.get_presets()
        assert len(presets) == 1
        assert presets[0]['name'] == '横並び2分割'
        assert presets[0]['hotkey'] == 'ctrl+alt+1'

    def test_add_multiple_presets(self, tmp_config, preset_data):
        tmp_config.add_preset({**preset_data, "name": "A"})
        tmp_config.add_preset({**preset_data, "name": "B"})
        tmp_config.add_preset({**preset_data, "name": "C"})
        assert len(tmp_config.get_presets()) == 3

    def test_get_preset_by_id(self, tmp_config, preset_data):
        pid = tmp_config.add_preset(preset_data)
        result = tmp_config.get_preset(pid)
        assert result is not None
        assert result['name'] == '横並び2分割'

    def test_get_preset_invalid_id_returns_none(self, tmp_config):
        assert tmp_config.get_preset('nonexistent-id') is None

    def test_update_preset_name(self, tmp_config, preset_data):
        pid = tmp_config.add_preset(preset_data)
        result = tmp_config.update_preset(pid, {"name": "新しい名前"})
        assert result is True
        assert tmp_config.get_preset(pid)['name'] == '新しい名前'

    def test_update_preset_invalid_id_returns_false(self, tmp_config):
        result = tmp_config.update_preset('invalid-id', {"name": "test"})
        assert result is False

    def test_delete_preset(self, tmp_config, preset_data):
        pid = tmp_config.add_preset(preset_data)
        assert len(tmp_config.get_presets()) == 1
        tmp_config.delete_preset(pid)
        assert len(tmp_config.get_presets()) == 0

    def test_delete_nonexistent_preset_no_error(self, tmp_config):
        tmp_config.delete_preset('nonexistent-id')  # エラーにならない

    def test_delete_does_not_affect_other_presets(self, tmp_config, preset_data):
        pid1 = tmp_config.add_preset({**preset_data, "name": "A"})
        pid2 = tmp_config.add_preset({**preset_data, "name": "B"})
        tmp_config.delete_preset(pid1)
        presets = tmp_config.get_presets()
        assert len(presets) == 1
        assert presets[0]['id'] == pid2

    def test_preset_persists_after_reload(self, tmp_config, preset_data):
        tmp_config.add_preset(preset_data)

        # 同じファイルを再ロード
        with patch.object(ConfigManager, '__init__', lambda self: None):
            mgr2 = ConfigManager.__new__(ConfigManager)
            mgr2.config_path = tmp_config.config_path
            mgr2.on_change = None
            mgr2._load()

        assert len(mgr2.get_presets()) == 1
        assert mgr2.get_presets()[0]['name'] == '横並び2分割'


# ─── ウィンドウスキーマ検証 ────────────────────────────────
class TestPresetWindowSchema:
    def test_windows_layout_values(self, tmp_config, preset_data):
        pid = tmp_config.add_preset(preset_data)
        preset = tmp_config.get_preset(pid)
        windows = preset['windows']

        assert len(windows) == 2
        for win in windows:
            layout = win['layout']
            for key in ('x', 'y', 'w', 'h'):
                assert key in layout
                assert 0.0 <= layout[key] <= 1.0

    def test_empty_windows_list(self, tmp_config):
        pid = tmp_config.add_preset({"name": "空", "hotkey": "", "windows": []})
        preset = tmp_config.get_preset(pid)
        assert preset['windows'] == []
