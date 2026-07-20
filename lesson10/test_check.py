"""practice5 核心函式的單元測試。"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# 確保 lesson10 目錄在 sys.path 中，以便 import 模組
sys.path.insert(0, str(Path(__file__).resolve().parent))

from practice5 import CheckResult, check_website_core, URL


# ---------------------------------------------------------------------------
# CheckResult 資料類別測試
# ---------------------------------------------------------------------------
class TestCheckResult:
    """測試 CheckResult 的屬性與計算邏輯。"""

    def test_success_status(self) -> None:
        r = CheckResult(http_status=200)
        assert r.status_label == "成功"
        assert r.status_color == "#2ecc71"

    def test_redirect_warning(self) -> None:
        r = CheckResult(http_status=301)
        assert r.status_label == "警告"
        assert r.status_color == "#f39c12"

    def test_client_error(self) -> None:
        r = CheckResult(http_status=404)
        assert r.status_label == "失敗"
        assert r.status_color == "#e74c3c"

    def test_server_error(self) -> None:
        r = CheckResult(http_status=500)
        assert r.status_label == "失敗"

    def test_no_response(self) -> None:
        r = CheckResult(http_status=None)
        assert r.status_label == "失敗"

    def test_error_overrides(self) -> None:
        r = CheckResult(http_status=200, error="timeout")
        assert r.status_label == "失敗"


# ---------------------------------------------------------------------------
# validate_url / validate_timeout 測試
# ---------------------------------------------------------------------------
class TestValidation:
    """測試輸入驗證函式。"""

    def test_valid_url(self) -> None:
        from gui import validate_url

        ok, msg = validate_url("https://example.com/")
        assert ok is True
        assert msg == ""

    def test_empty_url(self) -> None:
        from gui import validate_url

        ok, msg = validate_url("")
        assert ok is False
        assert "空" in msg

    def test_invalid_url(self) -> None:
        from gui import validate_url

        ok, msg = validate_url("not-a-url")
        assert ok is False

    def test_valid_timeout(self) -> None:
        from gui import validate_timeout

        ok, ms, msg = validate_timeout("5000")
        assert ok is True
        assert ms == 5000

    def test_empty_timeout_uses_default(self) -> None:
        from gui import validate_timeout

        ok, ms, msg = validate_timeout("")
        assert ok is True
        assert ms == 30_000

    def test_timeout_too_small(self) -> None:
        from gui import validate_timeout

        ok, ms, msg = validate_timeout("100")
        assert ok is False

    def test_timeout_not_number(self) -> None:
        from gui import validate_timeout

        ok, ms, msg = validate_timeout("abc")
        assert ok is False


# ---------------------------------------------------------------------------
# check_website_core 基本測試（使用 mock 避免真實網路請求）
# ---------------------------------------------------------------------------
class TestCheckWebsiteCore:
    """測試核心函式的基本流程（mock Playwright）。"""

    def test_returns_check_result(self) -> None:
        """確認回傳值為 CheckResult 型別。"""
        # 因為 check_website_core 會真實啟動 Playwright，
        # 在沒有瀏覽器的 CI 環境中可能失敗，
        # 所以用 mock 擋住 sync_playwright
        mock_response = MagicMock()
        mock_response.status = 200

        mock_page = MagicMock()
        mock_page.goto.return_value = mock_response
        mock_page.url = "https://example.com/"
        mock_page.title.return_value = "Example Domain"
        heading_el = MagicMock()
        heading_el.inner_text.return_value = "Example Domain"
        mock_page.get_by_role.return_value.first = heading_el
        mock_page.screenshot = MagicMock()

        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page

        mock_browser_type = MagicMock()
        mock_browser_type.launch.return_value = mock_browser

        mock_pw = MagicMock()
        mock_pw.chromium = mock_browser_type

        with patch("practice5.sync_playwright") as mock_sp:
            mock_sp.return_value.__enter__.return_value = mock_pw
            result = check_website_core(
                url="https://example.com/",
                browser_name="chromium",
                headless=True,
                timeout_ms=30_000,
            )

        assert isinstance(result, CheckResult)
        assert result.http_status == 200
        assert result.success is True
        assert result.page_title == "Example Domain"
        assert result.heading == "Example Domain"
        assert result.final_url == "https://example.com/"

    def test_handles_exception(self) -> None:
        """確認例外時回傳 error 訊息而非崩潰。"""
        with patch("practice5.sync_playwright") as mock_sp:
            mock_sp.return_value.__enter__.side_effect = RuntimeError("連線失敗")
            result = check_website_core(url="https://example.com/")

        assert result.success is False
        assert "連線失敗" in result.error
        assert result.status_label == "失敗"
