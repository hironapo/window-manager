#Requires AutoHotkey v2.0
#SingleInstance Force
SetWorkingDir(A_ScriptDir)

; ═══════════════════════════════════════════════════════════════
;  Window Manager  - AutoHotkey v2 スタンドアロン版
;  WSL・Python 不要。AutoHotkey v2 のみで動作。
;
;  起動   : WindowManager.ahk をダブルクリック
;  ポップアップ: Ctrl+Alt+W（変更可）
;  管理   : トレイアイコン右クリック → 管理メニュー
;
;  ホットキー書式（AHK v2 形式）
;    ^ = Ctrl  ! = Alt  + = Shift  # = Win
;    例） ^!1 = Ctrl+Alt+1
; ═══════════════════════════════════════════════════════════════

; ── グローバル変数 ───────────────────────────────────────────
global ConfigFile     := A_AppData "\WindowManager\wm_config.ini"
global Presets        := []
global PopupHotkey    := "^!w"
global mgmtGui        := ""
global selIdx         := 0
; 管理GUIのコントロール参照（トップレベルハンドラから参照）
global g_C            := Map()
; ミニバー
global miniBar        := ""
global miniBarVisible := true

; ─── 起動 ───────────────────────────────────────────────────
LoadConfig()
RegisterHotkeys()
SetupTray()
SetupMiniBar()
return

; ═══════════════════════════════════════════════════════════════
;  CONFIG  (INI 形式)
; ═══════════════════════════════════════════════════════════════

LoadConfig() {
    global ConfigFile, Presets, PopupHotkey
    Presets := []
    if !FileExist(ConfigFile) {
        WriteDefaultConfig()
        LoadConfig()
        return
    }
    try PopupHotkey := IniRead(ConfigFile, "General", "PopupHotkey", "^!w")
    count := Integer(IniRead(ConfigFile, "General", "PresetCount", "0"))
    loop count {
        sec := "Preset_" A_Index
        Presets.Push({
            Name:    IniRead(ConfigFile, sec, "Name",    "(名前なし)"),
            Hotkey:  IniRead(ConfigFile, sec, "Hotkey",  ""),
            Mode:    IniRead(ConfigFile, sec, "Mode",    "arrange"),
            App:     IniRead(ConfigFile, sec, "App",     ""),
            Title:   IniRead(ConfigFile, sec, "Title",   ""),
            Arrange: IniRead(ConfigFile, sec, "Arrange", "horizontal"),
            Windows: IniRead(ConfigFile, sec, "Windows", ""),
        })
    }
}

SaveConfig() {
    global ConfigFile, Presets, PopupHotkey
    IniWrite(PopupHotkey,    ConfigFile, "General", "PopupHotkey")
    IniWrite(Presets.Length, ConfigFile, "General", "PresetCount")
    loop Presets.Length {
        p   := Presets[A_Index]
        sec := "Preset_" A_Index
        IniWrite(p.Name,    ConfigFile, sec, "Name")
        IniWrite(p.Hotkey,  ConfigFile, sec, "Hotkey")
        IniWrite(p.Mode,    ConfigFile, sec, "Mode")
        IniWrite(p.App,     ConfigFile, sec, "App")
        IniWrite(p.Title,   ConfigFile, sec, "Title")
        IniWrite(p.Arrange, ConfigFile, sec, "Arrange")
        IniWrite(p.Windows, ConfigFile, sec, "Windows")
    }
}

WriteDefaultConfig() {
    global ConfigFile
    DirCreate(A_AppData "\WindowManager")
    IniWrite("^!w", ConfigFile, "General", "PopupHotkey")
    IniWrite(2,     ConfigFile, "General", "PresetCount")

    IniWrite("WSL 横並び",      ConfigFile, "Preset_1", "Name")
    IniWrite("^!1",             ConfigFile, "Preset_1", "Hotkey")
    IniWrite("arrange",         ConfigFile, "Preset_1", "Mode")
    IniWrite("WindowsTerminal", ConfigFile, "Preset_1", "App")
    IniWrite("",                ConfigFile, "Preset_1", "Title")
    IniWrite("horizontal",      ConfigFile, "Preset_1", "Arrange")
    IniWrite("",                ConfigFile, "Preset_1", "Windows")

    IniWrite("Chrome 横並び",   ConfigFile, "Preset_2", "Name")
    IniWrite("^!2",             ConfigFile, "Preset_2", "Hotkey")
    IniWrite("arrange",         ConfigFile, "Preset_2", "Mode")
    IniWrite("chrome",          ConfigFile, "Preset_2", "App")
    IniWrite("",                ConfigFile, "Preset_2", "Title")
    IniWrite("horizontal",      ConfigFile, "Preset_2", "Arrange")
    IniWrite("",                ConfigFile, "Preset_2", "Windows")
}

