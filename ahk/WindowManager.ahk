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

global ConfigFile  := A_ScriptDir "\wm_config.ini"
global Presets     := []
global PopupHotkey := "^!w"
global mgmtGui     := ""
global selIdx      := 0

; ─── 起動 ───────────────────────────────────────────────────
LoadConfig()
RegisterHotkeys()
SetupTray()
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
    IniWrite("^!w", ConfigFile, "General", "PopupHotkey")
    IniWrite(2,     ConfigFile, "General", "PresetCount")

    IniWrite("WSL 横並び",      ConfigFile, "Preset_1", "Name")
    IniWrite("^!1",             ConfigFile, "Preset_1", "Hotkey")
    IniWrite("arrange",         ConfigFile, "Preset_1", "Mode")
    IniWrite("WindowsTerminal", ConfigFile, "Preset_1", "App")
    IniWrite("wsl",             ConfigFile, "Preset_1", "Title")
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
    for p in Presets {
        if p.Hotkey != "" {
            pRef := p
            try Hotkey(p.Hotkey, ((*) => ApplyPreset(pRef)))
        }
    }
}

UnregisterHotkeys() {
    global Presets, PopupHotkey
    try Hotkey(PopupHotkey, "Off")
    for p in Presets {
        if p.Hotkey != ""
            try Hotkey(p.Hotkey, "Off")
    }
}

ReloadHotkeys() {
    UnregisterHotkeys()
    LoadConfig()
    RegisterHotkeys()
}

; ═══════════════════════════════════════════════════════════════
;  TRAY
; ═══════════════════════════════════════════════════════════════

SetupTray() {
    A_TrayMenu.Delete()
    A_TrayMenu.Add("管理メニュー", (*) => ShowManagement())
    A_TrayMenu.Add()
    A_TrayMenu.Add("再起動",       (*) => Reload())
    A_TrayMenu.Add("終了",         (*) => ExitApp())
    A_TrayMenu.Default := "管理メニュー"
    TraySetIcon("shell32.dll", 238)
    A_IconTip := "Window Manager"
}

; ═══════════════════════════════════════════════════════════════
;  WINDOW OPERATIONS
; ═══════════════════════════════════════════════════════════════

GetWorkArea() {
    MonitorGetWorkArea(, &wx, &wy, &wr, &wb)
    return {x: wx, y: wy, w: wr - wx, h: wb - wy}
}

; 可視ウィンドウ全一覧を返す [{hwnd, title, exe}]
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

; app名・titleフィルタで一致するウィンドウHWND配列を返す
FindWindows(app, titleFilter := "") {
    appL   := StrLower(StrReplace(app, ".exe", ""))
    titleL := StrLower(titleFilter)
    result := []

    for w in GetAllWindows() {
        exeL   := StrLower(StrReplace(w.exe, ".exe", ""))
        tL     := StrLower(w.title)

        ; アプリ一致: exe名 または タイトル部分一致
        appMatch := InStr(exeL, appL) || InStr(tL, appL)
        if !appMatch
            continue

        ; タイトルフィルタ（空なら無条件通過）
        if titleL != "" && !InStr(tL, titleL)
            continue

        result.Push(w.hwnd)
    }
    return result
}

