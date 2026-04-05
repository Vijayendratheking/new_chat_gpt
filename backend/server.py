from fastapi import FastAPI, APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import io
import csv
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional
import uuid
from datetime import datetime, timezone

from scheduler import run_scheduler, DAYS, SHIFTS, DEFAULT_OFF_DAY_PROFILES

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Default requirement data from the uploaded image
DEFAULT_ENGLISH = {
    "Monday":    {"00:00":7,"01:00":4,"02:00":3,"03:00":3,"04:00":3,"05:00":3,"06:00":7,"07:00":16,"08:00":26,"09:00":33,"10:00":38,"11:00":39,"12:00":39,"13:00":39,"14:00":38,"15:00":37,"16:00":38,"17:00":36,"18:00":36,"19:00":35,"20:00":32,"21:00":28,"22:00":20,"23:00":13},
    "Tuesday":   {"00:00":8,"01:00":4,"02:00":3,"03:00":3,"04:00":3,"05:00":3,"06:00":7,"07:00":20,"08:00":26,"09:00":32,"10:00":33,"11:00":34,"12:00":34,"13:00":35,"14:00":35,"15:00":35,"16:00":35,"17:00":34,"18:00":32,"19:00":32,"20:00":29,"21:00":26,"22:00":21,"23:00":13},
    "Wednesday": {"00:00":8,"01:00":5,"02:00":3,"03:00":3,"04:00":3,"05:00":3,"06:00":8,"07:00":19,"08:00":25,"09:00":32,"10:00":35,"11:00":36,"12:00":37,"13:00":38,"14:00":38,"15:00":37,"16:00":36,"17:00":34,"18:00":32,"19:00":31,"20:00":30,"21:00":27,"22:00":23,"23:00":14},
    "Thursday":  {"00:00":7,"01:00":5,"02:00":3,"03:00":3,"04:00":3,"05:00":3,"06:00":8,"07:00":17,"08:00":0,"09:00":28,"10:00":30,"11:00":31,"12:00":32,"13:00":33,"14:00":33,"15:00":33,"16:00":32,"17:00":30,"18:00":29,"19:00":28,"20:00":27,"21:00":24,"22:00":18,"23:00":13},
    "Friday":    {"00:00":8,"01:00":5,"02:00":3,"03:00":3,"04:00":3,"05:00":3,"06:00":8,"07:00":18,"08:00":24,"09:00":29,"10:00":32,"11:00":32,"12:00":33,"13:00":34,"14:00":33,"15:00":33,"16:00":32,"17:00":30,"18:00":29,"19:00":26,"20:00":23,"21:00":21,"22:00":15,"23:00":11},
    "Saturday":  {"00:00":6,"01:00":4,"02:00":2,"03:00":2,"04:00":2,"05:00":2,"06:00":5,"07:00":15,"08:00":20,"09:00":25,"10:00":27,"11:00":27,"12:00":27,"13:00":28,"14:00":26,"15:00":25,"16:00":25,"17:00":23,"18:00":20,"19:00":18,"20:00":17,"21:00":14,"22:00":12,"23:00":9},
    "Sunday":    {"00:00":5,"01:00":2,"02:00":2,"03:00":2,"04:00":2,"05:00":2,"06:00":3,"07:00":10,"08:00":17,"09:00":20,"10:00":21,"11:00":22,"12:00":22,"13:00":23,"14:00":23,"15:00":22,"16:00":21,"17:00":20,"18:00":20,"19:00":19,"20:00":18,"21:00":16,"22:00":12,"23:00":8},
}

DEFAULT_LANGUAGE = {
    "Monday":    {"00:00":0,"01:00":0,"02:00":0,"03:00":0,"04:00":0,"05:00":0,"06:00":0,"07:00":43,"08:00":53,"09:00":60,"10:00":60,"11:00":60,"12:00":59,"13:00":55,"14:00":51,"15:00":50,"16:00":50,"17:00":50,"18:00":41,"19:00":17,"20:00":0,"21:00":0,"22:00":0,"23:00":0},
    "Tuesday":   {"00:00":0,"01:00":0,"02:00":0,"03:00":0,"04:00":0,"05:00":0,"06:00":0,"07:00":43,"08:00":50,"09:00":52,"10:00":53,"11:00":53,"12:00":51,"13:00":49,"14:00":49,"15:00":49,"16:00":47,"17:00":46,"18:00":40,"19:00":18,"20:00":0,"21:00":0,"22:00":0,"23:00":0},
    "Wednesday": {"00:00":0,"01:00":0,"02:00":0,"03:00":0,"04:00":0,"05:00":0,"06:00":0,"07:00":41,"08:00":51,"09:00":54,"10:00":55,"11:00":55,"12:00":52,"13:00":49,"14:00":49,"15:00":48,"16:00":47,"17:00":43,"18:00":34,"19:00":15,"20:00":0,"21:00":0,"22:00":0,"23:00":0},
    "Thursday":  {"00:00":0,"01:00":0,"02:00":0,"03:00":0,"04:00":0,"05:00":0,"06:00":0,"07:00":40,"08:00":47,"09:00":49,"10:00":49,"11:00":48,"12:00":48,"13:00":47,"14:00":46,"15:00":46,"16:00":45,"17:00":42,"18:00":35,"19:00":18,"20:00":0,"21:00":0,"22:00":0,"23:00":0},
    "Friday":    {"00:00":0,"01:00":0,"02:00":0,"03:00":0,"04:00":0,"05:00":0,"06:00":0,"07:00":36,"08:00":48,"09:00":49,"10:00":49,"11:00":49,"12:00":48,"13:00":45,"14:00":43,"15:00":42,"16:00":39,"17:00":35,"18:00":28,"19:00":13,"20:00":0,"21:00":0,"22:00":0,"23:00":0},
    "Saturday":  {"00:00":0,"01:00":0,"02:00":0,"03:00":0,"04:00":0,"05:00":0,"06:00":0,"07:00":0,"08:00":41,"09:00":43,"10:00":43,"11:00":42,"12:00":39,"13:00":35,"14:00":31,"15:00":29,"16:00":14,"17:00":0,"18:00":0,"19:00":0,"20:00":0,"21:00":0,"22:00":0,"23:00":0},
    "Sunday":    {"00:00":0,"01:00":0,"02:00":0,"03:00":0,"04:00":0,"05:00":0,"06:00":0,"07:00":0,"08:00":24,"09:00":25,"10:00":26,"11:00":24,"12:00":23,"13:00":23,"14:00":23,"15:00":20,"16:00":10,"17:00":0,"18:00":0,"19:00":0,"20:00":0,"21:00":0,"22:00":0,"23:00":0},
}


