"""專案 01：開啟真實網頁，檢查標題並留下截圖。

此腳本使用 Playwright 自動化瀏覽器，開啟指定網頁（預設為 example.com），
驗證頁面標題與主標題是否正確，並將整個頁面截圖存檔。
支援透過命令列參數選擇不同的瀏覽器引擎。

可作為 CLI 腳本直接執行，也可被 GUI 模組 import 使用。
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

URL = "https://example.com/"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


@dataclass
class CheckResult:
    """儲存單次網站健康檢查結果的資料容器。"""

    url: str = ""
    final_url: str = ""
    browser: str = "chromium"
    http_status: int | None = None
    response_time_ms: float = 0.0
    page_title: str = ""
    heading: str = ""
    screenshot_path: str = ""
    success: bool = False
    message: str = ""
    error: str = ""

    @property
    def status_label(self) -> str:
        """根據 HTTP 狀態碼回傳人類可讀的狀態標籤。"""
        if self.error:
            return "失敗"
        if self.http_status is None:
            return "失敗"
        if 200 <= self.http_status < 300:
            return "成功"
        if 300 <= self.http_status < 400:
            return "警告"
        return "失敗"

    @property
    def status_color(self) -> str:
        """回傳對應狀態標籤的色碼（供 GUI 使用）。"""
        label = self.status_label
        if label == "成功":
            return "#2ecc71"
        if label == "警告":
            return "#f39c12"
        return "#e74c3c"


def check_website_core(
    url: str = URL,
    browser_name: str = "chromium",
    headless: bool = True,
    timeout_ms: int = 30_000,
    output_dir: Path | str = OUTPUT_DIR,
    log_callback: Any = None,
) -> CheckResult:
    """執行網站健康檢查的核心邏輯，回傳結構化結果。

    此函式可被 CLI 與 GUI 共用。GUI 可透過 log_callback 接收即時日誌。

    Args:
        url: 目標網站網址。
        browser_name: 瀏覽器引擎名稱（chromium / firefox / webkit）。
        headless: 是否以無頭模式啟動瀏覽器。
        timeout_ms: 頁面載入逾時毫秒數。
        output_dir: 截圖儲存目錄。
        log_callback: 可選的回呼函式，簽名為 fn(message: str)。

    Returns:
        CheckResult: 包含所有檢查結果的資料物件。
    """
    out = Path(output_dir)
    result = CheckResult(url=url, browser=browser_name)

    def log(msg: str) -> None:
        if log_callback:
            log_callback(msg)

    log(f"開始檢查 {url}（瀏覽器: {browser_name}）")

    try:
        out.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        result.error = f"無法建立輸出目錄: {exc}"
        log(result.error)
        return result

    start = time.perf_counter()

    try:
        with sync_playwright() as playwright:
            browser_type = getattr(playwright, browser_name)
            browser = browser_type.launch(headless=headless)
            page = browser.new_page(viewport={"width": 1280, "height": 720})

            response = page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            result.response_time_ms = round((time.perf_counter() - start) * 1000, 1)

            result.http_status = response.status if response else None
            result.final_url = page.url
            result.page_title = page.title()

            log(f"HTTP 狀態: {result.http_status}")
            log(f"頁面標題: {result.page_title}")

            try:
                heading_el = page.get_by_role("heading").first
                result.heading = heading_el.inner_text(timeout=5000)
                log(f"主標題: {result.heading}")
            except Exception:
                result.heading = "(無法取得)"
                log("主標題: (無法取得)")

            screenshot = out / f"homepage_{browser_name}.png"
            page.screenshot(path=screenshot, full_page=True)
            result.screenshot_path = str(screenshot)
            log(f"截圖已儲存: {screenshot}")

            browser.close()

        result.success = True
        result.message = "檢查完成"

    except Exception as exc:
        result.error = str(exc)
        result.success = False
        result.message = f"檢查失敗: {exc}"
        log(f"錯誤: {exc}")

    log(f"回應時間: {result.response_time_ms} ms")
    return result


def check_website(browser_name: str = "chromium") -> None:
    """CLI 用包裝函式：執行檢查並列印結果（保持原有行為）。"""
    result = check_website_core(browser_name=browser_name)
    print(f"瀏覽器: {result.browser}")
    print(f"HTTP 狀態: {result.http_status if result.http_status else '無回應'}")
    print(f"頁面標題: {result.page_title}")
    print(f"主標題: {result.heading}")
    print(f"截圖: {result.screenshot_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="開啟 example.com 網頁並截圖存檔")
    parser.add_argument(
        "--browser",
        choices=["chromium", "firefox", "webkit"],
        default="chromium",
        help="選擇瀏覽器引擎（預設: chromium）",
    )
    args = parser.parse_args()
    check_website(args.browser)
