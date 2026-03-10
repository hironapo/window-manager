# Window Manager 仕様書

バージョン: 2.0.0
対象OS: Windows 11
言語: Python 3.8+ / AutoHotkey v2

---

## 1. 概要

Windows 11 上で動作するウィンドウ配置管理ツール。
グローバルホットキーのリッスンと GUI を組み合わせ、登録されたプリセットに従ってウィンドウを自動配置します。

Python 版と AutoHotkey 版の 2 実装を提供します。

---

## 2. Python 版アーキテクチャ

### 2.1 コンポーネント構成

```
┌──────────────────────────────────────────────────┐
│  main.py  WindowManagerApp                        │
│  ├── ConfigManager     設定読み書き（JSON）        │
│  ├── keyboard daemon   グローバルホットキー監視    │
│  ├── PopupMenu         ポップアップ UI             │
│  └── ManagementWindow  管理 UI                    │
└──────────────────────────────────────────────────┘
          ↓ apply_preset()
┌──────────────────────────────────────────────────┐
│  window_mgr.py                                    │
│  ├── get_work_area()        作業領域取得           │
│  ├── get_all_windows()      ウィンドウ列挙         │
│  ├── find_all_windows_by_app() 複数ウィンドウ検索  │
│  ├── arrange_windows()      等分割配置             │
│  └── move_window()          SetWindowPos で配置   │
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

## 3. Python 版モジュール仕様

### 3.1 config_mgr.py — ConfigManager

**責務：** `config.json` の読み書きとプリセットの CRUD

#### メソッド

| メソッド | 引数 | 戻り値 | 説明 |
|---------|------|--------|------|
| `get(key, default)` | key: str | Any | 設定値取得 |
| `set(key, value)` | key: str, value: Any | — | 設定値保存（即座に書き込み） |
| `get_presets()` | — | list[dict] | 全プリセット取得 |
| `add_preset(preset)` | preset: dict | str | 追加（UUID を id として付与） |
| `update_preset(id, updates)` | id: str, updates: dict | bool | 部分更新 |
| `delete_preset(id)` | id: str | — | 削除 |

#### コールバック

```python
config.on_change = callable  # 保存のたびに呼ばれる → ホットキー再登録に使用
```

### 3.2 window_mgr.py — ウィンドウ操作

#### 関数

| 関数 | 説明 |
|------|------|
| `get_work_area()` | SPI_GETWORKAREA でタスクバー除外の作業領域を返す |
| `get_all_windows()` | EnumWindows で可視ウィンドウ一覧を返す |
| `find_all_windows_by_app(app, title_filter)` | 複数ウィンドウ対応。title_filter で絞り込み可 |
| `arrange_windows(hwnds, direction)` | horizontal / vertical / tile に等分割配置 |
| `apply_preset(preset)` | mode='arrange' または mode='custom' でプリセット適用 |
| `capture_current_layout()` | 現在のウィンドウ位置を比率で取得 |

#### プリセットモード

| モード | 動作 |
|--------|------|
| `arrange` | `app` + `title` に一致する全ウィンドウを `arrange` 方向に自動等分割 |
| `custom` | `windows` 配列の各エントリを x/y/w/h 比率で個別配置 |

#### 座標変換

```
比率 → ピクセル座標
  px_x = work_x + layout.x × work_w
  px_y = work_y + layout.y × work_h
  px_w = layout.w × work_w
  px_h = layout.h × work_h
```

使用 Win32 API:
- `SystemParametersInfoW(SPI_GETWORKAREA)` — 作業領域取得
- `EnumWindows` + `GetWindowThreadProcessId` + `psutil.Process` — exe 名取得
- `GetWindowPlacement` / `ShowWindow(SW_RESTORE)` — 最大化解除
- `SetWindowPos` — 位置・サイズ設定

---

## 4. AHK 版アーキテクチャ

### 4.1 ファイル構成

```
ahk/
├── WindowManager.ahk   # スクリプト本体（単一ファイル）
└── README.md
```

設定ファイル保存先: `%APPDATA%\WindowManager\wm_config.ini`

### 4.2 主要関数

| 関数 | 説明 |
|------|------|
| `LoadConfig()` | INI ファイルを読み込み Presets 配列を構築 |
| `SaveConfig()` | Presets 配列を INI ファイルに書き込み |
| `RegisterHotkeys()` | PopupHotkey とプリセットキーを登録 |
| `MakePresetHandler(preset)` | ループキャプチャ問題を回避するファクトリ関数 |
| `FindWindows(app, titleFilter)` | exe 名/タイトルで一致するウィンドウ HWND 配列を返す |
| `ArrangeWindows(hwnds, direction)` | horizontal / vertical / tile に等分割配置 |
| `ApplyPreset(preset)` | arrange / custom モードでプリセット適用 |
| `ShowPopup()` | 画面上部中央にポップアップメニュー表示 |
| `ShowManagement()` | モダン管理 GUI を表示 |
| `ExportConfig()` | 設定を任意パスの INI ファイルにコピー |
| `ImportConfig()` | 外部 INI ファイルをインポートして Reload() |

### 4.3 GUI イベントハンドラ（トップレベル関数）

| 関数 | 登録先 |
|------|--------|
| `MgmtCloseEvt` | 管理 GUI Close |
| `LvSelectEvt` | ListView ItemSelect |
| `SaveHkEvt` | ポップアップキー「適用」ボタン |
| `BtnNewEvt` | 「+ 新規」ボタン |
| `BtnDeleteEvt` | 「削除」ボタン |
| `BtnSaveEvt` | 「保存」ボタン |
| `BtnPickAppEvt` | 「選択...」ボタン |
| `PickSelectEvt` | PickWindow ダイアログ「選択」 |
| `PickCancelEvt` | PickWindow ダイアログ「キャンセル」 |

コントロール参照はグローバル Map `g_C` 経由で共有します。

---

## 5. AHK v2 実装における注意点

### 5.1 ブロッククロージャは関数内で使用不可

AHK v2 では `(*) { ... }` 形式のブロッククロージャを**関数本体の内側で定義するとパースエラーになる**ことがある。

```ahk
; NG: 関数内でのブロッククロージャ
MyFunc() {
    handler := (*) {   ; ← パースエラーになる場合がある
        DoSomething()
    }
    ctrl.OnEvent("Click", handler)
}

