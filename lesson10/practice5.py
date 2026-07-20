"""專案 01：開啟真實網頁，檢查標題並留下截圖。

此腳本使用 Playwright 自動化瀏覽器，開啟指定網頁（預設為 example.com），
驗證頁面標題與主標題是否正確，並將整個頁面截圖存檔。
支援透過命令列參數選擇不同的瀏覽器引擎。
"""

import argparse  # 解析命令列參數
from pathlib import Path  # 處理跨平台的檔案路徑

from playwright.sync_api import sync_playwright  # Playwright 的同步 API


# 目標網站網址（使用 HTTPS 確保連線安全）
URL = "https://example.com/"

# 截圖輸出目錄，設為此腳本所在資料夾下的 "output" 子資料夾
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def check_website(browser_name: str = "chromium") -> None:
    """開啟目標網頁、驗證內容並將頁面截圖存檔。

    Args:
        browser_name: 瀏覽器引擎名稱，可選 "chromium"、"firefox" 或 "webkit"。
    """
    # 建立輸出目錄（若已存在則忽略，不會拋出錯誤）
    OUTPUT_DIR.mkdir(exist_ok=True)

    # 使用 with 語句啟動 Playwright，確保結束時自動釋放所有資源
    with sync_playwright() as playwright:
        # 根據傳入的瀏覽器名稱，動態取得對應的瀏覽器類型物件
        # 例如 "chromium" → playwright.chromium, "firefox" → playwright.firefox
        browser_type = getattr(playwright, browser_name)

        # 啟動瀏覽器實例，headless=True 表示在背景執行，不開啟可見的視窗
        # 適用於伺服器或 CI/CD 環境
        browser = browser_type.launch(headless=True)

        # 建立新的瀏覽器分頁，並設定視窗大小為 1280×720
        # 指定視窗大小可確保截圖尺寸一致，避免因不同螢幕解析度而有差異
        page = browser.new_page(viewport={"width": 1280, "height": 720})

        # 瀏覽器導航至目標網址
        # wait_until="domcontentloaded" 表示等到 HTML 文件解析完成即返回
        # （不必等待圖片、樣式表等外部資源載入完成，加快執行速度）
        response = page.goto(URL, wait_until="domcontentloaded")

        # 使用無障礙角色定位器（ARIA role）找到名為 "Example Domain" 的標題元素
        # inner_text() 取得該元素的純文字內容（不含 HTML 標籤）
        heading = page.get_by_role("heading", name="Example Domain").inner_text()

        # 組合截圖檔案的完整路徑，檔名包含瀏覽器名稱以便區分不同瀏覽器的截圖
        screenshot = OUTPUT_DIR / f"homepage_{browser_name}.png"

        # 將整個頁面（含可滾動區域）截圖並儲存為 PNG 檔案
        # full_page=True 會擷取完整頁面長度，而非僅可見區域
        page.screenshot(path=screenshot, full_page=True)

        # 印出診斷資訊供開發者確認結果
        print(f"瀏覽器: {browser_name}")
        # response.status 回傳 HTTP 狀態碼（200=成功），若無回應則顯示提示
        print(f"HTTP 狀態: {response.status if response else '無回應'}")
        # page.title() 取得 HTML 文件的 <title> 標籤內容
        print(f"頁面標題: {page.title()}")
        # 印出前面取得的主標題文字
        print(f"主標題: {heading}")
        # 印出截圖的儲存路徑，方便使用者快速找到檔案
        print(f"截圖: {screenshot}")
        # 關閉瀏覽器，釋放系統資源
        browser.close()


if __name__ == "__main__":
    # 使用 argparse 建立命令列介面，讓使用者可選擇瀏覽器
    parser = argparse.ArgumentParser(
        description="開啟 example.com 網頁並截圖存檔"
    )
    parser.add_argument(
        "--browser",  # 命令列參數名稱，例如 --browser firefox
        choices=["chromium", "firefox", "webkit"],  # 限定可選值
        default="chromium",  # 預設使用 Chromium 瀏覽器
        help="選擇瀏覽器引擎（預設: chromium）",
    )
    args = parser.parse_args()  # 解析使用者輸入的參數
    check_website(args.browser)  # 呼叫主函式並傳入瀏覽器名稱
