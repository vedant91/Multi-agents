from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import json
import uuid
import os
import tempfile
import sys
from typing import List, Optional

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from Orchestrator import run_sentinel

app = FastAPI(title="SENTINEL Core API")

# Allow requests from our React Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store job status, results, and queues
jobs = {}

def execute_sentinel(job_id: str, payload: dict, uploaded_file_paths: list, queue: asyncio.Queue):
    """Runs the blocking run_sentinel function and puts events onto the async queue."""
    def progress_callback(step: str, pct: int):
        # We use asyncio.run_coroutine_threadsafe to push to the async queue from a sync thread
        loop = payload['loop']
        asyncio.run_coroutine_threadsafe(
            queue.put({"type": "progress", "step": step, "pct": pct}),
            loop
        )

    try:
        results = run_sentinel(
            company_name=payload.get("company_name", "Unknown Company"),
            promoter_name=payload.get("promoter_name", "Unknown Promoter"),
            sector=payload.get("sector", "unknown").lower(),
            loan_amount=payload.get("loan_amount", 0.0),
            loan_purpose=payload.get("loan_purpose", ""),
            loan_tenure_months=payload.get("loan_tenure_months", 60),
            uploaded_files=uploaded_file_paths,
            primary_notes=payload.get("primary_notes", ""),
            progress_callback=progress_callback
        )
        # Put final results on queue
        loop = payload['loop']
        asyncio.run_coroutine_threadsafe(
            queue.put({"type": "complete", "results": results}),
            loop
        )
    except Exception as e:
        loop = payload['loop']
        asyncio.run_coroutine_threadsafe(
            queue.put({"type": "error", "message": str(e)}),
            loop
        )
    finally:
        # Cleanup temporary files
        for path in uploaded_file_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass


@app.post("/api/analyze")
async def start_analysis(
    company_name: str = Form(...),
    promoter_name: str = Form(...),
    sector: str = Form(...),
    loan_amount: float = Form(...),
    loan_purpose: str = Form(""),
    loan_tenure_months: int = Form(60),
    files: List[UploadFile] = File(None)
):
    job_id = str(uuid.uuid4())
    
    # Save files to temp paths
    temp_file_paths = []
    if files:
        for file in files:
            if file.filename:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                content = await file.read()
                tmp.write(content)
                tmp.close()
                temp_file_paths.append(tmp.name)

    queue = asyncio.Queue()
    jobs[job_id] = {
        "queue": queue,
        "status": "running"
    }

    # Pass the current event loop down so the thread can push into the queue safely
    payload = {
        "company_name": company_name,
        "promoter_name": promoter_name,
        "sector": sector,
        "loan_amount": loan_amount,
        "loan_purpose": loan_purpose,
        "loan_tenure_months": loan_tenure_months,
        "loop": asyncio.get_running_loop()
    }

    # Run the blocking orchestrator in a separate thread
    asyncio.create_task(asyncio.to_thread(execute_sentinel, job_id, payload, temp_file_paths, queue))

    return {"job_id": job_id, "status": "started"}


@app.get("/api/stream/{job_id}")
async def stream_analysis(job_id: str):
    if job_id not in jobs:
        return {"error": "Job not found"}

    queue = jobs[job_id]["queue"]

    async def event_generator():
        try:
            while True:
                msg = await queue.get()
                
                if msg["type"] == "progress":
                    yield f"data: {json.dumps(msg)}\n\n"
                
                elif msg["type"] == "complete":
                    # Sanitize the cam_doc_path since Windows paths trip up JSON serialization sometimes if not dumped properly
                    # Also, some agents might return unexpected non-serializable objects (though mostly dicts/strings)
                    # Use default=str just in case
                    yield f"data: {json.dumps(msg, default=str)}\n\n"
                    break
                    
                elif msg["type"] == "error":
                    yield f"data: {json.dumps(msg)}\n\n"
                    break

        except asyncio.CancelledError:
            print(f"Client disconnected for job {job_id}")

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