; ═══════════════════════════════════════════════════════════════
;  HOTKEYS
; ═══════════════════════════════════════════════════════════════

RegisterHotkeys() {
    global Presets, PopupHotkey
    try Hotkey(PopupHotkey, ShowPopup)
    try Hotkey("^!t", TileActiveProcess)
    try Hotkey("^!q", ToggleMiniBar)
    for p in Presets {
        if p.Hotkey != ""
            try Hotkey(p.Hotkey, MakePresetHandler(p))
    }
}

MakePresetHandler(preset) {
    return (*) => ApplyPreset(preset)
}

UnregisterHotkeys() {
    global Presets, PopupHotkey
    try Hotkey(PopupHotkey, "Off")
    try Hotkey("^!t", "Off")
    try Hotkey("^!q", "Off")
    for p in Presets {
        if p.Hotkey != ""
            try Hotkey(p.Hotkey, "Off")
    }
}

ReloadHotkeys() {
    UnregisterHotkeys()
    LoadConfig()
    RegisterHotkeys()
    BuildMiniBar()
}

; ═══════════════════════════════════════════════════════════════
;  TRAY
; ═══════════════════════════════════════════════════════════════

SetupTray() {
    A_TrayMenu.Delete()
    A_TrayMenu.Add("管理メニュー",           (*) => ShowManagement())
    A_TrayMenu.Add("ミニバー 表示/非表示",   (*) => ToggleMiniBar())
    A_TrayMenu.Add()
    A_TrayMenu.Add("設定をエクスポート",     (*) => ExportConfig())
    A_TrayMenu.Add("設定をインポート",       (*) => ImportConfig())
    A_TrayMenu.Add()
    A_TrayMenu.Add("再起動",                 (*) => Reload())
    A_TrayMenu.Add("終了",                   (*) => ExitApp())
    A_TrayMenu.Default := "管理メニュー"
    TraySetIcon("shell32.dll", 238)
    A_IconTip := "Window Manager  (^!Q: ミニバー)"
}

; ═══════════════════════════════════════════════════════════════
;  WINDOW OPERATIONS
; ═══════════════════════════════════════════════════════════════

GetWorkArea() {
    MonitorGetWorkArea(, &wx, &wy, &wr, &wb)
    return {x: wx, y: wy, w: wr - wx, h: wb - wy}
}

GetAllWindows() {
    result := []
    for hwnd in WinGetList() {
        try {
            title := WinGetTitle("ahk_id " hwnd)
            if title = ""
                continue
            exe := WinGetProcessName("ahk_id " hwnd)
            result.Push({hwnd: hwnd, title: title, exe: exe})
        }
    }
    return result
}

; ウィンドウが「実際のアプリウィンドウ」か判定
; WS_EX_TOOLWINDOW（内部ヘルパー）とタイトルなしを除外
; ※ WS_CAPTION チェックは除外: Windows Terminal 等 WinUI/UWP アプリが除外されるため
IsRealAppWindow(hwnd) {
    try {
        if WinGetTitle("ahk_id " hwnd) = ""
            return false
        exStyle := WinGetExStyle("ahk_id " hwnd)
        if exStyle & 0x80  ; WS_EX_TOOLWINDOW（内部ヘルパー）
            return false
        return true
    } catch {
        return false
    }
}

