# Window Manager - AutoHotkey 版

WSL・Python 不要のスタンドアロン版。
**AutoHotkey v2** のみで動作します。

---

## 必要なもの

- [AutoHotkey v2](https://www.autohotkey.com/) のみ

---

## 起動方法

`WindowManager.ahk` をダブルクリックするだけ。

タスクトレイにアイコンが表示されます。

---

## 使い方

| 操作 | 内容 |
|------|------|
| `Ctrl+Alt+W` | ポップアップメニューを表示 |
| `Ctrl+Alt+1` | WSL横並び（デフォルト） |
| `Ctrl+Alt+2` | Chrome横並び（デフォルト） |
| トレイ右クリック → 管理メニュー | プリセット登録・削除 |
| トレイ右クリック → 再起動 | 設定再読み込み |

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

## プリセット登録

1. トレイ → **管理メニュー** を開く
2. **＋ 新規** をクリック
3. 名前・ホットキーを入力
4. アプリ名（`選択...`ボタンで一覧から選択可）
5. タイトル絞り込み（任意。例: `wsl` → WSLのみ）
6. 並べ方を選択（横並び / 縦並び / タイル）
7. **保存**

---

## 設定ファイル

`wm_config.ini`（スクリプトと同じフォルダに自動生成）

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

## Python版との違い

| 項目 | Python版 | AHK版 |
|------|---------|-------|
| 必要環境 | Python + WSL2 | AutoHotkey v2 のみ |
| 配布 | WSL必要 | .ahk単体で動作 |
| カスタムUI | tkinter | AHK Gui |
| 設定形式 | JSON | INI |
| exe化 | 不可 | Ahk2Exe でコンパイル可 |
