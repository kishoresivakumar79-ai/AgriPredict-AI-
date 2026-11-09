"""
Automated Screenshot Capture Engine for AgriPredict AI.
Launches Streamlit and FastAPI servers, waits for readiness,
and captures pixel-perfect high-resolution screenshots of all views
using Chrome Headless mode.
"""
import subprocess
import time
import urllib.request
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SCREENSHOTS_DIR = PROJECT_ROOT / "docs" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_PATH):
    CHROME_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

def wait_for_server(url: str, timeout: int = 25):
    """Waits for HTTP server to become responsive."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status in [200, 304]:
                    print(f"Server at {url} is ready!")
                    return True
        except Exception:
            time.sleep(1)
    print(f"Warning: Timed out waiting for {url}")
    return False

def capture_screenshot(url: str, output_path: Path, width: int = 1440, height: int = 960, delay: int = 4):
    """Uses Chrome headless to render and capture screenshot."""
    print(f"Capturing: {url} -> {output_path.name}")
    # Give the single-page application a couple seconds to load charts
    time.sleep(delay)
    
    cmd = [
        CHROME_PATH,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        f"--window-size={width},{height}",
        "--hide-scrollbars",
        f"--screenshot={str(output_path)}",
        url
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if output_path.exists():
        print(f" Successfully saved: {output_path.name} ({output_path.stat().st_size:,} bytes)")
    else:
        print(f"❌ Failed to capture: {output_path.name}")

def main():
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)

    # 1. Start Streamlit Server
    print("\n--- Starting Streamlit Dashboard ---")
    st_cmd = [
        sys.executable,
        "-m", "streamlit", "run",
        str(PROJECT_ROOT / "frontend" / "app.py"),
        "--server.port=8501",
        "--server.headless=true",
        "--browser.gatherUsageStats=false"
    ]
    st_proc = subprocess.Popen(st_cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        ready = wait_for_server("http://localhost:8501")
        if ready:
            views = [
                ("http://localhost:8501/?view=overview", SCREENSHOTS_DIR / "01_dashboard_overview.png", 4),
                ("http://localhost:8501/?view=price_prediction", SCREENSHOTS_DIR / "02_price_prediction.png", 5),
                ("http://localhost:8501/?view=market_analysis", SCREENSHOTS_DIR / "03_market_comparison.png", 4),
                ("http://localhost:8501/?view=weather_analysis", SCREENSHOTS_DIR / "04_weather_analysis.png", 4),
                ("http://localhost:8501/?view=supply_demand", SCREENSHOTS_DIR / "05_supply_demand.png", 4),
                ("http://localhost:8501/?view=profit_calculator", SCREENSHOTS_DIR / "06_profit_and_storage.png", 4),
                ("http://localhost:8501/?view=scenario_simulator", SCREENSHOTS_DIR / "07_scenario_digital_twin.png", 4),
                ("http://localhost:8501/?view=assistant_and_reports", SCREENSHOTS_DIR / "08_ai_assistant_reports.png", 4)
            ]

            for url, out_file, wait_s in views:
                capture_screenshot(url, out_file, delay=wait_s)
    finally:
        print("Stopping Streamlit...")
        st_proc.terminate()
        try:
            st_proc.wait(timeout=3)
        except Exception:
            st_proc.kill()

    # 2. Start FastAPI Server
    print("\n--- Starting FastAPI Backend ---")
    api_cmd = [
        sys.executable,
        "-m", "uvicorn",
        "backend.main:app",
        "--host=127.0.0.1",
        "--port=8000"
    ]
    api_proc = subprocess.Popen(api_cmd, cwd=str(PROJECT_ROOT), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        ready = wait_for_server("http://127.0.0.1:8000/health")
        if ready:
            docs_url = "http://127.0.0.1:8000/docs"
            docs_out = SCREENSHOTS_DIR / "09_fastapi_swagger_docs.png"
            capture_screenshot(docs_url, docs_out, width=1440, height=900, delay=3)
    finally:
        print("Stopping FastAPI...")
        api_proc.terminate()
        try:
            api_proc.wait(timeout=3)
        except Exception:
            api_proc.kill()

    print("\n All screenshot captures complete!")

if __name__ == "__main__":
    main()

