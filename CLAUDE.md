# window-manager プロジェクト ルール・既知バグ記録

## 作業開始時の必須確認

**必ずメモリファイルを読むこと（毎回）**:

```
~/.claude/projects/-home-matuhiro-python-window-manager/memory/MEMORY.md
```

- `dashboard.md` — 設計・ファイル構成・バグ修正履歴
- `ahk-syntax.md` — AHK v2 構文の落とし穴
- `work-log.md` — 日付別作業ログ

**作業終了時**: `work-log.md` に今回の作業を追記すること。

## プロジェクト概要
- Windows 11向けウィンドウ配置管理ツール（Python版 + AHK v2版）
- AHK版（`ahk/WindowManager.ahk`）はスタンドアロンで動作
- Python版はWindows専用（pywin32必須）、WSL/Linuxでは動作しない

---

## AHK v2 既知バグ・修正記録

### 1. `GetNext` の第2引数
- **誤**: `GetNext(0, "Selected")`
- **正**: `GetNext(0, "Focused")`
- AHK v2 では "Selected" は無効。ListView の選択行取得は "Focused" を使う。

### 2. `+Modal` オプション
- **誤**: `Gui("+Owner" hwnd " +Modal", ...)`
- **正**: `Gui("+Owner" hwnd, ...)` + `WinWaitClose` で代用
- AHK v2 では `+Modal` は無効なオプション。

### 3. 複数ウィンドウが1つしか配置されない（FindWindows）
- **原因1**: `WinGetList()` 全件スキャン + 手動フィルタでは一部ウィンドウが漏れる
- **正**: `WinGetList("ahk_exe chrome.exe")` のようにexe名で直接検索する
- **原因2**: Chrome等マルチプロセスアプリは内部ヘルパーウィンドウも返す
- **正**: `WS_EX_TOOLWINDOW`(0x80)や`WS_CAPTION`(0xC00000)なしのウィンドウを除外
- **原因3**: Chrome等は`WinActivate`してからでないと`WinMove`が効かない
- **正**: `RestoreAndMove` で `WinRestore → WinActivate → WinWaitActive → WinMove` の順で実行

### 4. Windows Terminal (WSL) が配置されない
- **原因**: `IsRealAppWindow` の `WS_CAPTION`(0xC00000) チェックが WinUI/UWP アプリを除外
- **正**: `WS_CAPTION` チェックを削除。`WS_EX_TOOLWINDOW` チェックのみ残す

### 5. ホットキー変更後に再起動が必要
- **原因**: `BtnSaveEvt` で `Presets[selIdx]` を新ホットキーで上書き**後**に
  `UnregisterHotkeys()` を呼ぶため、古いホットキーが解除されずに残る
- **正**: Presets 更新前に `oldHk` を保存し、変更がある場合は先に `Hotkey(oldHk, "Off")` する

### 6. ホットキー重複チェックなし
- **正**: 保存時にポップアップキー・システム予約キー（^!t, ^!q）・他プリセットと重複確認

### 7. ミニバーのドラッグが動かない
- **原因**: `-Caption` ウィンドウに `WM_LBUTTONDOWN` + `PostMessage(0xA1)` の方式は
  Text コントロールに `SS_NOTIFY` (0x100) がないとマウスイベントを受け取れない
- **正**: `OnMessage(0x0084, ...)` で `WM_NCHITTEST` を横取りし、ヘッダー領域で
  `HTCAPTION` (2) を返す → OSがドラッグを自動処理する

### 5. 「アクティブをタイル」でスクリプト自身が対象になる
- **原因**: ミニバーや管理メニューをクリックすると、そのウィンドウ（AutoHotkey）が
  アクティブになり、`WinGetProcessName("A")` がAHKプロセスを返す
- **正**: `WinGetPID("A") = DllCall("GetCurrentProcessId")` でスクリプト自身を除外

### 6. テスト実行ボタンで結果が見えない
- **原因**: 管理ウィンドウが前面にあり、配置後のウィンドウが隠れる
- **正**: `ApplyPreset` 前に管理ウィンドウを `Minimize()` し、800ms後に `Show()` で復元

---

## AHK v2 開発ルール

- `OnEvent` のコールバックはラムダ・クロージャを避け、トップレベル関数名を使う
  （管理GUIのように複雑なイベントハンドラは特に）
- コントロール参照は `g_C` (Map) 経由で共有する
- ホットキー登録/解除は `RegisterHotkeys` / `UnregisterHotkeys` をペアで管理する
- `-Caption +ToolWindow` のフローティングウィンドウのドラッグは `WM_NCHITTEST` で実装