; HWNDリストを指定方向に等分割配置
ArrangeWindows(hwnds, direction) {
    n := hwnds.Length
    if n = 0
        return
    wa := GetWorkArea()

    if direction = "horizontal" {
        w := wa.w // n
        i := 0
        for hwnd in hwnds {
            WinRestore("ahk_id " hwnd)
            WinMove(wa.x + i*w, wa.y, w, wa.h, "ahk_id " hwnd)
            i++
        }
    } else if direction = "vertical" {
        h := wa.h // n
        i := 0
        for hwnd in hwnds {
            WinRestore("ahk_id " hwnd)
            WinMove(wa.x, wa.y + i*h, wa.w, h, "ahk_id " hwnd)
            i++
        }
    } else if direction = "tile" {
        cols := Ceil(Sqrt(n))
        rows := Ceil(n / cols)
        tw   := wa.w // cols
        th   := wa.h // rows
        i    := 0
        for hwnd in hwnds {
            WinRestore("ahk_id " hwnd)
            WinMove(wa.x + Mod(i, cols)*tw, wa.y + (i // cols)*th, tw, th, "ahk_id " hwnd)
            i++
        }
    }
}

; プリセット適用
ApplyPreset(preset) {
    if preset.Mode = "arrange" {
        hwnds := FindWindows(preset.App, preset.Title)
        ArrangeWindows(hwnds, preset.Arrange)
        return
    }

    ; カスタムモード: "app,title,x,y,w,h;..." 形式
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

; ═══════════════════════════════════════════════════════════════
;  POPUP MENU（画面上部中央）
; ═══════════════════════════════════════════════════════════════

ShowPopup(*) {
    global Presets
    if Presets.Length = 0 {
        MsgBox("プリセットがありません。`nトレイアイコン右クリック → 管理メニューから追加してください。",
               "Window Manager", "0x40")
        return
    }

    m := Menu()
    for p in Presets {
        label := p.Name
        if p.Hotkey != ""
            label .= "`t" p.Hotkey
        pRef := p
        m.Add(label, ((*) => ApplyPreset(pRef)))
    }
    m.Add()
    m.Add("管理メニュー", (*) => ShowManagement())

    ; 画面上部中央に表示（Windowsのメニューはカーソル位置を基準にするので調整）
    x := A_ScreenWidth  // 2 - 120
    y := Integer(A_ScreenHeight * 0.12)
    m.Show(x, y)
}

; ═══════════════════════════════════════════════════════════════
;  MANAGEMENT GUI
; ═══════════════════════════════════════════════════════════════

ShowManagement(*) {
    global mgmtGui, Presets, PopupHotkey, selIdx

    if IsObject(mgmtGui) {
        try { mgmtGui.Show() ; return }
    }

    selIdx := 0
    mgmtGui := Gui("+Resize +MinSize680x460", "ウィンドウ配置プリセット管理")
    mgmtGui.BackColor := "FFFFFF"
    mgmtGui.SetFont("s10", "Meiryo")
    mgmtGui.OnEvent("Close", (*) => (mgmtGui := ""))

    ; ── ヘッダー ────────────────────────────
    mgmtGui.Add("Text", "x0 y0 w800 h44 0x0E BackgroundColor003366", "")  ; 塗り背景
    mgmtGui.Add("Text", "x12 y12 cWhite BackgroundColor003366",
                "ウィンドウ配置プリセット管理")
    mgmtGui.Add("Text", "x350 y14 cWhite BackgroundColor003366", "ポップアップキー：")
    edtPopupHk := mgmtGui.Add("Edit", "x488 y11 w130 BackgroundColor003366 cWhite",
                               PopupHotkey)
    mgmtGui.Add("Button", "x624 y9 w58 h26", "適用").OnEvent("Click", (*) {
        global PopupHotkey
        PopupHotkey := edtPopupHk.Value
        SaveConfig()
        ReloadHotkeys()
        ToolTip("ポップアップキー: " PopupHotkey)
        SetTimer(() => ToolTip(), -2000)
    })

    ; ── 左：プリセット一覧 ──────────────────
    mgmtGui.Add("Text", "x10 y54 w170", "プリセット一覧")
    lbPresets := mgmtGui.Add("ListBox", "x10 y72 w170 h280 vPresetLB", [])
    RefreshPresetList(lbPresets)

    mgmtGui.Add("Button", "x10 y360 w80 h26",  "＋ 新規").OnEvent("Click",
        (*) => OnNew(lbPresets, edtName, edtHk, edtApp, edtTitle, rdoH, rdoV, rdoT))
    mgmtGui.Add("Button", "x96 y360 w84 h26",  "削除").OnEvent("Click",
        (*) => OnDelete(lbPresets, edtName))

    ; ── 右：詳細 ────────────────────────────
    mgmtGui.Add("Text", "x196 y54", "プリセット詳細")

    mgmtGui.Add("Text",  "x196 y74 w90",  "名前：")
    edtName := mgmtGui.Add("Edit", "x290 y72 w390 vPresetName")

    mgmtGui.Add("Text",  "x196 y106 w90", "ホットキー：")
    edtHk := mgmtGui.Add("Edit", "x290 y104 w160 vPresetHk")
    mgmtGui.Add("Text",  "x456 y107 w220 cGray", "例: ^!1 = Ctrl+Alt+1  ^+F1 = Ctrl+Shift+F1")

    ; モード選択
    rdoArr := mgmtGui.Add("Radio", "x196 y138 vModeArr Checked", "アレンジ（自動タイル）")
    mgmtGui.Add("Radio",  "x390 y138 vModeCus",  "カスタム（位置指定）")

    ; ── アレンジパネル ───────────────────────
    mgmtGui.Add("GroupBox", "x196 y160 w490 h148", "アレンジ設定")

    mgmtGui.Add("Text", "x210 y182 w116", "アプリ名：")
    edtApp   := mgmtGui.Add("Edit",   "x330 y180 w200 vArrApp")
    mgmtGui.Add("Button", "x536 y178 w60 h24", "選択...").OnEvent("Click",
        (*) => OnPickApp(edtApp))

    mgmtGui.Add("Text", "x210 y214 w116", "タイトル絞り込み：")
    edtTitle := mgmtGui.Add("Edit",   "x330 y212 w200 vArrTitle")
    mgmtGui.Add("Text", "x536 y215 w150 cGray", "例: wsl （空欄=全て）")

    mgmtGui.Add("Text", "x210 y248 w116", "並べ方：")
    rdoH := mgmtGui.Add("Radio", "x330 y248 vDirH Checked", "横並び")
    rdoV := mgmtGui.Add("Radio", "x412 y248 vDirV",         "縦並び")
    rdoT := mgmtGui.Add("Radio", "x494 y248 vDirT",         "タイル(格子)")

    mgmtGui.Add("Text", "x210 y280 w470 cGray",
                "実行時に一致する全ウィンドウを自動で等分割配置します。")

    ; 保存ボタン
    mgmtGui.Add("Button", "x560 y420 w118 h32", "保存").OnEvent("Click",
        (*) => OnSave(lbPresets, edtName, edtHk, edtApp, edtTitle, rdoV, rdoT))

    ; 一覧選択イベント
    lbPresets.OnEvent("Change", (*) {
        global selIdx, Presets
        idx := lbPresets.Value
        if idx = 0 || idx > Presets.Length
            return
        selIdx := idx
        p := Presets[idx]
        edtName.Value  := p.Name
        edtHk.Value    := p.Hotkey
        edtApp.Value   := p.App
        edtTitle.Value := p.Title
        rdoH.Value := 1
        if p.Arrange = "vertical"
            rdoV.Value := 1
        else if p.Arrange = "tile"
            rdoT.Value := 1
    })

    mgmtGui.Show("w700 h460")
}

; ── 管理GUI イベントハンドラ ─────────────────────────────────

OnNew(lb, edtName, edtHk, edtApp, edtTitle, rdoH, rdoV, rdoT) {
    global selIdx
    selIdx := 0
    lb.Value := 0
    edtName.Value  := ""
    edtHk.Value    := ""
    edtApp.Value   := ""
    edtTitle.Value := ""
    rdoH.Value := 1
}

OnDelete(lb, edtName) {
    global selIdx, Presets
    if selIdx = 0
        return
    p := Presets[selIdx]
    if MsgBox("「" p.Name "」を削除しますか？", "削除確認", "0x24") != "Yes"
        return
    Presets.RemoveAt(selIdx)
    selIdx := 0
    SaveConfig()
    ReloadHotkeys()
    RefreshPresetList(lb)
    edtName.Value := ""
}

OnSave(lb, edtName, edtHk, edtApp, edtTitle, rdoV, rdoT) {
    global selIdx, Presets
    name := Trim(edtName.Value)
    if name = "" {
        MsgBox("名前を入力してください", "エラー", "0x10")
        return
    }
    dir := "horizontal"
    if rdoV.Value
        dir := "vertical"
    else if rdoT.Value
        dir := "tile"

    p := {
        Name:    name,
        Hotkey:  Trim(edtHk.Value),
        Mode:    "arrange",
        App:     Trim(edtApp.Value),
        Title:   Trim(edtTitle.Value),
        Arrange: dir,
        Windows: "",
    }

    if selIdx > 0
        Presets[selIdx] := p
    else
        Presets.Push(p)

    SaveConfig()
    ReloadHotkeys()
    RefreshPresetList(lb)
    ToolTip("「" name "」を保存しました")
    SetTimer(() => ToolTip(), -2000)
}

OnPickApp(edtApp) {
    global mgmtGui
    result := PickWindow(mgmtGui)
    if result != ""
        edtApp.Value := result
}

RefreshPresetList(lb) {
    global Presets
    lb.Delete()
    for p in Presets
        lb.Add([p.Name])
}

; ── ウィンドウ選択ダイアログ（モーダル）────────────────────
PickWindow(ownerGui) {
    ; クロージャ間でリザルトを共有するために Map を使用
    shared := Map("result", "")

    dlg := Gui("+Owner" ownerGui.Hwnd " +Modal", "ウィンドウを選択")
    dlg.BackColor := "FFFFFF"
    dlg.SetFont("s10", "Meiryo")
    dlg.OnEvent("Close", (*) => 0)

    dlg.Add("Text", "x10 y10", "実行中ウィンドウ（ダブルクリックで選択）")

    wins    := GetAllWindows()
    items   := []
    exeBases := []
    for w in wins {
        exeBase := StrReplace(w.exe, ".exe", "")
        items.Push(exeBase "  —  " SubStr(w.title, 1, 52))
        exeBases.Push(exeBase)
    }

    lb := dlg.Add("ListBox", "x10 y32 w480 h260", items)

    DoSelect := (*) {
        idx := lb.Value
        if idx > 0 && idx <= exeBases.Length {
            shared["result"] := exeBases[idx]
            dlg.Destroy()
        }
    }

    lb.OnEvent("DoubleClick", DoSelect)
    dlg.Add("Button", "x296 y302 w94 h28", "選択").OnEvent("Click", DoSelect)
    dlg.Add("Button", "x396 y302 w94 h28", "キャンセル").OnEvent("Click",
            (*) => dlg.Destroy())

    dlg.Show("w500 h340")

    ; ダイアログが閉じるまで待機
    WinWaitClose("ahk_id " dlg.Hwnd)
    return shared["result"]
}
