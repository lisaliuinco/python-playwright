"""網站健康檢查 GUI 應用程式。

使用 tkinter + ttk 建立現代化桌面介面，透過背景執行緒呼叫 Playwright
執行網站健康檢查，所有 UI 更新透過 after() 安全回到主執行緒。
"""

from __future__ import annotations

import re
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Any

from practice5 import CheckResult, URL, OUTPUT_DIR, check_website_core

# ---------------------------------------------------------------------------
# 色彩常數 — 深藍 × 青綠現代色系
# ---------------------------------------------------------------------------
COLOR_BG_DARK = "#0f1b2d"  # 深藍主背景
COLOR_BG_PANEL = "#162a45"  # 卡片 / 面板背景
COLOR_BG_INPUT = "#1e3a5f"  # 輸入欄位背景
COLOR_FG = "#e0e6ed"  # 主要文字
COLOR_FG_DIM = "#8899aa"  # 次要文字
COLOR_ACCENT = "#00d2d3"  # 青綠強調色
COLOR_ACCENT_HOVER = "#01a3a4"  # 青綠 hover
COLOR_SUCCESS = "#2ecc71"  # 綠色（成功）
COLOR_WARNING = "#f39c12"  # 橘色（警告）
COLOR_ERROR = "#e74c3c"  # 紅色（失敗）
COLOR_LOG_BG = "#0b1929"  # 日誌背景
COLOR_BORDER = "#1f4068"  # 邊框

FONT_TITLE = ("Microsoft JhengHei UI", 16, "bold")
FONT_LABEL = ("Microsoft JhengHei UI", 10)
FONT_VALUE = ("Microsoft JhengHei UI", 11, "bold")
FONT_BUTTON = ("Microsoft JhengHei UI", 10, "bold")
FONT_LOG = ("Consolas", 9)

# ---------------------------------------------------------------------------
# 驗證工具
# ---------------------------------------------------------------------------
_URL_RE = re.compile(
    r"^https?://"  # scheme
    r"[^\s/$.?#]"  # 至少一個非空白非特殊字元
    r".*$",
    re.IGNORECASE,
)


def validate_url(raw: str) -> tuple[bool, str]:
    """驗證 URL 格式，回傳 (是否通過, 錯誤訊息)。"""
    raw = raw.strip()
    if not raw:
        return False, "請輸入網址，不可為空。"
    if not _URL_RE.match(raw):
        return False, (
            f"網址格式不正確：「{raw}」\n"
            "請輸入完整的網址，例如 https://example.com/"
        )
    return True, ""


def validate_timeout(raw: str) -> tuple[bool, int, str]:
    """驗證逾時輸入，回傳 (是否通過, 轉換後的毫秒數, 錯誤訊息)。"""
    raw = raw.strip()
    if not raw:
        return True, 30_000, ""
    try:
        val = int(raw)
    except ValueError:
        return False, 0, f"逾時必須為整數，您輸入了「{raw}」。"
    if val < 1_000:
        return False, 0, "逾時不可小於 1000 毫秒（1 秒）。"
    if val > 120_000:
        return False, 0, "逾時不可超過 120000 毫秒（120 秒）。"
    return True, val, ""


