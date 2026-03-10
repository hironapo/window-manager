# Window Manager

Windows 11 向けウィンドウ配置管理ツール。
グローバルホットキーでウィンドウを素早くタイル・整列・プリセット配置できます。

**2つのバージョンがあります：**
- **Python 版** (`main.py`) — 高機能・WSL2 環境向け
- **AHK 版** (`ahk/WindowManager.ahk`) — AutoHotkey v2 のみ・スタンドアロン

---

## 機能

| 機能 | Python 版 | AHK 版 |
|------|-----------|--------|
| ポップアップメニュー | ✓ | ✓ |
| 即実行ホットキー | ✓ | ✓ |
| 自動タイル（アレンジモード） | ✓ | ✓ |
| プリセット管理UI | ✓ | ✓ |
| 設定エクスポート/インポート | ✗ | ✓ |
| クイックレイアウト14種 | ✓ | ✗ |
| 現在配置の取り込み | ✓ | ✗ |
| カスタム位置指定（比率） | ✓ | ✓ |

---

## Python 版

### 動作環境

- Windows 11（win32 API を使用）
- Python 3.8 以上（Windows 側）

> WSL2 から実行する場合は `py.exe -3 main.py` を使用してください。

### インストール

```powershell
pip install pywin32 keyboard psutil
```

### 起動

```powershell
py -3 main.py
```

> **管理者権限について：** `keyboard` ライブラリはグローバルホットキーの検知に管理者権限が必要な場合があります。

### 使い方

| 操作 | 内容 |
|------|------|
| `Ctrl+Alt+W` | ポップアップメニュー表示 |
| 数字キー 1〜9 | ポップアップからプリセット即実行 |
| プリセット個別キー | ポップアップなしで直接実行 |
| ⚙ 管理メニュー | プリセット登録・編集・削除 |

### ファイル構成

```
window-manager/
├── main.py            # エントリポイント、ホットキーデーモン
├── config_mgr.py      # JSON 設定管理
├── window_mgr.py      # Win32 ウィンドウ操作
├── ui_popup.py        # ポップアップ選択メニュー
├── ui_management.py   # プリセット管理 UI
├── config.json        # 設定ファイル（自動生成）
├── requirements.txt   # 依存ライブラリ
└── tests/
    ├── test_config_mgr.py
    └── test_window_mgr.py
```

### config.json 形式

```json
{
  "popup_hotkey": "ctrl+alt+w",
  "presets": [
    {
      "id": "uuid",
      "name": "WSL 横並び",
      "hotkey": "ctrl+alt+1",
      "mode": "arrange",
      "app": "WindowsTerminal",
      "title": "wsl",
      "arrange": "horizontal"
    },
    {
      "id": "uuid",
      "name": "左右 2 分割",
      "hotkey": "ctrl+alt+3",
      "mode": "custom",
      "windows": [
        { "app": "chrome",          "layout": {"x":0.0,"y":0.0,"w":0.5,"h":1.0} },
        { "app": "WindowsTerminal", "layout": {"x":0.5,"y":0.0,"w":0.5,"h":1.0} }
      ]
    }
  ]
}
```

---

## AHK 版

`ahk/` フォルダ参照 → [ahk/README.md](ahk/README.md)

---

## ライセンス

MIT
