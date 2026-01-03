# API for AutoFlip and FFmpeg

This API provides asynchronous job-based endpoints for video processing using FFmpeg and AutoFlip.

## Local Development Setup

1. Install dependencies (Python 3.10+).
2. Start Redis locally:
   - `docker run -p 6379:6379 -d redis:7-alpine`
3. Create a virtualenv, install dependencies:
   - `pip install -r api/requirements.txt`
4. Create `.env` from `.env.example` with `REDIS_URL=redis://localhost:6379` and `BASE_URL=http://localhost:8080`.
5. Start worker in a terminal:
   - `PYTHONPATH=. python api/worker.py`
6. Start API in another terminal:
   - `uvicorn api.main:app --reload --host 0.0.0.0 --port 8080`
7. Test with curl:
   - Enqueue trim:
     ```
     curl -X POST "http://localhost:8080/jobs/trim" \
       -H "Content-Type: application/json" \
       -d '{"input_url":"https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4","start":"00:00:00","end":"00:00:05"}'
     ```
   - Poll job status:
     ```
     curl http://localhost:8080/jobs/<job_id>
     ```
8. On finished, download from `http://localhost:8080/downloads/<filename>`.