"""
window_mgr.py - Windows ウィンドウ操作（win32api）
"""
import ctypes
import ctypes.wintypes

import win32gui
import win32con
import win32process
import psutil

user32 = ctypes.windll.user32


def get_work_area():
    """タスクバーを除いた作業領域を返す (x, y, w, h)"""
    rect = ctypes.wintypes.RECT()
    user32.SystemParametersInfoW(48, 0, ctypes.byref(rect), 0)  # SPI_GETWORKAREA
    return rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top


def get_all_windows():
    """可視ウィンドウ一覧を返す [{hwnd, title, exe, pid}]"""
    windows = []

    def callback(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd)
        if not title:
            return
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            proc = psutil.Process(pid)
            exe = proc.name()
            windows.append({'hwnd': hwnd, 'title': title, 'exe': exe, 'pid': pid})
        except Exception:
            pass

    win32gui.EnumWindows(callback, None)
    return windows


def find_window_by_app(app_name):
    """アプリ名（exe名またはタイトル部分一致）でHWNDを返す"""
    app_lower = app_name.lower().replace('.exe', '')
    for w in get_all_windows():
        exe_base = w['exe'].lower().replace('.exe', '')
        if app_lower in exe_base or app_lower in w['title'].lower():
            return w['hwnd']
    return None


def move_window(hwnd, x, y, w, h):
    """ウィンドウを最大化/最小化解除してから移動・リサイズする"""
    placement = win32gui.GetWindowPlacement(hwnd)
    if placement[1] in (win32con.SW_MAXIMIZE, win32con.SW_MINIMIZE):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetWindowPos(
        hwnd, win32con.HWND_TOP,
        x, y, w, h,
        win32con.SWP_SHOWWINDOW
    )


def apply_preset(preset):
    """プリセットを適用してウィンドウを配置する"""
    wx, wy, ww, wh = get_work_area()
    results = []
    for win_cfg in preset.get('windows', []):
        app = win_cfg.get('app', '')
        hwnd = find_window_by_app(app)
        if hwnd:
            layout = win_cfg.get('layout', {})
            x = wx + int(layout.get('x', 0) * ww)
            y = wy + int(layout.get('y', 0) * wh)
            w = int(layout.get('w', 0.5) * ww)
            h = int(layout.get('h', 1.0) * wh)
            move_window(hwnd, x, y, w, h)
            results.append((app, True))
        else:
            results.append((app, False))
    return results


def capture_current_layout():
    """現在表示中の全ウィンドウの位置・サイズを画面比率で取得する"""
    wx, wy, ww, wh = get_work_area()
    layout = []
    for w in get_all_windows():
        try:
            rect = win32gui.GetWindowRect(w['hwnd'])
            layout.append({
                'app': w['exe'].replace('.exe', ''),
                'title': w['title'],
                'layout': {
                    'x': round((rect[0] - wx) / ww, 3),
                    'y': round((rect[1] - wy) / wh, 3),
                    'w': round((rect[2] - rect[0]) / ww, 3),
                    'h': round((rect[3] - rect[1]) / wh, 3),
                }
            })
        except Exception:
            pass
    return layout
