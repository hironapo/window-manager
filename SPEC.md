# Window Manager 仕様書

バージョン: 1.0.0
対象OS: Windows 11
言語: Python 3.8+

---

## 1. 概要

本ツールはWindows 11上で動作するウィンドウ配置管理デーモンです。
グローバルホットキーのリッスンとtkinterベースのGUIを組み合わせ、
登録されたプリセットに従ってウィンドウを自動配置します。

---

## 2. アーキテクチャ

### 2.1 コンポーネント構成

```
┌──────────────────────────────────────────────────┐
│  main.py  WindowManagerApp                        │
│  ├── ConfigManager     設定読み書き（JSON）        │
│  ├── keyboard daemon   グローバルホットキー監視    │
│  ├── PopupMenu         ポップアップUI              │
│  └── ManagementWindow  管理UI                     │
└──────────────────────────────────────────────────┘
          ↓ apply_preset()
┌──────────────────────────────────────────────────┐
│  window_mgr.py                                    │
│  ├── get_work_area()   作業領域取得（SPI_GETWORKAREA）│
│  ├── get_all_windows() EnumWindows でウィンドウ列挙│
│  ├── find_window_by_app() exe名/タイトルで検索    │
│  └── move_window()     SetWindowPos で配置        │
└──────────────────────────────────────────────────┘
```

### 2.2 スレッドモデル

| スレッド | 担当 |
|---------|------|
| メインスレッド | tkinter イベントループ |
| keyboard フック | ホットキー検知（別スレッド） |

keyboard フックからのコールバックは `root.after(0, ...)` でメインスレッドに委譲し、
tkinter のスレッドセーフ制約を守ります。

---

## 3. モジュール仕様

### 3.1 config_mgr.py — ConfigManager

**責務：** `config.json` の読み書きとプリセットのCRUD

**ファイルパス：** `main.py` と同ディレクトリの `config.json`

#### メソッド

| メソッド | 引数 | 戻り値 | 説明 |
|---------|------|--------|------|
| `__init__()` | — | — | 設定ロード、なければデフォルト生成 |
| `get(key, default)` | key: str | Any | 設定値取得 |
| `set(key, value)` | key: str, value: Any | — | 設定値保存（即座に書き込み） |
| `get_presets()` | — | list[dict] | 全プリセット取得 |
| `get_preset(id)` | id: str | dict \| None | IDでプリセット取得 |
| `add_preset(preset)` | preset: dict | str | 追加（UUIDをidとして付与） |
| `update_preset(id, updates)` | id: str, updates: dict | bool | 部分更新 |
| `delete_preset(id)` | id: str | — | 削除 |

#### コールバック

```python
config.on_change = callable  # 保存のたびに呼ばれる
```

#### データスキーマ

```json
{
  "popup_hotkey": "ctrl+alt+w",
  "presets": [
    {
      "id": "<uuid4>",
      "name": "<string>",
      "hotkey": "<string>",
      "windows": [
        {
          "app": "<string>",
          "layout": {
            "x": "<float 0.0-1.0>",
            "y": "<float 0.0-1.0>",
            "w": "<float 0.0-1.0>",
            "h": "<float 0.0-1.0>"
          }
        }
      ]
    }
  ]
}
```

---

### 3.2 window_mgr.py — ウィンドウ操作

**責務：** Win32 API を通じたウィンドウ検出・移動

#### 関数

| 関数 | 引数 | 戻り値 | 説明 |
|------|------|--------|------|
| `get_work_area()` | — | (x, y, w, h): tuple[int] | タスクバー除外の作業領域（px） |
| `get_all_windows()` | — | list[dict] | 可視ウィンドウ一覧 |
| `find_window_by_app(app_name)` | app_name: str | int \| None | exe名/タイトル部分一致でHWND返却 |
| `move_window(hwnd, x, y, w, h)` | hwnd: int, xywh: int | — | 最大化解除→移動・リサイズ |
| `apply_preset(preset)` | preset: dict | list[tuple] | プリセット全窓を適用、結果リスト返却 |
| `capture_current_layout()` | — | list[dict] | 現在のウィンドウ位置を比率で取得 |

#### ウィンドウ検索ロジック

```python
# app_name を小文字化・.exe 除去して比較
app_lower = app_name.lower().replace('.exe', '')
for w in get_all_windows():
    if app_lower in w['exe'].lower().replace('.exe', ''):
        return w['hwnd']  # exe名に含まれれば優先
    if app_lower in w['title'].lower():
        return w['hwnd']  # タイトルにも照合
```

#### 座標変換

```
画面比率 → ピクセル座標
  px_x = work_x + layout.x × work_w
  px_y = work_y + layout.y × work_h
  px_w = layout.w × work_w
  px_h = layout.h × work_h
```

使用Win32 API:
- `SystemParametersInfoW(SPI_GETWORKAREA)` — 作業領域取得
- `EnumWindows` — ウィンドウ列挙
- `GetWindowPlacement` — 最大化状態確認
- `ShowWindow(SW_RESTORE)` — 最大化解除
- `SetWindowPos` — 位置・サイズ設定

---

### 3.3 ui_popup.py — PopupMenu

**責務：** ホットキーで呼び出すポップアップ選択メニュー

#### 初期化

```python
PopupMenu(root, config, on_manage=None)
```

| 引数 | 型 | 説明 |
|------|----|------|
| root | tk.Tk | ルートウィジェット |
| config | ConfigManager | 設定参照 |
| on_manage | callable \| None | 管理メニューを開くコールバック |

