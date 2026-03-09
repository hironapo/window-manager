"""
ui_management.py - プリセット管理ウィンドウ（登録・参照・削除）
"""
import tkinter as tk
from tkinter import messagebox

from window_mgr import get_all_windows, capture_current_layout

DARK_NAVY  = '#003366'
ROYAL_BLUE = '#0055AA'
LIGHT_BLUE = '#E8F4FC'
RED        = '#CC0000'
WHITE      = '#FFFFFF'
GRAY_LINE  = '#CCCCCC'
GRAY_TEXT  = '#666666'

# クイックレイアウトプリセット（名前: {x, y, w, h}）
QUICK_LAYOUTS = {
    '左半分':   {'x': 0.0,  'y': 0.0, 'w': 0.5,  'h': 1.0},
    '右半分':   {'x': 0.5,  'y': 0.0, 'w': 0.5,  'h': 1.0},
    '上半分':   {'x': 0.0,  'y': 0.0, 'w': 1.0,  'h': 0.5},
    '下半分':   {'x': 0.0,  'y': 0.5, 'w': 1.0,  'h': 0.5},
    '左1/3':    {'x': 0.0,  'y': 0.0, 'w': 0.33, 'h': 1.0},
    '中央1/3':  {'x': 0.33, 'y': 0.0, 'w': 0.34, 'h': 1.0},
    '右1/3':    {'x': 0.67, 'y': 0.0, 'w': 0.33, 'h': 1.0},
    '左2/3':    {'x': 0.0,  'y': 0.0, 'w': 0.67, 'h': 1.0},
    '右2/3':    {'x': 0.33, 'y': 0.0, 'w': 0.67, 'h': 1.0},
    '左上1/4':  {'x': 0.0,  'y': 0.0, 'w': 0.5,  'h': 0.5},
    '右上1/4':  {'x': 0.5,  'y': 0.0, 'w': 0.5,  'h': 0.5},
    '左下1/4':  {'x': 0.0,  'y': 0.5, 'w': 0.5,  'h': 0.5},
    '右下1/4':  {'x': 0.5,  'y': 0.5, 'w': 0.5,  'h': 0.5},
    '全画面':   {'x': 0.0,  'y': 0.0, 'w': 1.0,  'h': 1.0},
    'カスタム': None,
}


def _make_btn(parent, text, command, bg=DARK_NAVY, fg=WHITE, **kw):
    return tk.Button(parent, text=text, command=command,
                     bg=bg, fg=fg,
                     font=('Meiryo', 9, 'bold'),
                     relief='flat', cursor='hand2',
                     padx=10, pady=4, **kw)


