"""
main.py - Window Manager エントリポイント

Windows 11 向けウィンドウ配置管理ツール
  - グローバルホットキーでプリセットを即実行
  - ポップアップメニューで選択実行
  - 管理UIでプリセット登録・参照・削除

実行方法（Windows PowerShell / コマンドプロンプト）:
  py -3 main.py

必要ライブラリ:
  pip install pywin32 keyboard psutil
"""

import sys


def check_deps():
    missing = []
    for mod, pkg in [('win32gui', 'pywin32'), ('keyboard', 'keyboard'), ('psutil', 'psutil')]:
        try:
            __import__(mod)
        except ImportError:
            missing.append(pkg)
    return missing


missing = check_deps()
if missing:
    import tkinter as tk
    from tkinter import messagebox
    _root = tk.Tk()
    _root.withdraw()
    messagebox.showerror(
        '依存関係エラー',
        '以下のライブラリをインストールしてください:\n\n'
        f'pip install {" ".join(missing)}'
    )
    sys.exit(1)

import tkinter as tk
import keyboard

from config_mgr import ConfigManager
from window_mgr import apply_preset
from ui_popup import PopupMenu
from ui_management import ManagementWindow


class WindowManagerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # メインウィンドウは非表示

        self.config = ConfigManager()
        self.management = ManagementWindow(self.root, self.config)
        self.popup = PopupMenu(
            self.root, self.config,
            on_manage=self.management.show
        )

        # 設定変更時にホットキーを再登録
        self.config.on_change = lambda: self.root.after(0, self._register_hotkeys)
        self._register_hotkeys()

        self.root.protocol('WM_DELETE_WINDOW', self._quit)

    # ── ホットキー登録 ───────────────────────
    def _register_hotkeys(self):
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass

        # ポップアップ表示キー
        popup_hk = self.config.get('popup_hotkey', 'ctrl+alt+w')
        try:
            keyboard.add_hotkey(popup_hk, lambda: self.root.after(0, self.popup.show))
        except Exception as e:
            print(f'[WARN] ホットキー登録失敗: {popup_hk} → {e}')

        # プリセット個別ホットキー
        for preset in self.config.get_presets():
            hk = preset.get('hotkey', '').strip()
            if not hk:
                continue
            try:
                keyboard.add_hotkey(
                    hk,
                    lambda p=preset: self.root.after(0, lambda: apply_preset(p))
                )
            except Exception as e:
                print(f'[WARN] ホットキー登録失敗: {hk} → {e}')

    # ── 起動 ─────────────────────────────────
    def run(self):
        popup_hk = self.config.get('popup_hotkey', 'ctrl+alt+w')
        print('=' * 45)
        print('  Window Manager  起動中')
        print('=' * 45)
        print(f'  ポップアップ  : {popup_hk.upper()}')
        print(f'  管理メニュー  : ポップアップ → ⚙ 管理メニュー')
        print(f'  終了          : このウィンドウを閉じる')
        print('=' * 45)
        self.root.mainloop()

    def _quit(self):
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        self.root.destroy()


if __name__ == '__main__':
    app = WindowManagerApp()
    app.run()
