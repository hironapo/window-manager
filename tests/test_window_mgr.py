"""
tests/test_window_mgr.py - window_mgr のユニットテスト

Win32 API 呼び出しはすべてモックするため Windows 環境不要で実行可能。

実行方法:
  py -3 -m pytest tests/ -v
  または
  py -3 -m pytest tests/test_window_mgr.py -v
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

# ── Win32 モジュールをモックしてインポート ────────────────
# Linux/CI 環境でも実行できるよう win32 系をスタブ化する
win32gui_mock = MagicMock()
win32con_mock = MagicMock()
win32process_mock = MagicMock()
psutil_mock = MagicMock()
ctypes_mock = MagicMock()

win32con_mock.SW_MAXIMIZE = 3
win32con_mock.SW_MINIMIZE = 6
win32con_mock.SW_RESTORE  = 9
win32con_mock.HWND_TOP    = 0
win32con_mock.SWP_SHOWWINDOW = 0x0040

sys.modules['win32gui']     = win32gui_mock
sys.modules['win32con']     = win32con_mock
sys.modules['win32process'] = win32process_mock
sys.modules['psutil']       = psutil_mock
sys.modules['ctypes']       = ctypes_mock
sys.modules['ctypes.wintypes'] = MagicMock()

sys.path.insert(0, str(Path(__file__).parent.parent))

import window_mgr  # noqa: E402 (モック後にインポート)


# ─── get_work_area ──────────────────────────────────────────
class TestGetWorkArea:
    def test_returns_tuple_of_four_ints(self):
        import ctypes
        rect = MagicMock()
        rect.left   = 0
        rect.top    = 0
        rect.right  = 1920
        rect.bottom = 1040

        with patch('window_mgr.ctypes.wintypes.RECT', return_value=rect), \
             patch('window_mgr.user32.SystemParametersInfoW'):
            result = window_mgr.get_work_area()

        assert len(result) == 4

    def test_width_excludes_taskbar(self):
        rect = MagicMock()
        rect.left   = 0
        rect.top    = 0
        rect.right  = 1920
        rect.bottom = 1040  # 1080 - 40px タスクバー

        with patch('window_mgr.ctypes.wintypes.RECT', return_value=rect), \
             patch('window_mgr.user32.SystemParametersInfoW'):
            x, y, w, h = window_mgr.get_work_area()

        assert w == 1920
        assert h == 1040


# ─── get_all_windows ────────────────────────────────────────
class TestGetAllWindows:
    def _setup_enum(self, windows):
        """EnumWindows のシミュレーション"""
        def fake_enum(callback, extra):
            for hwnd, title, exe, pid in windows:
                win32gui_mock.IsWindowVisible.return_value = True
                win32gui_mock.GetWindowText.return_value = title
                win32process_mock.GetWindowThreadProcessId.return_value = (0, pid)
                proc = MagicMock()
                proc.name.return_value = exe
                psutil_mock.Process.return_value = proc
                callback(hwnd, extra)

        win32gui_mock.EnumWindows.side_effect = fake_enum

    def test_returns_list_of_dicts(self):
        self._setup_enum([(1001, 'Notepad', 'notepad.exe', 111)])
        result = window_mgr.get_all_windows()
        assert isinstance(result, list)
        assert len(result) == 1

    def test_window_dict_has_required_keys(self):
        self._setup_enum([(1001, 'My Window', 'app.exe', 42)])
        result = window_mgr.get_all_windows()
        w = result[0]
        assert 'hwnd'  in w
        assert 'title' in w
        assert 'exe'   in w
        assert 'pid'   in w

    def test_skips_invisible_windows(self):
        def fake_enum(callback, _):
            win32gui_mock.IsWindowVisible.return_value = False
            win32gui_mock.GetWindowText.return_value = 'Hidden'
            callback(999, None)

        win32gui_mock.EnumWindows.side_effect = fake_enum
        result = window_mgr.get_all_windows()
        assert result == []

    def test_skips_windows_with_empty_title(self):
        def fake_enum(callback, _):
            win32gui_mock.IsWindowVisible.return_value = True
            win32gui_mock.GetWindowText.return_value = ''
            callback(888, None)

        win32gui_mock.EnumWindows.side_effect = fake_enum
        result = window_mgr.get_all_windows()
        assert result == []


# ─── find_window_by_app ─────────────────────────────────────
class TestFindWindowByApp:
    def _mock_windows(self, window_list):
        with patch('window_mgr.get_all_windows', return_value=window_list):
            pass
        return window_list

    def test_finds_by_exe_name(self):
        wins = [{'hwnd': 10, 'title': 'Untitled', 'exe': 'notepad.exe', 'pid': 1}]
        with patch('window_mgr.get_all_windows', return_value=wins):
            hwnd = window_mgr.find_window_by_app('notepad')
        assert hwnd == 10

    def test_finds_by_exe_with_extension(self):
        wins = [{'hwnd': 10, 'title': 'X', 'exe': 'chrome.exe', 'pid': 2}]
        with patch('window_mgr.get_all_windows', return_value=wins):
            hwnd = window_mgr.find_window_by_app('chrome.exe')
        assert hwnd == 10

    def test_finds_by_title_substring(self):
        wins = [{'hwnd': 20, 'title': 'Visual Studio Code', 'exe': 'code.exe', 'pid': 3}]
        with patch('window_mgr.get_all_windows', return_value=wins):
            hwnd = window_mgr.find_window_by_app('visual studio')
        assert hwnd == 20

    def test_case_insensitive_match(self):
        wins = [{'hwnd': 30, 'title': 'NOTEPAD', 'exe': 'Notepad.EXE', 'pid': 4}]
        with patch('window_mgr.get_all_windows', return_value=wins):
            hwnd = window_mgr.find_window_by_app('notepad')
        assert hwnd == 30

    def test_returns_none_when_not_found(self):
        wins = [{'hwnd': 1, 'title': 'Other', 'exe': 'other.exe', 'pid': 5}]
        with patch('window_mgr.get_all_windows', return_value=wins):
            hwnd = window_mgr.find_window_by_app('nonexistent')
        assert hwnd is None

    def test_returns_first_match(self):
        wins = [
            {'hwnd': 100, 'title': 'Chrome 1', 'exe': 'chrome.exe', 'pid': 6},
            {'hwnd': 200, 'title': 'Chrome 2', 'exe': 'chrome.exe', 'pid': 7},
        ]
        with patch('window_mgr.get_all_windows', return_value=wins):
            hwnd = window_mgr.find_window_by_app('chrome')
        assert hwnd == 100


# ─── move_window ────────────────────────────────────────────
class TestMoveWindow:
    def test_calls_set_window_pos(self):
        win32gui_mock.GetWindowPlacement.return_value = (0, win32con_mock.SW_NORMAL, 0, 0, (0, 0, 800, 600))
        win32con_mock.SW_MAXIMIZE = 3
        win32con_mock.SW_MINIMIZE = 6

        window_mgr.move_window(1001, 0, 0, 960, 1080)

        win32gui_mock.SetWindowPos.assert_called_once()
        args = win32gui_mock.SetWindowPos.call_args[0]
        assert args[0] == 1001  # hwnd
        assert args[2] == 0     # x
        assert args[3] == 0     # y
        assert args[4] == 960   # w
        assert args[5] == 1080  # h

    def test_restores_maximized_window(self):
        win32gui_mock.GetWindowPlacement.return_value = (0, win32con_mock.SW_MAXIMIZE, 0, 0, (0, 0, 0, 0))

        window_mgr.move_window(1002, 100, 100, 500, 500)

        win32gui_mock.ShowWindow.assert_called_with(1002, win32con_mock.SW_RESTORE)

    def test_restores_minimized_window(self):
        win32gui_mock.GetWindowPlacement.return_value = (0, win32con_mock.SW_MINIMIZE, 0, 0, (0, 0, 0, 0))

        window_mgr.move_window(1003, 0, 0, 400, 400)

        win32gui_mock.ShowWindow.assert_called_with(1003, win32con_mock.SW_RESTORE)


# ─── apply_preset ───────────────────────────────────────────
class TestApplyPreset:
    def _make_preset(self, windows):
        return {
            'name': 'テスト',
            'hotkey': '',
            'windows': windows
        }

    def test_applies_all_windows_in_preset(self):
        preset = self._make_preset([
            {'app': 'chrome',  'layout': {'x': 0.0, 'y': 0.0, 'w': 0.5, 'h': 1.0}},
            {'app': 'notepad', 'layout': {'x': 0.5, 'y': 0.0, 'w': 0.5, 'h': 1.0}},
        ])
        with patch('window_mgr.get_work_area', return_value=(0, 0, 1920, 1080)), \
             patch('window_mgr.find_window_by_app', side_effect=[1001, 1002]), \
             patch('window_mgr.move_window') as mock_move:
            results = window_mgr.apply_preset(preset)

        assert len(results) == 2
        assert results[0] == ('chrome',  True)
        assert results[1] == ('notepad', True)
        assert mock_move.call_count == 2

    def test_pixel_calculation_left_half(self):
        preset = self._make_preset([
            {'app': 'chrome', 'layout': {'x': 0.0, 'y': 0.0, 'w': 0.5, 'h': 1.0}},
        ])
        with patch('window_mgr.get_work_area', return_value=(0, 0, 1920, 1080)), \
             patch('window_mgr.find_window_by_app', return_value=1001), \
             patch('window_mgr.move_window') as mock_move:
            window_mgr.apply_preset(preset)

        mock_move.assert_called_once_with(1001, 0, 0, 960, 1080)

    def test_pixel_calculation_right_half(self):
        preset = self._make_preset([
            {'app': 'chrome', 'layout': {'x': 0.5, 'y': 0.0, 'w': 0.5, 'h': 1.0}},
        ])
        with patch('window_mgr.get_work_area', return_value=(0, 0, 1920, 1080)), \
             patch('window_mgr.find_window_by_app', return_value=1001), \
             patch('window_mgr.move_window') as mock_move:
            window_mgr.apply_preset(preset)

        mock_move.assert_called_once_with(1001, 960, 0, 960, 1080)

    def test_work_area_offset_applied(self):
        # タスクバー分オフセットがある場合
        preset = self._make_preset([
            {'app': 'app', 'layout': {'x': 0.0, 'y': 0.0, 'w': 1.0, 'h': 1.0}},
        ])
        with patch('window_mgr.get_work_area', return_value=(0, 40, 1920, 1040)), \
             patch('window_mgr.find_window_by_app', return_value=1001), \
             patch('window_mgr.move_window') as mock_move:
            window_mgr.apply_preset(preset)

        mock_move.assert_called_once_with(1001, 0, 40, 1920, 1040)

    def test_missing_window_returns_false(self):
        preset = self._make_preset([
            {'app': 'nonexistent', 'layout': {'x': 0.0, 'y': 0.0, 'w': 0.5, 'h': 1.0}},
        ])
        with patch('window_mgr.get_work_area', return_value=(0, 0, 1920, 1080)), \
             patch('window_mgr.find_window_by_app', return_value=None), \
             patch('window_mgr.move_window') as mock_move:
            results = window_mgr.apply_preset(preset)

        assert results[0] == ('nonexistent', False)
        mock_move.assert_not_called()

    def test_empty_preset_returns_empty_list(self):
        preset = self._make_preset([])
        with patch('window_mgr.get_work_area', return_value=(0, 0, 1920, 1080)):
            results = window_mgr.apply_preset(preset)
        assert results == []


# ─── capture_current_layout ─────────────────────────────────
class TestCaptureCurrentLayout:
    def test_returns_layout_with_ratio(self):
        wins = [{'hwnd': 1, 'title': 'App', 'exe': 'app.exe', 'pid': 1}]
        win32gui_mock.GetWindowRect.return_value = (0, 40, 960, 1080)

        with patch('window_mgr.get_all_windows', return_value=wins), \
             patch('window_mgr.get_work_area', return_value=(0, 40, 1920, 1040)):
            result = window_mgr.capture_current_layout()

        assert len(result) == 1
        layout = result[0]['layout']
        assert layout['x'] == pytest.approx(0.0,   abs=0.01)
        assert layout['y'] == pytest.approx(0.0,   abs=0.01)
        assert layout['w'] == pytest.approx(0.5,   abs=0.01)
        assert layout['h'] == pytest.approx(1.0,   abs=0.01)

    def test_result_includes_app_and_title(self):
        wins = [{'hwnd': 2, 'title': 'Notepad', 'exe': 'notepad.exe', 'pid': 2}]
        win32gui_mock.GetWindowRect.return_value = (0, 0, 960, 1080)

        with patch('window_mgr.get_all_windows', return_value=wins), \
             patch('window_mgr.get_work_area', return_value=(0, 0, 1920, 1080)):
            result = window_mgr.capture_current_layout()

        assert result[0]['app'] == 'notepad'
        assert result[0]['title'] == 'Notepad'