def parse_csv_to_dict(content: str) -> Dict:
    """Parse CSV content into nested dict {day: {hour: value}}."""
    reader = csv.DictReader(io.StringIO(content))
    result = {}
    for day in DAYS:
        result[day] = {}
    for row in reader:
        interval = row.get("Interval", row.get("interval", "")).strip()
        if not interval:
            continue
        for day in DAYS:
            val = row.get(day, "0").strip()
            try:
                result[day][interval] = float(val) if val else 0
            except ValueError:
                result[day][interval] = 0
    return result


@api_router.get("/")
async def root():
    return {"message": "Cross-Skill Scheduler API"}


@api_router.get("/default-requirements")
async def get_default_requirements():
    """Return the default requirement data."""
    return {
        "english": DEFAULT_ENGLISH,
        "language": DEFAULT_LANGUAGE,
    }


@api_router.post("/run-schedule")
async def run_schedule_endpoint(
    english_file: Optional[UploadFile] = File(None),
    language_file: Optional[UploadFile] = File(None),
):
    """Run the scheduling algorithm. Uses default data if no files uploaded."""
    if english_file and english_file.filename:
        eng_content = (await english_file.read()).decode("utf-8")
        english_data = parse_csv_to_dict(eng_content)
    else:
        english_data = DEFAULT_ENGLISH

    if language_file and language_file.filename:
        lang_content = (await language_file.read()).decode("utf-8")
        language_data = parse_csv_to_dict(lang_content)
    else:
        language_data = DEFAULT_LANGUAGE

    result = run_scheduler(english_data, language_data)

    # Store in MongoDB
    schedule_id = str(uuid.uuid4())
    doc = {
        "id": schedule_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "english_input": english_data,
        "language_input": language_data,
        "shiftwise": result["shiftwise"],
        "gap_analysis": result["gap_analysis"],
        "roster": result["roster"],
        "sla": result["sla"],
        "summary": result["summary"],
    }
    await db.schedules.insert_one(doc)

    return {
        "id": schedule_id,
        "shiftwise": result["shiftwise"],
        "gap_analysis": result["gap_analysis"],
        "roster": result["roster"],
        "sla": result["sla"],
        "summary": result["summary"],
    }


@api_router.get("/schedules")
async def list_schedules():
    """List all schedules (summary only)."""
    schedules = await db.schedules.find(
        {}, {"_id": 0, "id": 1, "timestamp": 1, "summary": 1}
    ).sort("timestamp", -1).to_list(50)
    return schedules


@api_router.get("/schedule/{schedule_id}")
async def get_schedule(schedule_id: str):
    """Get full schedule results."""
    doc = await db.schedules.find_one({"id": schedule_id}, {"_id": 0})
    if not doc:
        return {"error": "Schedule not found"}
    return doc


@api_router.get("/export/{schedule_id}/{export_type}")
async def export_csv(schedule_id: str, export_type: str):
    """Export schedule data as CSV."""
    doc = await db.schedules.find_one({"id": schedule_id}, {"_id": 0})
    if not doc:
        return {"error": "Schedule not found"}

    output = io.StringIO()
    writer = csv.writer(output)

    if export_type == "shiftwise":
        headers = ["Shift ID", "Hours"] + DAYS + ["Total"]
        writer.writerow(headers)
        for row in doc["shiftwise"]:
            writer.writerow([row["shift_id"], row["hours"]] + [row[d] for d in DAYS] + [row["total"]])

    elif export_type == "roster":
        headers = ["Agent ID", "Off Days"] + DAYS
        writer.writerow(headers)
        for row in doc["roster"]:
            writer.writerow([row["agent_id"], row["off_days"]] + [row[d] for d in DAYS])

    elif export_type == "gap":
        headers = ["Interval"]
        for d in DAYS:
            headers += [f"{d} Req", f"{d} Deployed", f"{d} Gap"]
        writer.writerow(headers)
        for row in doc["gap_analysis"]:
            vals = [row["interval"]]
            for d in DAYS:
                vals += [row[f"{d}_required"], row[f"{d}_deployed"], row[f"{d}_gap"]]
            writer.writerow(vals)

    elif export_type == "sla":
        headers = ["Day", "Eng Required", "Eng Met", "Eng SLA%", "Lang Required", "Lang Met", "Lang SLA%", "Combined Required", "Combined Met", "Combined SLA%"]
        writer.writerow(headers)
        for row in doc["sla"]["daily"]:
            writer.writerow([
                row["day"], row["english_required"], row["english_met"], row["english_sla"],
                row["language_required"], row["language_met"], row["language_sla"],
                row["combined_required"], row["combined_met"], row["combined_sla"],
            ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={export_type}_{schedule_id[:8]}.csv"}
    )


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
