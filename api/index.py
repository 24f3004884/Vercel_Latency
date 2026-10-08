# api/index.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import json

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Request body schema
class MetricsRequest(BaseModel):
    regions: list[str]
    threshold_ms: int

@app.post("/metrics")
async def compute_metrics(req: MetricsRequest):
    # Load telemetry list
    with open("api/q-vercel-latency.json", "r") as f:
        telemetry = json.load(f)

    results = {}
    for region in req.regions:
        # Filter list by region
        data = [d for d in telemetry if d["region"] == region]
        if not data:
            results[region] = {"error": "No data"}
            continue

        latencies = [d["latency_ms"] for d in data if "latency_ms" in d]
        uptimes = [d["uptime_pct"] for d in data if "uptime_pct" in d]

        avg_latency = float(np.mean(latencies)) if latencies else 0.0
        p95_latency = float(np.percentile(latencies, 95)) if latencies else 0.0
        avg_uptime = float(np.mean(uptimes)) if uptimes else 0.0
        breaches = sum(1 for l in latencies if l > req.threshold_ms)

        results[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches,
        }

    return results
