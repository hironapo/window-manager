"""
ui_popup.py - グローバルホットキーで表示するポップアップ選択メニュー
"""
import tkinter as tk

DARK_NAVY  = '#003366'
ROYAL_BLUE = '#0055AA'
LIGHT_BLUE = '#E8F4FC'
RED        = '#CC0000'
WHITE      = '#FFFFFF'
GRAY_LINE  = '#CCCCCC'
GRAY_TEXT  = '#666666'


class PopupMenu:
    def __init__(self, root, config, on_manage=None):
        self.root = root
        self.config = config
        self.on_manage = on_manage
        self.window = None

    # ─────────────────────────────────────────
    def show(self):
        if self.window and self.window.winfo_exists():
            self.window.destroy()

        self.window = tk.Toplevel(self.root)
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        self.window.configure(bg=WHITE)

        self._build()
        self._center()

        self.window.focus_force()
        self.window.bind('<Escape>', lambda _: self.close())
        self.window.bind('<FocusOut>', lambda _: self.close())

    def close(self):
        if self.window and self.window.winfo_exists():
            self.window.destroy()
        self.window = None

    # ─────────────────────────────────────────
    def _center(self):
        self.window.update_idletasks()
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        w  = self.window.winfo_reqwidth()
        h  = self.window.winfo_reqheight()
        self.window.geometry(f'+{(sw - w) // 2}+{(sh - h) // 2}')

    # ─────────────────────────────────────────
    def _build(self):
        # ── タイトルバー ──────────────────────
        title_bar = tk.Frame(self.window, bg=DARK_NAVY, height=42)
        title_bar.pack(fill='x')
        title_bar.pack_propagate(False)

        tk.Label(title_bar, text='ウィンドウ配置',
                 bg=DARK_NAVY, fg=WHITE,
                 font=('Meiryo', 12, 'bold'),
                 padx=14, anchor='w').pack(side='left', fill='y')

        close = tk.Label(title_bar, text='✕',
                         bg=DARK_NAVY, fg=WHITE,
                         font=('Meiryo', 11), cursor='hand2', padx=14)
        close.pack(side='right', fill='y')
        close.bind('<Button-1>', lambda _: self.close())

        # ── プリセット一覧 ────────────────────
        body = tk.Frame(self.window, bg=WHITE, padx=10, pady=8)
        body.pack(fill='both', expand=True)

        presets = self.config.get_presets()
        if presets:
            for i, preset in enumerate(presets):
                self._preset_row(body, preset, i)
        else:
            tk.Label(body,
                     text='プリセットがありません\n管理メニューから追加してください',
                     bg=WHITE, fg='#999999',
                     font=('Meiryo', 9), pady=16).pack()

        # ── 区切り線 ──────────────────────────
        tk.Frame(self.window, height=1, bg=GRAY_LINE).pack(fill='x')

        # ── フッター ──────────────────────────
        footer = tk.Frame(self.window, bg=LIGHT_BLUE, padx=10, pady=7)
        footer.pack(fill='x')

        tk.Label(footer, text='ESC で閉じる',
                 bg=LIGHT_BLUE, fg=GRAY_TEXT,
                 font=('Meiryo', 8)).pack(side='left')

        manage_btn = tk.Button(footer, text='⚙ 管理メニュー',
                               bg=ROYAL_BLUE, fg=WHITE,
                               font=('Meiryo', 9, 'bold'),
                               relief='flat', cursor='hand2',
                               padx=10, pady=3,
                               command=self._open_manage)
        manage_btn.pack(side='right')

    # ─────────────────────────────────────────
    def _preset_row(self, parent, preset, index):
        from window_mgr import apply_preset

        row = tk.Frame(parent, bg=WHITE, cursor='hand2')
        row.pack(fill='x', pady=2)

        # 番号バッジ
        badge = tk.Label(row, text=str(index + 1),
                         bg=DARK_NAVY, fg=WHITE,
                         font=('Meiryo', 9, 'bold'),
                         width=2, padx=4, pady=3)
        badge.pack(side='left', padx=(0, 8))

        name = tk.Label(row, text=preset.get('name', '(名前なし)'),
                        bg=WHITE, fg=DARK_NAVY,
                        font=('Meiryo', 10), anchor='w', pady=4)
        name.pack(side='left', fill='x', expand=True)

        hk_text = preset.get('hotkey', '')
        hk = tk.Label(row, text=hk_text.upper() if hk_text else '',
                      bg=WHITE, fg='#999999',
                      font=('Meiryo', 8), padx=8)
        hk.pack(side='right')

        widgets = [row, name, hk]

        def on_enter(_):
            for w in widgets:
                w.configure(bg=LIGHT_BLUE)

        def on_leave(_):
            for w in widgets:
                w.configure(bg=WHITE)

        def on_click(_=None):
            self.close()
            apply_preset(preset)

        for w in widgets:
            w.bind('<Enter>', on_enter)
            w.bind('<Leave>', on_leave)
            w.bind('<Button-1>', on_click)

        # 数字キーで即実行
        if index < 9:
            self.window.bind(str(index + 1), on_click)

    # ─────────────────────────────────────────
    def _open_manage(self):
        self.close()
        if self.on_manage:
            self.on_manage()
