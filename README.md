# ScriptSausage

ScriptSausage 是一個基於 Python 與 Tkinter 打造的跨平台腳本管理與執行工具。它可以幫助你將各式各樣的 `.py`, `.bat`, `.cmd`, `.ps1`, `.exe` 集中管理在同一個介面中，並支援動態參數設定。

## Example use cases
- Running repetitive local scripts without remembering commands
- Managing small personal utilities in one place
- Quickly testing scripts with different parameters

## 專案結構

```
ScriptSausage/
├── scriptsausage/           # 主程式套件
│   ├── main.py          # 核心 UI 與執行邏輯
│   └── ScriptSausage.json      # 自動儲存的設定檔 (執行後產生)
├── tests/               # 測試用程式與實驗腳本
│   ├── fixtures/        # 給主程式測試用的假腳本 (.bat, .py)
│   └── test_*.py        # 包含 POSIX 參數解析、Undo/Redo 等底層實驗腳本
├── docs/                # 專案文件
│   └── spec.md          # 需求與架構規格書
├── run.py               # 程式進入點
├── .gitignore           # 忽略暫存檔與編譯檔
└── README.md            # 專案說明
```

## 功能特色
- **集中管理**：透過 Notebook 頁籤管理大量腳本，支援滑鼠滾輪快速切換頁籤。
- **支援多種執行環境**：自動辨識 `.py`, `.bat`, `.ps1`、`.exe` 並以獨立終端機視窗執行。
- **視覺化與防呆**：
  - 根據副檔名動態改變「執行」按鈕顏色的科技感 UI。
  - 路徑若不存在會自動標紅並鎖死執行按鈕。
- **強健的快捷鍵支援**：為所有輸入框加入全域的 `Ctrl+C/V/X` 以及 50 步防呆歷史紀錄的 `Ctrl+Z` (復原) 與 `Ctrl+Y` (重做)。
- **進階參數高亮**：進階編輯視窗內建 Regex 語法高亮 (Syntax Highlighting)，自動標色 `--flag` 與 `"字串"`。
- **全自動即時儲存**：無需手動點擊，任何打字與設定變更皆會在背景「零干擾」自動存入 `ScriptSausage.json` (綠色版設計)。

## 如何執行
請確保已安裝 Python 3.11 或以上版本，在專案根目錄下執行：
```bash
python run.py
```