FindWindows(app, titleFilter := "") {
    appL   := StrLower(StrReplace(app, ".exe", ""))
    titleL := StrLower(titleFilter)
    result := []
    seen   := Map()

    ; exe名でウィンドウ検索
    try {
        for hwnd in WinGetList("ahk_exe " appL ".exe") {
            if seen.Has(hwnd) || !IsRealAppWindow(hwnd)
                continue
            title := WinGetTitle("ahk_id " hwnd)
            if titleL != "" && !InStr(StrLower(title), titleL)
                continue
            result.Push(hwnd)
            seen[hwnd] := 1
        }
    }

    ; exe名でヒットしない場合: exe名またはタイトルで補完
    if result.Length = 0 {
        for w in GetAllWindows() {
            if seen.Has(w.hwnd) || !IsRealAppWindow(w.hwnd)
                continue
            exeL := StrLower(StrReplace(w.exe, ".exe", ""))
            tL   := StrLower(w.title)
            if !InStr(exeL, appL) && !InStr(tL, appL)
                continue
            if titleL != "" && !InStr(tL, titleL)
                continue
            result.Push(w.hwnd)
            seen[w.hwnd] := 1
        }
    }

    ; 最終フォールバック: タイトルのみで検索（WSL等exe名が一致しないケース）
    if result.Length = 0 && titleL != "" {
        for w in GetAllWindows() {
            if seen.Has(w.hwnd) || !IsRealAppWindow(w.hwnd)
                continue
            if InStr(StrLower(w.title), titleL)
                result.Push(w.hwnd)
        }
    }

    return result
}

; ウィンドウを復元・アクティブ化してから移動（Chrome等で必要）
RestoreAndMove(hwnd, x, y, w, h) {
    WinRestore("ahk_id " hwnd)
    WinActivate("ahk_id " hwnd)
    WinWaitActive("ahk_id " hwnd,, 1)
    WinMove(x, y, w, h, "ahk_id " hwnd)
}