#### メソッド

| メソッド | 説明 |
|---------|------|
| `show()` | ポップアップを画面中央に表示 |
| `close()` | ポップアップを閉じる |

#### UI仕様

| 要素 | 仕様 |
|------|------|
| ウィンドウ装飾 | なし（`overrideredirect=True`） |
| 常時最前面 | `attributes('-topmost', True)` |
| 表示位置 | 画面中央 |
| キーバインド | `ESC` → 閉じる、`FocusOut` → 閉じる、`1`〜`9` → プリセット実行 |
| ホバー効果 | 行の背景色を LIGHT_BLUE に変更 |

#### 配色

| 要素 | 色 |
|------|----|
| タイトルバー | #003366（ダークネイビー） |
| 背景 | #FFFFFF（白） |
| フッター | #E8F4FC（ライトブルー） |
| 管理ボタン | #0055AA（ロイヤルブルー） |
| 番号バッジ | #003366 背景・白文字 |
| フォント | Meiryo |

---

### 3.4 ui_management.py — ManagementWindow

**責務：** プリセットのCRUD管理UI

#### 初期化

```python
ManagementWindow(root, config)
```

#### メソッド

| メソッド | 説明 |
|---------|------|
| `show()` | 管理ウィンドウを表示（既に開いていれば前面に） |

#### UI構成

```
┌─────────────────────────────────────────────────────┐
│ ヘッダー（タイトル + ポップアップホットキー設定）    │
├─────────────────┬───────────────────────────────────┤
│ プリセット一覧  │ プリセット詳細                    │
│                 │  名前・ホットキー入力              │
│ [＋新規][削除]  │  ウィンドウ配置テーブル            │
│                 │  [＋ウィンドウ追加][現在取り込む]  │
│                 │                         [保存]    │
└─────────────────┴───────────────────────────────────┘
```

#### ウィンドウ行の入力項目

| 列 | 型 | 説明 |
|----|----|------|
| アプリ名 | テキスト | exe名またはウィンドウタイトル部分文字列 |
| クイックレイアウト | ドロップダウン | 選択で X/Y/W/H を自動入力 |
| X | float 0.0-1.0 | 作業領域左端からの比率 |
| Y | float 0.0-1.0 | 作業領域上端からの比率 |
| W | float 0.0-1.0 | 作業領域幅に対するウィンドウ幅比率 |
| H | float 0.0-1.0 | 作業領域高さに対するウィンドウ高さ比率 |

#### クイックレイアウト一覧

| 名前 | x | y | w | h |
|------|---|---|---|---|
| 左半分 | 0.0 | 0.0 | 0.5 | 1.0 |
| 右半分 | 0.5 | 0.0 | 0.5 | 1.0 |
| 上半分 | 0.0 | 0.0 | 1.0 | 0.5 |
| 下半分 | 0.0 | 0.5 | 1.0 | 0.5 |
| 左1/3 | 0.0 | 0.0 | 0.33 | 1.0 |
| 中央1/3 | 0.33 | 0.0 | 0.34 | 1.0 |
| 右1/3 | 0.67 | 0.0 | 0.33 | 1.0 |
| 左2/3 | 0.0 | 0.0 | 0.67 | 1.0 |
| 右2/3 | 0.33 | 0.0 | 0.67 | 1.0 |
| 左上1/4 | 0.0 | 0.0 | 0.5 | 0.5 |
| 右上1/4 | 0.5 | 0.0 | 0.5 | 0.5 |
| 左下1/4 | 0.0 | 0.5 | 0.5 | 0.5 |
| 右下1/4 | 0.5 | 0.5 | 0.5 | 0.5 |
| 全画面 | 0.0 | 0.0 | 1.0 | 1.0 |

#### ホットキーキャプチャ

管理UI内のホットキー入力欄にフォーカスした状態でキーを押すと、
`Ctrl/Shift/Alt + キー` を自動的に `ctrl+shift+x` 形式で入力します。

---

## 4. ホットキーシステム

### 4.1 登録フロー

```
起動
  │
  ├─ config.popup_hotkey を登録
  │     → popup.show() を root.after(0, ...) でメインスレッドへ
  │
  └─ 各 preset.hotkey を登録
        → apply_preset(preset) を root.after(0, ...) でメインスレッドへ

設定変更（config.on_change）
  └─ keyboard.unhook_all_hotkeys() → 再登録
```

### 4.2 ホットキー文字列形式

`keyboard` ライブラリの形式に準拠：

```
ctrl+alt+w
ctrl+shift+1
alt+f1
```

---

## 5. エラーハンドリング

| ケース | 処理 |
|--------|------|
| 依存ライブラリ未インストール | 起動時にダイアログ表示 → 終了 |
| ホットキー登録失敗 | `[WARN]` をコンソール出力、他のキーは継続登録 |
| ウィンドウが見つからない | スキップ（apply_preset の結果に `False` を記録） |
| 最大化ウィンドウの移動 | `SW_RESTORE` 後に `SetWindowPos` |
| 数値パースエラー（レイアウト値） | その行をスキップして保存 |

---

## 6. 制限事項

- マルチモニター対応: プライマリモニターのみ（将来対応予定）
- UAC昇格が必要なウィンドウ（タスクマネージャー等）は移動不可
- `keyboard` ライブラリは管理者権限を推奨
- WSL2 から実行する場合は `py.exe -3 main.py` で Windows Python を使用
