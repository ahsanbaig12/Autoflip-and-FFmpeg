import time
import requests

API_BASE = "http://localhost:8080"

# Sample video URL (small one)
VIDEO_URL = "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4"  # Note: this might not be exact, but for example

def test_trim():
    # Submit trim job
    payload = {
        "input_url": VIDEO_URL,
        "start": "00:00:00",
        "end": "00:00:05"
    }
    response = requests.post(f"{API_BASE}/jobs/trim", json=payload)
    assert response.status_code == 200
    data = response.json()
    job_id = data["job_id"]
    print(f"Job submitted: {job_id}")

    # Poll status
    while True:
        response = requests.get(f"{API_BASE}/jobs/{job_id}")
        assert response.status_code == 200
        status_data = response.json()
        print(f"Status: {status_data['status']}")
        if status_data["status"] == "finished":
            result_url = status_data["result_url"]
            # Check download
            download_resp = requests.get(result_url)
            assert download_resp.status_code == 200
            assert len(download_resp.content) > 0
            print("Test passed!")
            break
        elif status_data["status"] == "failed":
            raise AssertionError(f"Job failed: {status_data.get('error')}")
        time.sleep(2)

if __name__ == "__main__":
    test_trim()