ArrangeWindows(hwnds, direction) {
    n := hwnds.Length
    if n = 0 {
        TrayTip("Window Manager", "ウィンドウが見つかりませんでした", 2)
        return
    }
    wa := GetWorkArea()
    if direction = "horizontal" {
        w := wa.w // n
        i := 0
        for hwnd in hwnds {
            RestoreAndMove(hwnd, wa.x + i*w, wa.y, w, wa.h)
            i++
        }
    } else if direction = "vertical" {
        h := wa.h // n
        i := 0
        for hwnd in hwnds {
            RestoreAndMove(hwnd, wa.x, wa.y + i*h, wa.w, h)
            i++
        }
    } else if direction = "tile" {
        cols := Ceil(Sqrt(n))
        rows := Ceil(n / cols)
        tw   := wa.w // cols
        th   := wa.h // rows
        i    := 0
        for hwnd in hwnds {
            RestoreAndMove(hwnd, wa.x + Mod(i,cols)*tw, wa.y + (i//cols)*th, tw, th)
            i++
        }
    }
}

ApplyPreset(preset) {
    if preset.Mode = "arrange" {
        hwnds := FindWindows(preset.App, preset.Title)
        ArrangeWindows(hwnds, preset.Arrange)
        return
    }
    if preset.Windows = ""
        return
    wa   := GetWorkArea()
    pool := Map()
    cur  := Map()
    for def in StrSplit(preset.Windows, ";") {
        p := StrSplit(def, ",")
        if p.Length < 6
            continue
        key := p[1] "|" p[2]
        if !pool.Has(key) {
            pool[key] := FindWindows(Trim(p[1]), Trim(p[2]))
            cur[key]  := 1
        }
    }
    for def in StrSplit(preset.Windows, ";") {
        p := StrSplit(def, ",")
        if p.Length < 6
            continue
        key   := p[1] "|" p[2]
        idx   := cur.Has(key) ? cur[key] : 1
        hwnds := pool.Has(key) ? pool[key] : []
        if idx <= hwnds.Length {
            hwnd := hwnds[idx]
            cur[key] := idx + 1
            x := wa.x + Round(Float(p[3]) * wa.w)
            y := wa.y + Round(Float(p[4]) * wa.h)
            w := Round(Float(p[5]) * wa.w)
            h := Round(Float(p[6]) * wa.h)
            WinRestore("ahk_id " hwnd)
            WinMove(x, y, w, h, "ahk_id " hwnd)
        }
    }
}

; アクティブウィンドウと同じプロセスの全ウィンドウをタイル表示 (Ctrl+Alt+T)
TileActiveProcess(*) {
    try {
        hwndActive := WinGetID("A")
        exe := WinGetProcessName("ahk_id " hwndActive)
    } catch {
        return
    }
    if exe = ""
        return
    ; スクリプト自身のウィンドウ（管理メニュー等）は除外
    if WinGetPID("ahk_id " hwndActive) = DllCall("GetCurrentProcessId")
        return
    hwnds := FindWindows(StrReplace(exe, ".exe", ""))
    if hwnds.Length = 0
        return
    ArrangeWindows(hwnds, "tile")
    name := StrReplace(exe, ".exe", "")
    ToolTip("タイル完了: " name " (" hwnds.Length " ウィンドウ)")
    SetTimer(() => ToolTip(), -2000)
}

; ═══════════════════════════════════════════════════════════════
;  MINI BAR（常時表示フローティングメニュー）
;  Ctrl+Alt+Q で表示/非表示トグル、ヘッダーをドラッグで移動
; ═══════════════════════════════════════════════════════════════

SetupMiniBar() {
    OnMessage(0x0084, OnMiniNcHitTest)  ; WM_NCHITTEST（ドラッグ用）
    OnMessage(0x0003, OnMiniBarMove)    ; WM_MOVE（位置保存）
    BuildMiniBar()
}

BuildMiniBar() {
    global miniBar, miniBarVisible, Presets, ConfigFile, miniDragHwnd

    if IsObject(miniBar) {
        miniBar.Destroy()
        miniBar := ""
    }

    bx := Integer(IniRead(ConfigFile, "MiniBar", "X", A_ScreenWidth - 170))
    by := Integer(IniRead(ConfigFile, "MiniBar", "Y", 10))
    bw := 162

    miniBar := Gui("-Caption +AlwaysOnTop +ToolWindow", "WM Mini")
    miniBar.BackColor := "1E1E2E"
    miniBar.SetFont("s9", "Meiryo")
    miniBar.MarginX := 0
    miniBar.MarginY := 0

    ; ヘッダー（ドラッグ用・タイトル）
    miniBar.Add("Text", "x0 y0 w142 h20 0x201 c9999CC Background16213E", "  ⚡ WM")
    ; 非表示ボタン（×）
    miniBar.Add("Text", "x142 y0 w20 h20 0x201 cFF8888 Background16213E", "×").OnEvent("Click", (*) => ToggleMiniBar())

    y := 21
    miniBar.Add("Text", "x0 y" y " w162 h1 Background333355", "")
    y += 4

    ; プリセットボタン（ホットキーを右側に表示）
    for p in Presets {
        label := SubStr(p.Name, 1, 14)
        if p.Hotkey != ""
            label .= "  [" p.Hotkey "]"
        miniBar.Add("Button", "x2 y" y " w158 h22", label).OnEvent("Click", MakeMiniHandler(p))
        y += 24
    }

    ; 固定機能ボタン
    miniBar.Add("Text", "x0 y" y " w162 h1 Background333355", "")
    y += 4
    miniBar.Add("Button", "x2 y" y " w158 h22", "▶ アクティブをタイル").OnEvent("Click", (*) => TileActiveProcess())
    y += 24
    miniBar.Add("Button", "x2 y" y " w158 h22", "⚙ 管理メニュー").OnEvent("Click", (*) => ShowManagement())
    y += 26

    miniBar.Show("x" bx " y" by " w" bw " h" y " NoActivate")
    WinSetTransparent(215, "ahk_id " miniBar.Hwnd)

    if !miniBarVisible
        miniBar.Hide()
}

MakeMiniHandler(preset) {
    return (*) => ApplyPreset(preset)
}

ToggleMiniBar(*) {
    global miniBar, miniBarVisible
    if !IsObject(miniBar)
        return
    if miniBarVisible {
        miniBar.Hide()
        miniBarVisible := false
    } else {
        miniBar.Show("NoActivate")
        miniBarVisible := true
    }
}

OnMiniNcHitTest(wParam, lParam, msg, hwnd) {
    global miniBar
    if !IsObject(miniBar)
        return
    ; ミニバー本体またはその子コントロールのみ対象
    barHwnd := miniBar.Hwnd
    if hwnd != barHwnd {
        if DllCall("GetParent", "Ptr", hwnd, "Ptr") != barHwnd
            return
    }
    ; スクリーン座標 → ウィンドウ相対座標（符号拡張考慮）
    WinGetPos(&wx, &wy,,, "ahk_id " barHwnd)
    screenX := lParam & 0xFFFF
    screenY := (lParam >> 16) & 0xFFFF
    if screenX >= 0x8000
        screenX -= 0x10000
    if screenY >= 0x8000
        screenY -= 0x10000
    relX := screenX - wx
    relY := screenY - wy
    ; ヘッダー領域（×ボタン x>=142 は除外）でHTCAPTIONを返す
    if relY >= 0 && relY < 22 && relX >= 0 && relX < 142
        return 2  ; HTCAPTION → OSがドラッグを処理
}

OnMiniBarMove(wParam, lParam, msg, hwnd) {
    global miniBar
    if !IsObject(miniBar) || hwnd != miniBar.Hwnd
        return
    SetTimer(SaveMiniBarPos, -800)
}

SaveMiniBarPos() {
    global miniBar, ConfigFile
    if !IsObject(miniBar)
        return
    WinGetPos(&wx, &wy,,, "ahk_id " miniBar.Hwnd)
    IniWrite(wx, ConfigFile, "MiniBar", "X")
    IniWrite(wy, ConfigFile, "MiniBar", "Y")
}

; ═══════════════════════════════════════════════════════════════
;  POPUP MENU
; ═══════════════════════════════════════════════════════════════

ShowPopup(*) {
    global Presets
    if Presets.Length = 0 {
        MsgBox("プリセットがありません。`nトレイ右クリック → 管理メニューから追加してください。",
               "Window Manager", "0x40")
        return
    }
    m := Menu()
    for p in Presets {
        label := p.Name
        if p.Hotkey != ""
            label .= "`t" p.Hotkey
        m.Add(label, MakePresetHandler(p))
    }
    m.Add()
    m.Add("管理メニュー", (*) => ShowManagement())
    x := A_ScreenWidth // 2 - 120
    y := Integer(A_ScreenHeight * 0.12)
    m.Show(x, y)
}

; ═══════════════════════════════════════════════════════════════
;  MANAGEMENT GUI
;  ルール: ShowManagement 内では OnEvent にトップレベル関数名のみ渡す
;          ラムダ・クロージャは一切使わない
;          コントロール参照は g_C (Map) 経由で共有
; ═══════════════════════════════════════════════════════════════

ShowManagement(*) {
    global mgmtGui, Presets, PopupHotkey, selIdx, g_C

    if IsObject(mgmtGui) {
        try mgmtGui.Show()
        return
    }

    selIdx := 0
    SW := 210

    mgmtGui := Gui("+Resize +MinSize800x510", "Window Manager")
    mgmtGui.BackColor := "FFFFFF"
    mgmtGui.SetFont("s10", "Meiryo")
    mgmtGui.OnEvent("Close", MgmtCloseEvt)

    ; ── サイドバー背景
    mgmtGui.Add("Text", "x0 y0 w210 h510 0x0E Background003366", "")

    ; ── ロゴ
    mgmtGui.SetFont("s12 bold", "Meiryo")
    mgmtGui.Add("Text", "x0 y0 w210 h54 0x201 Background003366 cWhite", "Window Manager")
    mgmtGui.SetFont("s10", "Meiryo")

    mgmtGui.Add("Text", "x0 y54 w210 h2 Background0055AA", "")
    mgmtGui.Add("Text", "x14 y64 Background003366 cWhite", "プリセット")

    ; ── プリセット ListView
    lv := mgmtGui.Add("ListView", "x0 y84 w210 h316 -Hdr -Multi NoSort Background003366 cWhite", ["名前"])
    lv.ModifyCol(1, 206)
    SendMessage(0x1024, 0xFFFFFF, 0, lv)
    SendMessage(0x1025, 0x663300, 0, lv)
    SendMessage(0x1001, 0x663300, 0, lv)
    RefreshPresetList(lv)

    mgmtGui.Add("Text",   "x0 y406 w210 h1 Background0055AA", "")
    mgmtGui.Add("Button", "x12 y416 w88 h28",  "+ 新規").OnEvent("Click", BtnNewEvt)
    mgmtGui.Add("Button", "x106 y416 w84 h28", "削除").OnEvent("Click",   BtnDeleteEvt)

    ; ── サイドバー右端線
    mgmtGui.Add("Text", "x210 y0 w2 h510 Background0055AA", "")

    ; ── 右コンテンツ
    CX := 226
    CW := 560
    LW := 106
    IX := CX + LW

    mgmtGui.Add("Text", "x" CX " y18 w" LW, "ポップアップ：")
    eHk := mgmtGui.Add("Edit", "x" IX " y16 w130", PopupHotkey)
    mgmtGui.Add("Button", "x" (IX+136) " y14 w52 h26", "適用").OnEvent("Click", SaveHkEvt)

    mgmtGui.Add("Text", "x" CX " y50 w" CW " h1 BackgroundE8F4FC", "")
    mgmtGui.Add("Text", "x" CX " y51 w" CW " h1 Background0055AA", "")

    mgmtGui.SetFont("s10 bold", "Meiryo")
    mgmtGui.Add("Text", "x" CX " y62", "プリセット詳細")
    mgmtGui.SetFont("s10", "Meiryo")

    mgmtGui.Add("Text", "x" CX " y94 w" LW " Right", "名前：")
    eName := mgmtGui.Add("Edit", "x" IX " y92 w" (CW-LW-4), "")

    mgmtGui.Add("Text", "x" CX " y126 w" LW " Right", "ホットキー：")
    eHotkey := mgmtGui.Add("Edit", "x" IX " y124 w120", "")
    mgmtGui.Add("Button", "x" (IX+126) " y122 w46 h24", "自動").OnEvent("Click", BtnAutoHkEvt)
    mgmtGui.Add("Text", "x" (IX+178) " y127 cGray", "^!1〜^!9  # = Win")

    mgmtGui.Add("Text", "x" CX " y160 w" LW " Right", "モード：")
    mgmtGui.Add("Radio", "x" IX " y160 Checked", "自動タイル")
    mgmtGui.Add("Radio", "x" (IX+92) " y160", "手動配置")

    GBX := CX - 4
    GBW := CW + 4
    mgmtGui.Add("GroupBox", "x" GBX " y182 w" GBW " h158", "アレンジ設定")

    mgmtGui.Add("Text", "x" (GBX+16) " y204 w" LW " Right", "アプリ名：")
    eApp := mgmtGui.Add("Edit", "x" (GBX+LW+16) " y202 w196", "")
    mgmtGui.Add("Button", "x" (GBX+LW+218) " y200 w60 h24", "選択...").OnEvent("Click", BtnPickAppEvt)

    mgmtGui.Add("Text", "x" (GBX+16) " y236 w" LW " Right", "タイトル絞込：")
    eTitle := mgmtGui.Add("Edit", "x" (GBX+LW+16) " y234 w196", "")
    mgmtGui.Add("Text", "x" (GBX+LW+218) " y237 cGray", "例: wsl  (空=全て)")

    mgmtGui.Add("Text", "x" (GBX+16) " y270 w" LW " Right", "並べ方：")
    rH := mgmtGui.Add("Radio", "x" (GBX+LW+16) " y270 Checked", "横並び")
    rV := mgmtGui.Add("Radio", "x" (GBX+LW+92) " y270", "縦並び")
    rT := mgmtGui.Add("Radio", "x" (GBX+LW+168) " y270", "タイル")

    mgmtGui.Add("Text", "x" (GBX+16) " y304 w" (GBW-20) " cGray",
        "実行時に一致する全ウィンドウを自動で等分割配置します。")

    ; ── フッター
    mgmtGui.Add("Text",   "x0 y458 w800 h2 BackgroundE8F4FC", "")
    mgmtGui.Add("Button", "x226 y468 w108 h34", "インポート").OnEvent("Click",  BtnImportEvt)
    mgmtGui.Add("Button", "x340 y468 w108 h34", "エクスポート").OnEvent("Click", BtnExportEvt)
    mgmtGui.Add("Button", "x460 y468 w128 h34", "▶ テスト実行").OnEvent("Click", BtnTestEvt)
    mgmtGui.Add("Button", "x648 y468 w128 h34", "保存").OnEvent("Click",         BtnSaveEvt)

    ; ── コントロール参照を g_C に保存
    g_C["lv"]     := lv
    g_C["eName"]  := eName
    g_C["eHotkey"]:= eHotkey
    g_C["eHk"]    := eHk
    g_C["eApp"]   := eApp
    g_C["eTitle"] := eTitle
    g_C["rH"]     := rH
    g_C["rV"]     := rV
    g_C["rT"]     := rT

    lv.OnEvent("ItemSelect", LvSelectEvt)

    mgmtGui.Show("w800 h510")
}

; ═══════════════════════════════════════════════════════════════
;  管理GUI トップレベルイベントハンドラ
;  ※ ラムダ・クロージャを使わず関数名で OnEvent に登録
; ═══════════════════════════════════════════════════════════════

MgmtCloseEvt(*) {
    global mgmtGui
    mgmtGui := ""
}

LvSelectEvt(*) {
    global selIdx, Presets, g_C
    idx := g_C["lv"].GetNext(0, "Focused")
    if idx < 1 || idx > Presets.Length
        return
    selIdx := idx
    p := Presets[idx]
    g_C["eName"].Value   := p.Name
    g_C["eHotkey"].Value := p.Hotkey
    g_C["eApp"].Value    := p.App
    g_C["eTitle"].Value  := p.Title
    g_C["rH"].Value := 1
    g_C["rV"].Value := (p.Arrange = "vertical") ? 1 : 0
    g_C["rT"].Value := (p.Arrange = "tile")     ? 1 : 0
}

SaveHkEvt(*) {
    global PopupHotkey, g_C
    PopupHotkey := g_C["eHk"].Value
    SaveConfig()
    ReloadHotkeys()
    ToolTip("ポップアップキー: " PopupHotkey)
    SetTimer(() => ToolTip(), -2000)
}

BtnNewEvt(*) {
    global selIdx, g_C
    selIdx := 0
    loop g_C["lv"].GetCount()
        g_C["lv"].Modify(A_Index, "-Select")
    g_C["eName"].Value   := ""
    g_C["eHotkey"].Value := ""
    g_C["eApp"].Value    := ""
    g_C["eTitle"].Value  := ""
    g_C["rH"].Value := 1
}

BtnDeleteEvt(*) {
    global selIdx, Presets, g_C
    if selIdx = 0
        return
    p := Presets[selIdx]
    if MsgBox("「" p.Name "」を削除しますか？", "削除確認", "0x24") != "Yes"
        return
    Presets.RemoveAt(selIdx)
    selIdx := 0
    SaveConfig()
    ReloadHotkeys()
    RefreshPresetList(g_C["lv"])
    g_C["eName"].Value := ""
}

BtnSaveEvt(*) {
    global selIdx, Presets, g_C, PopupHotkey
    name := Trim(g_C["eName"].Value)
    if name = "" {
        MsgBox("名前を入力してください", "エラー", "0x10")
        return
    }
    hk := Trim(g_C["eHotkey"].Value)
    ; ホットキー重複チェック
    if hk != "" {
        if hk = PopupHotkey {
            MsgBox("「" hk "」はポップアップキーと重複しています。", "ホットキー重複", "0x10")
            return
        }
        if hk = "^!t" || hk = "^!q" {
            MsgBox("「" hk "」はシステム予約キーです。", "ホットキー重複", "0x10")
            return
        }
        for i, pr in Presets {
            if i = selIdx
                continue
            if pr.Hotkey = hk {
                MsgBox("「" hk "」はすでに「" pr.Name "」で使用中です。", "ホットキー重複", "0x10")
                return
            }
        }
    }
    dir := "horizontal"
    if g_C["rV"].Value
        dir := "vertical"
    if g_C["rT"].Value
        dir := "tile"
    p := {
        Name:    name,
        Hotkey:  hk,
        Mode:    "arrange",
        App:     Trim(g_C["eApp"].Value),
        Title:   Trim(g_C["eTitle"].Value),
        Arrange: dir,
        Windows: "",
    }
    ; Presets 更新前に古いホットキーを解除（変更前のキーを先に消す）
    if selIdx > 0 {
        oldHk := Presets[selIdx].Hotkey
        if oldHk != "" && oldHk != hk
            try Hotkey(oldHk, "Off")
    }
    if selIdx > 0
        Presets[selIdx] := p
    else
        Presets.Push(p)
    SaveConfig()
    ReloadHotkeys()
    RefreshPresetList(g_C["lv"])
    ToolTip("「" name "」を保存しました")
    SetTimer(() => ToolTip(), -2000)
}

BtnAutoHkEvt(*) {
    AutoAssignHotkey()
}

AutoAssignHotkey() {
    global Presets, PopupHotkey, g_C, selIdx
    used := Map()
    used[PopupHotkey] := 1
    used["^!t"] := 1
    used["^!q"] := 1
    for i, pr in Presets {
        if i != selIdx && pr.Hotkey != ""
            used[pr.Hotkey] := 1
    }
    loop 9 {
        candidate := "^!" A_Index
        if !used.Has(candidate) {
            g_C["eHotkey"].Value := candidate
            return
        }
    }
    MsgBox("^!1〜^!9 がすべて使用中です。", "自動割当", "0x30")
}

BtnPickAppEvt(*) {
    global mgmtGui, g_C
    result := PickWindow(mgmtGui)
    if result != ""
        g_C["eApp"].Value := result
}

BtnTestEvt(*) {
    global selIdx, Presets, g_C, mgmtGui
    name := Trim(g_C["eName"].Value)
    app  := Trim(g_C["eApp"].Value)
    if app = "" {
        MsgBox("アプリ名が入力されていません。", "テスト実行", "0x30")
        return
    }
    dir := "horizontal"
    if g_C["rV"].Value
        dir := "vertical"
    if g_C["rT"].Value
        dir := "tile"
    testPreset := {
        Name:    name,
        Mode:    "arrange",
        App:     app,
        Title:   Trim(g_C["eTitle"].Value),
        Arrange: dir,
        Windows: "",
        Hotkey:  "",
    }
    ; 管理ウィンドウを一時的に最小化して結果を確認しやすくする
    if IsObject(mgmtGui)
        mgmtGui.Minimize()
    ApplyPreset(testPreset)
    Sleep(800)
    if IsObject(mgmtGui)
        mgmtGui.Show()
    ToolTip("テスト実行: " app " → " dir)
    SetTimer(() => ToolTip(), -2000)
}

BtnImportEvt(*) {
    ImportConfig()
}

BtnExportEvt(*) {
    ExportConfig()
}

RefreshPresetList(lv) {
    global Presets
    lv.Delete()
    for p in Presets
        lv.Add(, p.Name)
}

; ═══════════════════════════════════════════════════════════════
;  設定エクスポート・インポート
; ═══════════════════════════════════════════════════════════════

ExportConfig() {
    global ConfigFile
    dest := FileSelect("S16", A_Desktop "\wm_backup.ini",
        "設定ファイルをエクスポート", "設定ファイル (*.ini)")
    if dest = ""
        return
    if !FileCopy(ConfigFile, dest, 1) {
        MsgBox("エクスポートに失敗しました。", "エラー", "0x10")
        return
    }
    ToolTip("エクスポート完了: " dest)
    SetTimer(() => ToolTip(), -3000)
}

ImportConfig() {
    global ConfigFile
    src := FileSelect(1, A_Desktop, "設定ファイルをインポート", "設定ファイル (*.ini)")
    if src = ""
        return
    if MsgBox("現在の設定を上書きしてインポートしますか？`n(スクリプトが再起動されます)",
              "インポート確認", "0x24") != "Yes"
        return
    if !FileCopy(src, ConfigFile, 1) {
        MsgBox("インポートに失敗しました。", "エラー", "0x10")
        return
    }
    Reload()
}

; ═══════════════════════════════════════════════════════════════
;  ウィンドウ選択ダイアログ
; ═══════════════════════════════════════════════════════════════

PickWindow(ownerGui) {
    global g_C
    shared   := Map("result", "")
    dlg      := Gui("+Owner" ownerGui.Hwnd, "ウィンドウを選択")
    dlg.BackColor := "FFFFFF"
    dlg.SetFont("s10", "Meiryo")
    dlg.OnEvent("Close", (*) => 0)
    dlg.Add("Text", "x10 y10", "実行中ウィンドウ（ダブルクリックで選択）")

    wins     := GetAllWindows()
    items    := []
    exeBases := []
    for w in wins {
        eb := StrReplace(w.exe, ".exe", "")
        items.Push(eb "  —  " SubStr(w.title, 1, 52))
        exeBases.Push(eb)
    }

    lb := dlg.Add("ListBox", "x10 y32 w480 h260", items)

    g_C["pick_lb"]       := lb
    g_C["pick_exeBases"] := exeBases
    g_C["pick_shared"]   := shared
    g_C["pick_dlg"]      := dlg

    lb.OnEvent("DoubleClick", PickSelectEvt)
    dlg.Add("Button", "x296 y302 w94 h28", "選択").OnEvent("Click",     PickSelectEvt)
    dlg.Add("Button", "x396 y302 w94 h28", "キャンセル").OnEvent("Click", PickCancelEvt)

    dlg.Show("w500 h340")
    WinWaitClose("ahk_id " dlg.Hwnd)
    return shared["result"]
}

PickSelectEvt(*) {
    global g_C
    lb       := g_C["pick_lb"]
    exeBases := g_C["pick_exeBases"]
    shared   := g_C["pick_shared"]
    dlg      := g_C["pick_dlg"]
    idx := lb.Value
    if idx > 0 && idx <= exeBases.Length {
        shared["result"] := exeBases[idx]
        dlg.Destroy()
    }
}

PickCancelEvt(*) {
    global g_C
    g_C["pick_dlg"].Destroy()
}