; OK: トップレベルで定義
MyHandler(*) {
    DoSomething()
}
MyFunc() {
    ctrl.OnEvent("Click", MyHandler)
}
```

**対策:** イベントハンドラはすべてトップレベル関数として定義し、コントロール参照はグローバル Map で共有する。

### 5.2 ループ内クロージャのキャプチャ問題

```ahk
; NG: pRef は関数スコープで共有 → 全ハンドラが最後の p を使う
for p in Presets {
    pRef := p
    Hotkey(p.Hotkey, (*) => ApplyPreset(pRef))
}

; OK: ファクトリ関数で独立スコープを作る
MakePresetHandler(preset) {
    return (*) => ApplyPreset(preset)  ; preset は引数なので独立
}
for p in Presets {
    Hotkey(p.Hotkey, MakePresetHandler(p))
}
```

### 5.3 `else if` をクロージャ末尾で使用不可

```ahk
; NG: クロージャ/関数末尾の else if はパースエラー
handler := (*) {
    if cond1
        a := 1
    else if cond2   ; ← 末尾の } で "Unexpected }" エラー
        a := 2
}

; OK: 三項演算子に書き換える
a := cond1 ? 1 : (cond2 ? 2 : 0)

; OK: 独立した if 文に分割する
if cond1
    a := 1
if cond2
    a := 2
```

### 5.4 ファットアロー vs ブロッククロージャ

| 形式 | 使用可能な場所 | 注意 |
|------|--------------|------|
| `(*) => 単一式` | どこでも ○ | 単一式のみ。return 不要 |
| `(*) { 複数文 }` | トップレベルのみ ○ | 関数内で使うとパースエラーの可能性 |
| 名前付きトップレベル関数 | どこでも ○ | 最も安全。推奨 |

### 5.5 IniRead / IniWrite はネイティブパスのみ対応

Windows API の `WritePrivateProfileString` を使用するため、UNC パス（`\\wsl.localhost\...`）は書き込み不可。

```ahk
; NG: WSL パスへの書き込みは失敗する
global ConfigFile := A_ScriptDir "\wm_config.ini"  ; WSL から実行時に NG

; OK: Windows ネイティブパスを使う
global ConfigFile := A_AppData "\WindowManager\wm_config.ini"
```

### 5.6 エスケープ文字（AHK v2）

| 記法 | 意味 |
|------|------|
| `` `n `` | 改行 |
| `` `t `` | タブ |
| `` `` `` | バッククォート自身 |
| `"` (文字列内) | `""` でエスケープ |

AHK v1 の `\n` `\t` は使用不可。

---

## 6. エラーハンドリング

| ケース | Python 版 | AHK 版 |
|--------|-----------|--------|
| 依存ライブラリ未インストール | ダイアログ → 終了 | — |
| ホットキー登録失敗 | `[WARN]` をコンソール出力 | `try` で握りつぶし |
| ウィンドウが見つからない | スキップ | スキップ |
| 最大化ウィンドウの移動 | SW_RESTORE 後に移動 | WinRestore 後に WinMove |
| 設定ファイル書き込み失敗 | — | エラーダイアログ表示 |

---

## 7. 制限事項

- マルチモニター: プライマリモニターのみ対応（将来対応予定）
- UAC 昇格が必要なウィンドウ（タスクマネージャー等）は移動不可
- Python 版は `keyboard` ライブラリの制約で管理者権限を推奨
- AHK 版のカスタムモードは手動で INI を編集する必要がある
