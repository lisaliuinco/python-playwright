# python-playwright

Python + Playwright 自動化練習專案，包含網頁截圖、內容檢查與 GUI 健康檢查工具。

## 專案結構

```
python-playwright/
├── lesson10/
│   ├── practice5.py    # 核心檢查邏輯（CLI + 可 import）
│   ├── gui.py          # tkinter GUI 入口
│   ├── test_check.py   # 單元測試
│   └── output/         # 截圖輸出目錄
├── pyproject.toml
├── requirements.txt
└── README.md
```

## 安裝

使用 [uv](https://docs.astral.sh/uv/) 管理虛擬環境與依賴：

```bash
# 全域安裝 uv（若尚未安裝）
pip install uv

# 建立虛擬環境並安裝依賴
uv sync

# 安裝 Playwright 瀏覽器
uv run playwright install
```

若只需核心 GUI 功能（不含 Jupyter）：

```bash
uv sync --no-group dev
```

## 執行方式

### CLI 模式

```bash
# 預設使用 Chromium
uv run python lesson10/practice5.py

# 指定瀏覽器
uv run python lesson10/practice5.py --browser firefox
uv run python lesson10/practice5.py --browser webkit
```

### GUI 模式

```bash
uv run python lesson10/gui.py
```

### 測試

```bash
uv run pytest lesson10/test_check.py -v
```

## 功能說明

### 核心函式 `check_website_core()`

| 參數 | 型別 | 說明 |
|------|------|------|
| `url` | str | 目標網址 |
| `browser_name` | str | 瀏覽器引擎 (chromium/firefox/webkit) |
| `headless` | bool | 是否無頭模式 |
| `timeout_ms` | int | 載入逾時毫秒數 |
| `output_dir` | Path | 截圖儲存目錄 |
| `log_callback` | callable | 即時日誌回呼 |

回傳 `CheckResult` 資料物件，包含 HTTP 狀態、標題、截圖路徑等。

### GUI 應用程式

- 深藍 × 青綠現代化介面
- 左側：URL、瀏覽器選擇、Headless 開關、逾時設定
- 右側：HTTP 狀態、回應時間、頁面標題、截圖預覽
- 底部：可滾動執行日誌、開啟資料夾、清除結果
- Playwright 在背景執行緒執行，不阻塞 UI
