import pytest
import time
import subprocess
import requests
import os
import sys
from playwright.sync_api import Page, expect

@pytest.fixture(scope="module")
def api_server():
    """実 API サーバーをバックグラウンドで起動するフィクスチャ。"""
    env = os.environ.copy()
    env["AUTH_MODE"] = "disabled"
    env["JARVIS_ENV"] = "development"
    env["PYTHONPATH"] = "."
    # 競合を避けるためのポート番号
    port = "8089"
    
    # 直接 python -m uvicorn を呼ぶ (絶対パスを使用)
    cmd = [sys.executable, "-m", "uvicorn", "jarvis_web.app:app", "--port", port, "--log-level", "info"]
    
    process = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        shell=False
    )
    
    url = f"http://localhost:{port}"
    success = False
    last_error = ""
    # 起動を待機
    for i in range(30):
        try:
            print(f"Polling {url}/api/health (attempt {i})...")
            resp = requests.get(f"{url}/api/health", timeout=2)
            if resp.status_code == 200:
                success = True
                print("API Server is ready!")
                break
        except Exception as e:
            last_error = str(e)
        time.sleep(1)

    if not success:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True)
        else:
            process.terminate()
        raise RuntimeError(f"API Server failed to start on {url}. i={i}, Last error: {last_error}")
        
    yield url
    
    print("Stopping API Server...")
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True)
    else:
        process.terminate()

@pytest.fixture(scope="module")
def dashboard_server():
    """Dashboard 静的ファイルを配信するサーバーを起動するフィクスチャ。"""
    port = "8081"
    process = subprocess.Popen(
        ["python", "-m", "http.server", port, "--directory", "dashboard"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    
    url = f"http://localhost:{port}"
    success = False
    for _ in range(10):
        try:
            resp = requests.get(url, timeout=1)
            if resp.status_code == 200:
                success = True
                break
        except:
            pass
        time.sleep(1)
    
    if not success:
        process.terminate()
        raise RuntimeError(f"Dashboard server failed to start on {url}")

    yield url
    process.terminate()

def test_dashboard_real_api_integration(page: Page, api_server, dashboard_server):
    """Dashboard が設定された実 API と疎通できることを確認する。"""
    page.on("console", lambda msg: print(f"Browser console: {msg.text}"))
    
    print("Navigating to settings...")
    page.goto(f"{dashboard_server}/settings.html")
    page.fill('[data-testid="api-base"]', api_server)
    page.fill('[data-testid="api-token"]', "test-token")
    page.click('[data-testid="save-settings"]')
    
    print("Navigating to ops...")
    page.goto(f"{dashboard_server}/ops.html")
    
    api_status_card = page.locator('.status-card[data-key="api"]')
    api_badge = api_status_card.locator('[data-role="status"]')
    
    print("Waiting for health status 'ok'...")
    expect(api_badge).to_contain_text("ok", timeout=15000, ignore_case=True)
    
    print("Navigating to index...")
    page.goto(f"{dashboard_server}/index.html")
    
    empty_notice = page.locator('#latest-runs-empty')
    expect(empty_notice).to_be_visible()
    expect(empty_notice).not_to_contain_text("未接続")
    print("Test passed successfully!")
