import time
import sys
import os
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def mock_generate_caption(*args, **kwargs):
    time.sleep(1.0) # Simulate blocking work
    return "a photo of a cat"

def run_test(threads: int):
    print(f"Testing with threads={threads}...")
    urls = [f"http://example.com/image{i}.jpg" for i in range(5)]
    
    # Mock response object
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "image/jpeg"}
    mock_response.content = b"fakeimagebytes"
    mock_response.raise_for_status = MagicMock()

    # We need to mock httpx used in the route
    # Since we are using TestClient for the API call, the API implementation uses httpx
    # We will patch httpx.AsyncClient.get
    
    start_time = time.time()
    
    with patch("src.services.vision.vision_service.generate_caption", side_effect=mock_generate_caption):
        with patch("httpx.AsyncClient.get", return_value=mock_response) as mock_get:
             response = client.post(
                 "/tag-image/urls-batch",
                 data={
                     "urls": urls,
                     "threads": threads
                 }
             )
    
    end_time = time.time()
    duration = end_time - start_time
    print(f"Status: {response.status_code}")
    print(f"Duration: {duration:.2f} seconds")
    return duration

if __name__ == "__main__":
    t1 = run_test(threads=1)
    t2 = run_test(threads=5)
    
    print("\n--- Results ---")
    print(f"1 Thread: {t1:.2f}s")
    print(f"5 Threads: {t2:.2f}s")
    
    if t1 > 4.0 and t2 < 2.0:
        print("SUCCESS: Multi-threading is working!")
    else:
        print("FAILURE: Speedup expected.")
