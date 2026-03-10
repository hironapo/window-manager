"""
ui_popup.py - コマンドパレット風ポップアップ（モダンデザイン）
"""
import tkinter as tk

DARK_NAVY  = '#003366'
ROYAL_BLUE = '#0055AA'
LIGHT_BLUE = '#E8F4FC'
WHITE      = '#FFFFFF'
GRAY_BG    = '#F5F7FA'
GRAY_LINE  = '#E0E4EA'
GRAY_TEXT  = '#888888'
HOVER_BG   = '#EBF3FB'
BADGE_BG   = '#003366'


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
        self.window.configure(bg=GRAY_LINE)  # 外枠色として細いボーダーに見せる

        self._build()
        self._position_top_center()

        self.window.focus_force()
        self.window.bind('<Escape>', lambda _: self.close())
        self.window.bind('<FocusOut>', self._on_focus_out)

    def close(self):
        if self.window and self.window.winfo_exists():
            self.window.destroy()
        self.window = None

    def _on_focus_out(self, event):
        # 子ウィジェットへのフォーカス移動では閉じない
        try:
            focused = self.window.focus_get()
            if focused and str(focused).startswith(str(self.window)):
                return
        except Exception:
            pass
        self.close()

    # ── 位置: 画面上部中央 ───────────────────
    def _position_top_center(self):
        self.window.update_idletasks()
        sw = self.window.winfo_screenwidth()
        w  = self.window.winfo_reqwidth()
        h  = self.window.winfo_reqheight()
        x  = (sw - w) // 2
        y  = max(80, int(self.window.winfo_screenheight() * 0.12))
        self.window.geometry(f'{w}x{h}+{x}+{y}')

    # ─────────────────────────────────────────
    def _build(self):
        # 1px ボーダーを GRAY_LINE の外枠フレームで再現
        inner = tk.Frame(self.window, bg=WHITE)
        inner.pack(padx=1, pady=1, fill='both', expand=True)

        # ── ヘッダー ──────────────────────────
        hdr = tk.Frame(inner, bg=WHITE, pady=12, padx=16)
        hdr.pack(fill='x')

        tk.Label(hdr, text='WINDOW LAYOUT',
                 bg=WHITE, fg=DARK_NAVY,
                 font=('Meiryo', 9, 'bold'),
                 anchor='w').pack(side='left')

        tk.Label(hdr, text='ESC',
                 bg=GRAY_BG, fg=GRAY_TEXT,
                 font=('Meiryo', 8),
                 padx=6, pady=1, relief='flat').pack(side='right', padx=(0, 2))
        tk.Label(hdr, text='閉じる:',
                 bg=WHITE, fg=GRAY_TEXT,
                 font=('Meiryo', 8)).pack(side='right')

        # 区切り
        tk.Frame(inner, height=1, bg=GRAY_LINE).pack(fill='x')

        # ── プリセット一覧 ────────────────────
        presets = self.config.get_presets()

        if presets:
            list_frame = tk.Frame(inner, bg=WHITE)
            list_frame.pack(fill='both', expand=True, pady=4)
            for i, preset in enumerate(presets):
                self._preset_row(list_frame, preset, i)
        else:
            tk.Label(inner,
                     text='プリセットなし  ー  管理メニューから追加',
                     bg=WHITE, fg=GRAY_TEXT,
                     font=('Meiryo', 9), pady=20).pack()

        # 区切り
        tk.Frame(inner, height=1, bg=GRAY_LINE).pack(fill='x')

        # ── フッター ──────────────────────────
        footer = tk.Frame(inner, bg=GRAY_BG, padx=14, pady=8)
        footer.pack(fill='x')

        manage_btn = tk.Button(
            footer, text='管理メニュー',
            bg=ROYAL_BLUE, fg=WHITE,
            font=('Meiryo', 8, 'bold'),
            relief='flat', cursor='hand2',
            padx=12, pady=3,
            command=self._open_manage
        )
        manage_btn.pack(side='right')

        tk.Label(footer,
                 text='数字キーで即実行',
                 bg=GRAY_BG, fg=GRAY_TEXT,
                 font=('Meiryo', 8)).pack(side='left', pady=1)

    # ─────────────────────────────────────────
    def _preset_row(self, parent, preset, index):
        from window_mgr import apply_preset

        # 偶数行に淡い背景
        row_bg = WHITE if index % 2 == 0 else GRAY_BG

        row = tk.Frame(parent, bg=row_bg, cursor='hand2', pady=0)
        row.pack(fill='x')

        # 左アクセントライン
        accent = tk.Frame(row, bg=WHITE, width=3)
        accent.pack(side='left', fill='y')

        # 番号バッジ
        badge = tk.Label(row,
                         text=str(index + 1) if index < 9 else ' ',
                         bg=BADGE_BG, fg=WHITE,
                         font=('Meiryo', 8, 'bold'),
                         width=2, padx=4, pady=8)
        badge.pack(side='left', padx=(8, 10))

        name = tk.Label(row,
                        text=preset.get('name', '(名前なし)'),
                        bg=row_bg, fg=DARK_NAVY,
                        font=('Meiryo', 10), anchor='w')
        name.pack(side='left', fill='x', expand=True, pady=8)

        hk_text = preset.get('hotkey', '')
        if hk_text:
            hk = tk.Label(row,
                          text=hk_text.upper(),
                          bg=GRAY_BG, fg=GRAY_TEXT,
                          font=('Meiryo', 8),
                          padx=6, pady=2, relief='flat')
            hk.pack(side='right', padx=12, pady=6)
        else:
            hk = tk.Label(row, bg=row_bg)

        all_widgets = [row, accent, name, hk]

        def on_enter(_):
            for w in all_widgets:
                w.configure(bg=HOVER_BG)
            accent.configure(bg=ROYAL_BLUE)

        def on_leave(_):
            for w in all_widgets:
                w.configure(bg=row_bg)
            accent.configure(bg=WHITE)

        def on_click(_=None):
            self.close()
            apply_preset(preset)

        for w in [row, name]:
            w.bind('<Enter>', on_enter)
            w.bind('<Leave>', on_leave)
            w.bind('<Button-1>', on_click)

        if index < 9:
            self.window.bind(str(index + 1), on_click)

    # ─────────────────────────────────────────
    def _open_manage(self):
        self.close()
        if self.on_manage:
            self.on_manage()