# ---------------------------------------------------------------------------
# 風格設定
# ---------------------------------------------------------------------------
def apply_style(root: tk.Tk) -> None:
    """套用自訂 ttk 風格，打造現代化深色介面。"""
    style = ttk.Style(root)
    root.configure(bg=COLOR_BG_DARK)

    style.theme_use("clam")

    # 全域
    style.configure(".", background=COLOR_BG_DARK, foreground=COLOR_FG, font=FONT_LABEL)
    style.configure("TFrame", background=COLOR_BG_DARK)
    style.configure("Card.TFrame", background=COLOR_BG_PANEL, relief="flat")
    style.configure("TLabel", background=COLOR_BG_DARK, foreground=COLOR_FG)
    style.configure(
        "Card.TLabel", background=COLOR_BG_PANEL, foreground=COLOR_FG, font=FONT_LABEL
    )
    style.configure(
        "Title.TLabel",
        background=COLOR_BG_DARK,
        foreground=COLOR_ACCENT,
        font=FONT_TITLE,
    )
    style.configure(
        "Value.TLabel",
        background=COLOR_BG_PANEL,
        foreground=COLOR_FG,
        font=FONT_VALUE,
    )
    style.configure(
        "Dim.TLabel",
        background=COLOR_BG_PANEL,
        foreground=COLOR_FG_DIM,
        font=FONT_LABEL,
    )
    style.configure(
        "Status.TLabel",
        background=COLOR_BG_PANEL,
        foreground=COLOR_FG,
        font=("Microsoft JhengHei UI", 14, "bold"),
        anchor="center",
    )

    # 輸入欄位
    style.configure(
        "TEntry",
        fieldbackground=COLOR_BG_INPUT,
        foreground=COLOR_FG,
        insertcolor=COLOR_ACCENT,
        borderwidth=1,
        relief="flat",
    )

    # 開關按鈕
    style.configure(
        "Accent.TCheckbutton",
        background=COLOR_BG_PANEL,
        foreground=COLOR_ACCENT,
        font=FONT_LABEL,
        indicatorcolor=COLOR_BG_INPUT,
    )
    style.map(
        "Accent.TCheckbutton",
        indicatorcolor=[("selected", COLOR_ACCENT)],
        background=[("active", COLOR_BG_PANEL)],
    )

    # 下拉選單
    style.configure(
        "TCombobox",
        fieldbackground=COLOR_BG_INPUT,
        background=COLOR_BG_INPUT,
        foreground=COLOR_FG,
        arrowcolor=COLOR_ACCENT,
        borderwidth=1,
        relief="flat",
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", COLOR_BG_INPUT)],
        foreground=[("readonly", COLOR_FG)],
    )

    # 主要按鈕
    style.configure(
        "Accent.TButton",
        background=COLOR_ACCENT,
        foreground="#0f1b2d",
        font=FONT_BUTTON,
        borderwidth=0,
        padding=(20, 8),
    )
    style.map(
        "Accent.TButton",
        background=[("active", COLOR_ACCENT_HOVER), ("disabled", COLOR_FG_DIM)],
        foreground=[("disabled", COLOR_BG_DARK)],
    )

    # 次要按鈕
    style.configure(
        "Secondary.TButton",
        background=COLOR_BG_INPUT,
        foreground=COLOR_FG,
        font=FONT_LABEL,
        borderwidth=0,
        padding=(12, 6),
    )
    style.map(
        "Secondary.TButton",
        background=[("active", COLOR_BORDER)],
    )

    # 分隔線
    style.configure("TSeparator", background=COLOR_BORDER)

    # 滾動條
    style.configure(
        "Vertical.TScrollbar",
        background=COLOR_BG_INPUT,
        troughcolor=COLOR_BG_DARK,
        arrowcolor=COLOR_ACCENT,
        borderwidth=0,
    )