# ─────────────────────────────────────────────────────────────
class ManagementWindow:
    def __init__(self, root, config):
        self.root = root
        self.config = config
        self.window = None
        self.selected_id = None
        self._row_data = []   # [{frame, app_var, x_var, y_var, w_var, h_var}]

    # ── 表示 ─────────────────────────────────
    def show(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
        self.window = tk.Toplevel(self.root)
        self.window.title('ウィンドウマネージャー 管理')
        self.window.geometry('860x520')
        self.window.configure(bg=WHITE)
        self.window.attributes('-topmost', True)
        self.window.resizable(True, True)
        self._build()
        self._refresh_list()

    # ── UI構築 ───────────────────────────────
    def _build(self):
        # ヘッダー
        hdr = tk.Frame(self.window, bg=DARK_NAVY, height=48)
        hdr.pack(fill='x')
        hdr.pack_propagate(False)
        tk.Label(hdr, text='ウィンドウ配置プリセット管理',
                 bg=DARK_NAVY, fg=WHITE,
                 font=('Meiryo', 13, 'bold'),
                 padx=16, anchor='w').pack(side='left', fill='y')

        # ポップアップホットキー設定
        hk_frame = tk.Frame(hdr, bg=DARK_NAVY)
        hk_frame.pack(side='right', fill='y', padx=12)
        tk.Label(hk_frame, text='ポップアップキー：',
                 bg=DARK_NAVY, fg=WHITE, font=('Meiryo', 9)).pack(side='left', pady=12)
        self.popup_hk_var = tk.StringVar(value=self.config.get('popup_hotkey', 'ctrl+alt+w'))
        hk_entry = tk.Entry(hk_frame, textvariable=self.popup_hk_var,
                            font=('Meiryo', 9), width=14,
                            fg=DARK_NAVY, relief='solid', bd=1)
        hk_entry.pack(side='left', padx=(0, 6))
        hk_entry.bind('<KeyPress>', self._capture_hotkey_entry(self.popup_hk_var))
        _make_btn(hk_frame, '適用', self._save_popup_hotkey,
                  bg=ROYAL_BLUE, pady=2).pack(side='left')

        # メインエリア
        main = tk.Frame(self.window, bg=WHITE)
        main.pack(fill='both', expand=True, padx=14, pady=10)

        # ── 左：一覧 ──────────────────────────
        left = tk.Frame(main, bg=WHITE)
        left.pack(side='left', fill='y', padx=(0, 12))

        tk.Label(left, text='プリセット一覧',
                 bg=WHITE, fg=DARK_NAVY,
                 font=('Meiryo', 10, 'bold')).pack(anchor='w', pady=(0, 4))

        box_frame = tk.Frame(left, bg=GRAY_LINE, bd=1)
        box_frame.pack(fill='y', expand=True)

        self.listbox = tk.Listbox(
            box_frame, font=('Meiryo', 10),
            fg=DARK_NAVY, bg=WHITE,
            selectbackground=ROYAL_BLUE, selectforeground=WHITE,
            relief='flat', bd=0, width=20, height=14,
            activestyle='none'
        )
        self.listbox.pack(fill='both', expand=True, padx=1, pady=1)
        self.listbox.bind('<<ListboxSelect>>', self._on_select)

        btn_row = tk.Frame(left, bg=WHITE)
        btn_row.pack(fill='x', pady=(6, 0))
        _make_btn(btn_row, '＋ 新規', self._new_preset, bg=ROYAL_BLUE).pack(side='left', padx=(0, 4))
        _make_btn(btn_row, '削除',    self._delete_preset, bg=RED).pack(side='left')

        # ── 右：詳細 ──────────────────────────
        self.right = tk.Frame(main, bg=WHITE)
        self.right.pack(side='left', fill='both', expand=True)
        self._build_detail()

    # ── 詳細パネル ───────────────────────────
    def _build_detail(self):
        for w in self.right.winfo_children():
            w.destroy()
        self._row_data.clear()

        tk.Label(self.right, text='プリセット詳細',
                 bg=WHITE, fg=DARK_NAVY,
                 font=('Meiryo', 10, 'bold')).pack(anchor='w', pady=(0, 8))

        # 名前
        r = tk.Frame(self.right, bg=WHITE)
        r.pack(fill='x', pady=2)
        tk.Label(r, text='名前：', bg=WHITE, fg=DARK_NAVY,
                 font=('Meiryo', 10), width=12, anchor='w').pack(side='left')
        self.name_var = tk.StringVar()
        tk.Entry(r, textvariable=self.name_var,
                 font=('Meiryo', 10), fg=DARK_NAVY,
                 relief='solid', bd=1).pack(side='left', fill='x', expand=True)

        # ホットキー
        r2 = tk.Frame(self.right, bg=WHITE)
        r2.pack(fill='x', pady=2)
        tk.Label(r2, text='ホットキー：', bg=WHITE, fg=DARK_NAVY,
                 font=('Meiryo', 10), width=12, anchor='w').pack(side='left')
        self.hotkey_var = tk.StringVar()
        hk_e = tk.Entry(r2, textvariable=self.hotkey_var,
                        font=('Meiryo', 10), fg=DARK_NAVY,
                        relief='solid', bd=1, width=18)
        hk_e.pack(side='left')
        hk_e.bind('<KeyPress>', self._capture_hotkey_entry(self.hotkey_var))
        tk.Label(r2, text='(クリックしてキー押下で自動入力)',
                 bg=WHITE, fg='#999999', font=('Meiryo', 8)).pack(side='left', padx=6)

        # ウィンドウ一覧ヘッダ
        tk.Label(self.right, text='ウィンドウ配置：',
                 bg=WHITE, fg=DARK_NAVY,
                 font=('Meiryo', 10, 'bold')).pack(anchor='w', pady=(10, 4))

        # テーブル外枠
        tbl_outer = tk.Frame(self.right, bg=GRAY_LINE, bd=1)
        tbl_outer.pack(fill='both', expand=True)

        # テーブルヘッダ行
        hdr = tk.Frame(tbl_outer, bg=DARK_NAVY)
        hdr.pack(fill='x')
        for col, w in [('アプリ名', 16), ('クイックレイアウト', 15),
                       ('X', 6), ('Y', 6), ('W', 6), ('H', 6), ('', 3)]:
            tk.Label(hdr, text=col, bg=DARK_NAVY, fg=WHITE,
                     font=('Meiryo', 9, 'bold'), width=w, pady=4).pack(side='left')

        # スクロール可能エリア
        canvas = tk.Canvas(tbl_outer, bg=WHITE, bd=0, highlightthickness=0, height=150)
        scrollbar = tk.Scrollbar(tbl_outer, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)

        self.win_list_frame = tk.Frame(canvas, bg=WHITE)
        canvas_window = canvas.create_window((0, 0), window=self.win_list_frame, anchor='nw')

        def on_frame_configure(_):
            canvas.configure(scrollregion=canvas.bbox('all'))
        def on_canvas_configure(e):
            canvas.itemconfig(canvas_window, width=e.width)

        self.win_list_frame.bind('<Configure>', on_frame_configure)
        canvas.bind('<Configure>', on_canvas_configure)

        # ボタン行
        win_btns = tk.Frame(self.right, bg=WHITE)
        win_btns.pack(fill='x', pady=(6, 0))
        _make_btn(win_btns, '＋ ウィンドウ追加', self._pick_window, bg=ROYAL_BLUE).pack(side='left', padx=(0, 6))
        _make_btn(win_btns, '現在の配置を取り込む', self._capture_layout, bg='#555555').pack(side='left')

        # 保存ボタン
        save_row = tk.Frame(self.right, bg=WHITE)
        save_row.pack(fill='x', pady=(10, 0))
        _make_btn(save_row, '保存', self._save_preset, bg=DARK_NAVY, width=12).pack(side='right')

    # ── 行追加 ───────────────────────────────
    def _add_window_row(self, win_cfg=None):
        if win_cfg is None:
            win_cfg = {'app': '', 'layout': {'x': 0.0, 'y': 0.0, 'w': 0.5, 'h': 1.0}}

        layout = win_cfg.get('layout', {})
        bg = LIGHT_BLUE if len(self.win_list_frame.winfo_children()) % 2 == 0 else WHITE

        row = tk.Frame(self.win_list_frame, bg=bg, pady=2)
        row.pack(fill='x', padx=2)

        app_var = tk.StringVar(value=win_cfg.get('app', ''))
        x_var   = tk.StringVar(value=str(layout.get('x', 0.0)))
        y_var   = tk.StringVar(value=str(layout.get('y', 0.0)))
        w_var   = tk.StringVar(value=str(layout.get('w', 0.5)))
        h_var   = tk.StringVar(value=str(layout.get('h', 1.0)))

        def entry(var, width=6):
            return tk.Entry(row, textvariable=var,
                            font=('Meiryo', 9), fg=DARK_NAVY,
                            relief='solid', bd=1, width=width, bg=WHITE)

        app_e = entry(app_var, 16)
        app_e.pack(side='left', padx=2)

        # クイックレイアウトドロップダウン
        ql_var = tk.StringVar(value='カスタム')
        ql_menu = tk.OptionMenu(row, ql_var, *QUICK_LAYOUTS.keys())
        ql_menu.config(font=('Meiryo', 8), bg=WHITE, fg=DARK_NAVY,
                       relief='solid', bd=1, width=12, highlightthickness=0)
        ql_menu['menu'].config(font=('Meiryo', 8))
        ql_menu.pack(side='left', padx=2)

        def on_quick_select(*_):
            val = ql_var.get()
            if val != 'カスタム' and QUICK_LAYOUTS[val]:
                q = QUICK_LAYOUTS[val]
                x_var.set(str(q['x']))
                y_var.set(str(q['y']))
                w_var.set(str(q['w']))
                h_var.set(str(q['h']))

        ql_var.trace_add('write', on_quick_select)

        for var in (x_var, y_var, w_var, h_var):
            entry(var).pack(side='left', padx=2)

        del_lbl = tk.Label(row, text='✕', bg=bg, fg=RED,
                           font=('Meiryo', 10), cursor='hand2', padx=4)
        del_lbl.pack(side='left')
        del_lbl.bind('<Button-1>', lambda _: row.destroy())

        self._row_data.append({
            'frame': row,
            'app': app_var, 'x': x_var, 'y': y_var, 'w': w_var, 'h': h_var
        })

    # ── ウィンドウ選択 ───────────────────────
    def _pick_window(self):
        WindowPicker(self.window, self._on_window_picked)

    def _on_window_picked(self, app_name):
        self._add_window_row({'app': app_name, 'layout': {'x': 0.5, 'y': 0.0, 'w': 0.5, 'h': 1.0}})

    # ── 現在配置を取り込む ────────────────────
    def _capture_layout(self):
        for rd in self._row_data:
            try:
                rd['frame'].destroy()
            except Exception:
                pass
        self._row_data.clear()

        for win in capture_current_layout()[:12]:
            self._add_window_row(win)

    # ── 保存 ─────────────────────────────────
    def _get_windows_from_rows(self):
        windows = []
        for rd in self._row_data:
            try:
                if not rd['frame'].winfo_exists():
                    continue
                windows.append({
                    'app': rd['app'].get().strip(),
                    'layout': {
                        'x': float(rd['x'].get() or 0),
                        'y': float(rd['y'].get() or 0),
                        'w': float(rd['w'].get() or 0.5),
                        'h': float(rd['h'].get() or 1.0),
                    }
                })
            except (ValueError, tk.TclError):
                pass
        return windows

    def _save_preset(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror('エラー', '名前を入力してください', parent=self.window)
            return
        data = {
            'name': name,
            'hotkey': self.hotkey_var.get().strip(),
            'windows': self._get_windows_from_rows()
        }
        if self.selected_id:
            self.config.update_preset(self.selected_id, data)
        else:
            self.config.add_preset(data)
            self.selected_id = None
        self._refresh_list()
        messagebox.showinfo('保存完了', f'「{name}」を保存しました', parent=self.window)

    # ── 新規・削除 ───────────────────────────
    def _new_preset(self):
        self.selected_id = None
        self.listbox.selection_clear(0, 'end')
        self._build_detail()

    def _delete_preset(self):
        if not self.selected_id:
            return
        preset = self.config.get_preset(self.selected_id)
        if not preset:
            return
        if messagebox.askyesno('削除確認', f'「{preset["name"]}」を削除しますか？', parent=self.window):
            self.config.delete_preset(self.selected_id)
            self.selected_id = None
            self._refresh_list()
            self._build_detail()

    # ── 一覧 ─────────────────────────────────
    def _refresh_list(self):
        self.listbox.delete(0, 'end')
        self._preset_ids = []
        for p in self.config.get_presets():
            self.listbox.insert('end', p.get('name', '(名前なし)'))
            self._preset_ids.append(p['id'])

    def _on_select(self, _):
        sel = self.listbox.curselection()
        if not sel:
            return
        pid = self._preset_ids[sel[0]]
        self.selected_id = pid
        preset = self.config.get_preset(pid)
        if preset:
            self._build_detail()
            self.name_var.set(preset.get('name', ''))
            self.hotkey_var.set(preset.get('hotkey', ''))
            for win_cfg in preset.get('windows', []):
                self._add_window_row(win_cfg)

    # ── ポップアップホットキー保存 ────────────
    def _save_popup_hotkey(self):
        hk = self.popup_hk_var.get().strip()
        if hk:
            self.config.set('popup_hotkey', hk)
            messagebox.showinfo('保存', f'ポップアップキーを「{hk}」に設定しました',
                                parent=self.window)

    # ── ホットキーキャプチャ ──────────────────
    @staticmethod
    def _capture_hotkey_entry(var):
        def handler(event):
            mods = []
            if event.state & 0x4: mods.append('ctrl')
            if event.state & 0x1: mods.append('shift')
            if event.state & 0x8: mods.append('alt')
            key = event.keysym.lower()
            ignore = {'control_l', 'control_r', 'shift_l', 'shift_r',
                      'alt_l', 'alt_r', 'super_l', 'super_r'}
            if key not in ignore:
                mods.append(key)
                var.set('+'.join(mods))
            return 'break'
        return handler


# ─────────────────────────────────────────────────────────────
class WindowPicker(tk.Toplevel):
    """実行中ウィンドウを一覧から選択するダイアログ"""

    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.title('ウィンドウを選択')
        self.geometry('460x320')
        self.configure(bg=WHITE)
        self.attributes('-topmost', True)
        self.grab_set()
        self._build()

    def _build(self):
        tk.Label(self, text='実行中ウィンドウ',
                 bg=WHITE, fg=DARK_NAVY,
                 font=('Meiryo', 11, 'bold'), pady=8).pack()

        frame = tk.Frame(self, bg=GRAY_LINE, bd=1)
        frame.pack(fill='both', expand=True, padx=12, pady=(0, 8))

        self.listbox = tk.Listbox(
            frame, font=('Meiryo', 10),
            fg=DARK_NAVY, bg=WHITE,
            selectbackground=ROYAL_BLUE, selectforeground=WHITE,
            relief='flat', bd=0, activestyle='none'
        )
        self.listbox.pack(fill='both', expand=True, padx=1, pady=1)

        self._windows = get_all_windows()
        for w in self._windows:
            self.listbox.insert('end', f"{w['exe'].replace('.exe','')}  —  {w['title'][:45]}")

        self.listbox.bind('<Double-Button-1>', lambda _: self._select())

        btn_row = tk.Frame(self, bg=WHITE)
        btn_row.pack(fill='x', padx=12, pady=8)
        _make_btn(btn_row, 'キャンセル', self.destroy, bg='#888888').pack(side='right', padx=(4, 0))
        _make_btn(btn_row, '選択', self._select, bg=ROYAL_BLUE).pack(side='right')

    def _select(self):
        sel = self.listbox.curselection()
        if sel:
            w = self._windows[sel[0]]
            self.callback(w['exe'].replace('.exe', ''))
            self.destroy()
