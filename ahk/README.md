# Window Manager - AutoHotkey 版

WSL・Python 不要のスタンドアロン版。**AutoHotkey v2** のみで動作します。

---

## 必要なもの

- [AutoHotkey v2](https://www.autohotkey.com/) のみ

---

## 起動方法

`WindowManager.ahk` をダブルクリックするだけ。タスクトレイにアイコンが表示されます。

---

## コマンド一覧

### ホットキー

| 操作 | 内容 |
|------|------|
| `Ctrl+Alt+W` | ポップアップメニュー表示 |
| `Ctrl+Alt+1` | WSL 横並び（デフォルト） |
| `Ctrl+Alt+2` | Chrome 横並び（デフォルト） |
| プリセットで設定したキー | 対応プリセットを即実行 |

### トレイアイコン右クリック

| メニュー | 内容 |
|----------|------|
| 管理メニュー | プリセット登録・編集・削除 |
| 設定をエクスポート | INI ファイルを任意の場所に保存 |
| 設定をインポート | INI ファイルから設定を読み込み・再起動 |
| 再起動 | スクリプト再読み込み |
| 終了 | スクリプト終了 |

### 管理メニュー内ボタン

| ボタン | 内容 |
|--------|------|
| + 新規 | フォームをクリアして新規入力モードへ |
| 削除 | 選択中のプリセットを削除（確認あり） |
| 選択... | 実行中ウィンドウ一覧からアプリ名を選択 |
| 適用 | ポップアップキーを変更して即反映 |
| 保存 | フォーム内容をプリセットとして保存 |
| インポート | 設定ファイルを読み込み・再起動 |
| エクスポート | 設定ファイルをデスクトップなどに保存 |

---

## ホットキー書式（AHK v2）

| 記号 | キー |
|------|------|
| `^`  | Ctrl |
| `!`  | Alt  |
| `+`  | Shift |
| `#`  | Win  |

例: `^!1` = Ctrl+Alt+1、`^+F1` = Ctrl+Shift+F1

---

## プリセット登録手順

1. トレイ → **管理メニュー** を開く
2. **+ 新規** をクリック
3. 名前・ホットキーを入力
4. アプリ名（`選択...` ボタンで実行中ウィンドウ一覧から選択可）
5. タイトル絞り込み（任意。例: `wsl` → WSL のみ対象）
6. 並べ方を選択（横並び / 縦並び / タイル）
7. **保存**

---

## 設定ファイル

保存先: `%APPDATA%\WindowManager\wm_config.ini`

```ini
[General]
PopupHotkey=^!w
PresetCount=2

[Preset_1]
Name=WSL 横並び
Hotkey=^!1
Mode=arrange
App=WindowsTerminal
Title=wsl
Arrange=horizontal

[Preset_2]
Name=Chrome 横並び
Hotkey=^!2
Mode=arrange
App=chrome
Title=
Arrange=horizontal
```

---

## Python 版との違い

| 項目 | Python 版 | AHK 版 |
|------|-----------|--------|
| 必要環境 | Python + WSL2 | AutoHotkey v2 のみ |
| 配布 | WSL 必要 | .ahk 単体で動作 |
| カスタム UI | tkinter | AHK Gui |
| 設定形式 | JSON | INI |
| 設定保存先 | スクリプトと同フォルダ | %APPDATA%\WindowManager |
| exe 化 | 不可 | Ahk2Exe でコンパイル可 |
| 現在配置キャプチャ | 対応 | 未対応 |
| クイックレイアウト14種 | 対応 | 未対応 |