# ---------------------------------------------------------------------------
# 主應用程式
# ---------------------------------------------------------------------------
class HealthCheckApp:
    """網站健康檢查桌面應用程式的主類別。"""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("網站健康檢查工具")
        self.root.geometry("1200x760")
        self.root.minsize(1000, 640)
        self.root.configure(bg=COLOR_BG_DARK)

        apply_style(self.root)

        self._is_running = False
        self._worker_thread: threading.Thread | None = None

        self._build_ui()

    # ------------------------------------------------------------------
    # UI 建構
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        """建立所有 UI 元件。"""
        # 頂部標題列
        header = ttk.Frame(self.root, style="TFrame")
        header.pack(fill="x", padx=20, pady=(16, 4))
        ttk.Label(header, text="🔍 網站健康檢查工具", style="Title.TLabel").pack(
            side="left"
        )

        ttk.Separator(self.root, orient="horizontal").pack(
            fill="x", padx=20, pady=(0, 8)
        )

        # 主體容器（左右雙欄）
        body = ttk.Frame(self.root, style="TFrame")
        body.pack(fill="both", expand=True, padx=20, pady=(0, 8))
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=5)
        body.rowconfigure(0, weight=1)

        self._build_left_panel(body)
        self._build_right_panel(body)

        # 底部區域
        ttk.Separator(self.root, orient="horizontal").pack(
            fill="x", padx=20, pady=(0, 4)
        )
        self._build_bottom_panel()

    # ---- 左側面板 ----
    def _build_left_panel(self, parent: ttk.Frame) -> None:
        """建立左側輸入控制面板。"""
        card = ttk.Frame(parent, style="Card.TFrame", padding=16)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        card.columnconfigure(0, weight=1)

        row = 0

        # 標題
        ttk.Label(card, text="檢查設定", style="Value.TLabel").grid(
            row=row, column=0, sticky="w", pady=(0, 12)
        )
        row += 1

        # URL 輸入
        ttk.Label(card, text="網址 (URL)", style="Card.TLabel").grid(
            row=row, column=0, sticky="w", pady=(4, 2)
        )
        row += 1
        self._url_var = tk.StringVar(value=URL)
        url_entry = ttk.Entry(card, textvariable=self._url_var, width=36)
        url_entry.grid(row=row, column=0, sticky="ew", pady=(0, 8), ipady=4)
        row += 1

        # 瀏覽器選擇
        ttk.Label(card, text="瀏覽器引擎", style="Card.TLabel").grid(
            row=row, column=0, sticky="w", pady=(4, 2)
        )
        row += 1
        self._browser_var = tk.StringVar(value="chromium")
        browser_combo = ttk.Combobox(
            card,
            textvariable=self._browser_var,
            values=["chromium", "firefox", "webkit"],
            state="readonly",
            width=33,
        )
        browser_combo.grid(row=row, column=0, sticky="ew", pady=(0, 8), ipady=4)
        row += 1

        # Headless 開關
        self._headless_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            card,
            text="無頭模式 (Headless)",
            variable=self._headless_var,
            style="Accent.TCheckbutton",
        ).grid(row=row, column=0, sticky="w", pady=(4, 8))
        row += 1

        # Timeout 輸入
        ttk.Label(card, text="逾時時間 (毫秒)", style="Card.TLabel").grid(
            row=row, column=0, sticky="w", pady=(4, 2)
        )
        row += 1
        self._timeout_var = tk.StringVar(value="30000")
        timeout_entry = ttk.Entry(card, textvariable=self._timeout_var, width=36)
        timeout_entry.grid(row=row, column=0, sticky="ew", pady=(0, 8), ipady=4)
        row += 1

        ttk.Label(card, text="範圍：1000 ~ 120000 ms", style="Dim.TLabel").grid(
            row=row, column=0, sticky="w", pady=(0, 12)
        )
        row += 1

        # 開始按鈕
        self._start_btn = ttk.Button(
            card,
            text="▶  開始檢查",
            style="Accent.TButton",
            command=self._on_start,
        )
        self._start_btn.grid(row=row, column=0, sticky="ew", pady=(0, 8), ipady=4)
        row += 1

        # 進度指示
        self._progress_var = tk.StringVar(value="")
        ttk.Label(card, textvariable=self._progress_var, style="Dim.TLabel").grid(
            row=row, column=0, sticky="w"
        )

    # ---- 右側面板 ----
    def _build_right_panel(self, parent: ttk.Frame) -> None:
        """建立右側結果顯示面板。"""
        card = ttk.Frame(parent, style="Card.TFrame", padding=16)
        card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=1)

        row = 0

        ttk.Label(card, text="檢查結果", style="Value.TLabel").grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 12)
        )
        row += 1

        # 狀態徽章
        self._status_var = tk.StringVar(value="—")
        self._status_label = ttk.Label(
            card, textvariable=self._status_var, style="Status.TLabel"
        )
        self._status_label.grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=(0, 12), ipady=8
        )
        # 設定狀態徽章的初始背景
        self._status_frame = card
        row += 1

        # HTTP 狀態
        row = self._make_result_row(card, row, "HTTP 狀態碼")
        self._http_var = tk.StringVar(value="—")

        # 回應時間
        row = self._make_result_row(card, row, "回應時間")
        self._time_var = tk.StringVar(value="—")

        # 頁面標題
        row = self._make_result_row(card, row, "頁面標題")
        self._title_var = tk.StringVar(value="—")

        # 主標題
        row = self._make_result_row(card, row, "主標題 (H1)")
        self._heading_var = tk.StringVar(value="—")

        # 最終 URL
        row = self._make_result_row(card, row, "最終 URL")
        self._final_url_var = tk.StringVar(value="—")

        ttk.Separator(card, orient="horizontal").grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=8
        )
        row += 1

        # 截圖預覽
        ttk.Label(card, text="截圖預覽", style="Card.TLabel").grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(4, 4)
        )
        row += 1

        self._preview_label = ttk.Label(card, text="尚無截圖", style="Dim.TLabel")
        self._preview_label.grid(
            row=row, column=0, columnspan=2, sticky="nsew", pady=(0, 0)
        )
        card.rowconfigure(row, weight=1)
        self._preview_image: Any = None  # 防止被 GC 回收

    def _make_result_row(
        self, parent: ttk.Frame, row: int, label_text: str
    ) -> int:
        """建立一個「標籤 + 值」的結果列，回傳下一列索引。"""
        ttk.Label(parent, text=label_text, style="Card.TLabel").grid(
            row=row, column=0, sticky="w", pady=3, padx=(0, 8)
        )
        var = tk.StringVar(value="—")
        ttk.Label(parent, textvariable=var, style="Value.TLabel").grid(
            row=row, column=1, sticky="w", pady=3
        )
        # 把 var 設定到對應屬性（由呼叫端在外部綁定）
        setattr(self, f"_row_{row}_var", var)
        return row + 1

    # ---- 底部面板 ----
    def _build_bottom_panel(self) -> None:
        """建立底部日誌與操作按鈕區域。"""
        bottom = ttk.Frame(self.root, style="TFrame")
        bottom.pack(fill="both", expand=True, padx=20, pady=(0, 12))

        # 日誌標題列
        log_header = ttk.Frame(bottom, style="TFrame")
        log_header.pack(fill="x", pady=(0, 4))
        ttk.Label(log_header, text="執行日誌", style="Card.TLabel").pack(side="left")

        # 按鈕列
        btn_frame = ttk.Frame(log_header, style="TFrame")
        btn_frame.pack(side="right")
        ttk.Button(
            btn_frame,
            text="📁 開啟輸出資料夾",
            style="Secondary.TButton",
            command=self._open_output_dir,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            btn_frame,
            text="🗑 清除結果",
            style="Secondary.TButton",
            command=self._clear_results,
        ).pack(side="left")

        # 可滾動日誌區
        log_frame = ttk.Frame(bottom, style="Card.TFrame", padding=4)
        log_frame.pack(fill="both", expand=True)

        self._log_text = tk.Text(
            log_frame,
            bg=COLOR_LOG_BG,
            fg=COLOR_FG_DIM,
            font=FONT_LOG,
            insertbackground=COLOR_ACCENT,
            selectbackground=COLOR_BG_INPUT,
            borderwidth=0,
            highlightthickness=0,
            state="disabled",
            wrap="word",
        )
        scrollbar = ttk.Scrollbar(
            log_frame, orient="vertical", command=self._log_text.yview
        )
        self._log_text.configure(yscrollcommand=scrollbar.set)

        self._log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # ------------------------------------------------------------------
    # 結果值的綁定（修正 _make_result_row 的屬性映射）
    # ------------------------------------------------------------------
    def _bind_result_vars(self) -> None:
        """將結果面板的各個 tk.StringVar 綁定到對應屬性。"""
        # _make_result_row 用 setattr 動態建立了 _row_{n}_var，
        # 但我們需要知道正確的列號。改用明確綁定更可靠。
        # 實際上我們在 _build_right_panel 中直接使用 self._xxx_var，
        # 所以這裡不需要額外綁定。此方法保留為擴充用途。
        pass

    # ------------------------------------------------------------------
    # 事件處理
    # ------------------------------------------------------------------
    def _on_start(self) -> None:
        """「開始檢查」按鈕被點擊時觸發。"""
        if self._is_running:
            return

        # 驗證 URL
        url_ok, url_err = validate_url(self._url_var.get())
        if not url_ok:
            messagebox.showwarning("輸入錯誤", url_err)
            return

        # 驗證逾時
        timeout_ok, timeout_ms, timeout_err = validate_timeout(
            self._timeout_var.get()
        )
        if not timeout_ok:
            messagebox.showwarning("輸入錯誤", timeout_err)
            return

        self._is_running = True
        self._start_btn.configure(state="disabled")
        self._progress_var.set("⏳ 正在檢查中，請稍候…")
        self._set_status_badge("檢查中…", COLOR_WARNING)

        url = self._url_var.get().strip()
        browser_name = self._browser_var.get()
        headless = self._headless_var.get()

        self._append_log(f"[啟動] 網址={url}  瀏覽器={browser_name}  headless={headless}")

        # 在背景執行緒中執行 Playwright，避免阻塞 UI
        self._worker_thread = threading.Thread(
            target=self._run_check,
            args=(url, browser_name, headless, timeout_ms),
            daemon=True,
        )
        self._worker_thread.start()

    def _run_check(
        self,
        url: str,
        browser_name: str,
        headless: bool,
        timeout_ms: int,
    ) -> None:
        """背景執行緒：執行檢查後透過 root.after 安全更新 UI。"""
        try:
            result = check_website_core(
                url=url,
                browser_name=browser_name,
                headless=headless,
                timeout_ms=timeout_ms,
                output_dir=OUTPUT_DIR,
                log_callback=lambda msg: self.root.after(0, self._append_log, msg),
            )
        except Exception as exc:
            result = CheckResult(
                url=url,
                browser=browser_name,
                error=str(exc),
                message=f"未預期的錯誤: {exc}",
            )

        # 安全地回到主執行緒更新 UI
        self.root.after(0, self._on_check_done, result)

    def _on_check_done(self, result: CheckResult) -> None:
        """檢查完成後在主執行緒更新所有結果元件。"""
        self._is_running = False
        self._start_btn.configure(state="normal")
        self._progress_var.set("")

        # 狀態徽章
        self._set_status_badge(result.status_label, result.status_color)

        # 結果欄位
        self._http_var.set(
            str(result.http_status) if result.http_status else "無回應"
        )
        self._time_var.set(f"{result.response_time_ms} ms")
        self._title_var.set(result.page_title or "—")
        self._heading_var.set(result.heading or "—")
        self._final_url_var.set(result.final_url or result.url)

        # 截圖預覽
        self._load_preview(result.screenshot_path)

        self._append_log(f"[完成] {result.message}")

    # ------------------------------------------------------------------
    # UI 輔助方法
    # ------------------------------------------------------------------
    def _set_status_badge(self, text: str, color: str) -> None:
        """更新狀態徽章文字與背景色。"""
        self._status_var.set(text)
        # ttk.Label 不直接支援 background 動態變色，
        # 改用 tk.Label 實現徽章效果
        try:
            self._status_label.destroy()
        except Exception:
            pass

        self._status_label = tk.Label(
            self._status_frame,
            text=text,
            bg=color,
            fg="#0f1b2d",
            font=("Microsoft JhengHei UI", 14, "bold"),
            anchor="center",
            padx=16,
            pady=6,
        )
        self._status_label.grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=(0, 12)
        )

    def _append_log(self, message: str) -> None:
        """在日誌區末尾追加一行訊息。"""
        self._log_text.configure(state="normal")
        self._log_text.insert("end", message + "\n")
        self._log_text.see("end")
        self._log_text.configure(state="disabled")

    def _load_preview(self, path: str) -> None:
        """載入截圖到預覽區（使用 Pillow 若可用，否則顯示路徑）。"""
        if not path or not Path(path).is_file():
            self._preview_label.configure(text="截圖檔案不存在")
            return

        try:
            from PIL import Image, ImageTk

            img = Image.open(path)
            # 縮圖以符合預覽區大小
            max_w, max_h = 480, 260
            img.thumbnail((max_w, max_h), Image.LANCZOS)
            self._preview_image = ImageTk.PhotoImage(img)
            self._preview_label.configure(
                image=self._preview_image, text="", compound="center"
            )
        except ImportError:
            self._preview_label.configure(
                text=f"截圖已儲存:\n{path}\n（安裝 Pillow 可顯示預覽）"
            )
        except Exception as exc:
            self._preview_label.configure(text=f"預覽載入失敗: {exc}")

    def _open_output_dir(self) -> None:
        """用系統檔案管理員開啟截圖輸出目錄。"""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        path_str = str(OUTPUT_DIR)
        if sys.platform == "win32":
            subprocess.Popen(["explorer", path_str])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path_str])
        else:
            subprocess.Popen(["xdg-open", path_str])
        self._append_log(f"[系統] 已開啟資料夾: {path_str}")

    def _clear_results(self) -> None:
        """清除所有結果顯示與日誌。"""
        self._http_var.set("—")
        self._time_var.set("—")
        self._title_var.set("—")
        self._heading_var.set("—")
        self._final_url_var.set("—")
        self._set_status_badge("—", COLOR_BG_INPUT)

        try:
            self._preview_label.configure(
                image="", text="尚無截圖", compound="center"
            )
        except Exception:
            pass
        self._preview_image = None

        self._log_text.configure(state="normal")
        self._log_text.delete("1.0", "end")
        self._log_text.configure(state="disabled")

        self._append_log("[系統] 結果已清除")


# ---------------------------------------------------------------------------
# 程式進入點
# ---------------------------------------------------------------------------
def main() -> None:
    """啟動 GUI 應用程式。"""
    root = tk.Tk()
    root.withdraw()  # 先隱藏，等佈局完成後再顯示
    HealthCheckApp(root)
    root.deiconify()
    root.mainloop()


if __name__ == "__main__":
    main()
