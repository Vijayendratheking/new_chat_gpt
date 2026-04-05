import numpy as np
import copy
from typing import Dict, List, Tuple

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# 9 authorized shift patterns, each 9 hours
SHIFTS = [
    {"id": "S07", "start": 7, "hours": list(range(7, 16))},
    {"id": "S08", "start": 8, "hours": list(range(8, 17))},
    {"id": "S09", "start": 9, "hours": list(range(9, 18))},
    {"id": "S10", "start": 10, "hours": list(range(10, 19))},
    {"id": "S11", "start": 11, "hours": list(range(11, 20))},
    {"id": "S14", "start": 14, "hours": list(range(14, 23))},
    {"id": "S16", "start": 16, "hours": [(16 + i) % 24 for i in range(9)]},  # 16-00
    {"id": "S18", "start": 18, "hours": [(18 + i) % 24 for i in range(9)]},  # 18-02
    {"id": "S20", "start": 20, "hours": [(20 + i) % 24 for i in range(9)]},  # 20-04
]

# Default off-day profiles
DEFAULT_OFF_DAY_PROFILES = [
    {"off_days": ["Saturday", "Sunday"], "count": 108},
    {"off_days": ["Sunday", "Monday"], "count": 26},
    {"off_days": ["Monday", "Tuesday"], "count": 26},
    {"off_days": ["Tuesday", "Wednesday"], "count": 26},
    {"off_days": ["Wednesday", "Thursday"], "count": 26},
]

TOTAL_AGENTS = 212


def build_agents(off_day_profiles=None):
    if off_day_profiles is None:
        off_day_profiles = DEFAULT_OFF_DAY_PROFILES
    agents = []
    agent_id = 1
    for profile in off_day_profiles:
        for _ in range(profile["count"]):
            agents.append({
                "id": f"AGT-{agent_id:03d}",
                "off_days": set(profile["off_days"]),
                "schedule": {}  # day -> shift_id
            })
            agent_id += 1
    return agents


def parse_requirements(english_data: Dict, language_data: Dict) -> Dict[str, np.ndarray]:
    """Build combined requirement arrays. Each is shape (24,) per day."""
    combined = {}
    english_by_day = {}
    language_by_day = {}
    for day in DAYS:
        eng = np.zeros(24, dtype=float)
        lang = np.zeros(24, dtype=float)
        for hour in range(24):
            hour_key = f"{hour:02d}:00"
            eng[hour] = float(english_data.get(day, {}).get(hour_key, 0))
            lang[hour] = float(language_data.get(day, {}).get(hour_key, 0))
        english_by_day[day] = eng
        language_by_day[day] = lang
        combined[day] = eng + lang
    return combined, english_by_day, language_by_day


def score_shift(shift: Dict, requirement: np.ndarray, coverage: np.ndarray, volume: np.ndarray) -> float:
    """Score a shift based on gap coverage (primary) and volume buffer (secondary)."""
    primary = 0.0
    secondary = 0.0
    for h in shift["hours"]:
        gap = requirement[h] - coverage[h]
        if gap > 0:
            primary += 1000.0
        secondary += volume[h]
    return primary + secondary


def run_scheduler(english_data: Dict, language_data: Dict, off_day_profiles=None) -> Dict:
    """Run the greedy scheduling algorithm."""
    combined, english_by_day, language_by_day = parse_requirements(english_data, language_data)
    agents = build_agents(off_day_profiles)

    # For each day, run the greedy assignment
    for day in DAYS:
        requirement = combined[day]
        coverage = np.zeros(24, dtype=float)
        volume = requirement.copy()  # raw volume for buffer scoring

        available_agents = [a for a in agents if day not in a["off_days"]]

        for agent in available_agents:
            best_shift = None
            best_score = -1.0

            for shift in SHIFTS:
                s = score_shift(shift, requirement, coverage, volume)
                if s > best_score:
                    best_score = s
                    best_shift = shift

            if best_shift is not None:
                agent["schedule"][day] = best_shift["id"]
                for h in best_shift["hours"]:
                    coverage[h] += 1.0

    # Build results
    shiftwise = build_shiftwise(agents)
    gap_analysis = build_gap_analysis(agents, combined)
    roster = build_roster(agents)
    sla = build_sla(agents, english_by_day, language_by_day, combined)

    return {
        "shiftwise": shiftwise,
        "gap_analysis": gap_analysis,
        "roster": roster,
        "sla": sla,
        "summary": build_summary(agents, combined)
    }


def build_shiftwise(agents: List[Dict]) -> List[Dict]:
    """Count agents per shift per day."""
    rows = []
    for shift in SHIFTS:
        row = {"shift_id": shift["id"], "start": f"{shift['start']:02d}:00",
               "hours": f"{shift['hours'][0]:02d}:00-{shift['hours'][-1]:02d}:59"}
        for day in DAYS:
            count = sum(1 for a in agents if a["schedule"].get(day) == shift["id"])
            row[day] = count
        row["total"] = sum(row[d] for d in DAYS)
        rows.append(row)

    # Add totals row
    total_row = {"shift_id": "TOTAL", "start": "", "hours": ""}
    for day in DAYS:
        total_row[day] = sum(r[day] for r in rows)
    total_row["total"] = sum(total_row[d] for d in DAYS)
    rows.append(total_row)
    return rows


def build_gap_analysis(agents: List[Dict], combined: Dict) -> List[Dict]:
    """Build hour-by-hour gap analysis for each day."""
    rows = []
    for hour in range(24):
        row = {"interval": f"{hour:02d}:00"}
        for day in DAYS:
            required = combined[day][hour]
            deployed = 0
            for a in agents:
                shift_id = a["schedule"].get(day)
                if shift_id:
                    shift = next(s for s in SHIFTS if s["id"] == shift_id)
                    if hour in shift["hours"]:
                        deployed += 1
            gap = deployed - required
            row[f"{day}_required"] = int(required)
            row[f"{day}_deployed"] = deployed
            row[f"{day}_gap"] = round(gap, 1)
        rows.append(row)
    return rows


def build_roster(agents: List[Dict]) -> List[Dict]:
    """Build the agent roster table."""
    rows = []
    for a in agents:
        row = {
            "agent_id": a["id"],
            "off_days": ", ".join(sorted(a["off_days"])),
        }
        for day in DAYS:
            row[day] = a["schedule"].get(day, "OFF")
        rows.append(row)
    return rows


def build_sla(agents, english_by_day, language_by_day, combined) -> Dict:
    """Calculate SLA metrics per project per day."""
    daily_sla = []
    for day in DAYS:
        eng_req = english_by_day[day]
        lang_req = language_by_day[day]
        total_req = combined[day]

        # Calculate deployed coverage per hour
        deployed = np.zeros(24)
        for a in agents:
            shift_id = a["schedule"].get(day)
            if shift_id:
                shift = next(s for s in SHIFTS if s["id"] == shift_id)
                for h in shift["hours"]:
                    deployed[h] += 1

        # Proportional split
        eng_met = np.zeros(24)
        lang_met = np.zeros(24)
        for h in range(24):
            if total_req[h] > 0:
                ratio_eng = eng_req[h] / total_req[h]
                ratio_lang = lang_req[h] / total_req[h]
                actual = min(deployed[h], total_req[h])
                eng_met[h] = actual * ratio_eng
                lang_met[h] = actual * ratio_lang
            # If requirement is 0 but agents deployed, that's extra coverage (no SLA impact)

        total_eng_req = eng_req.sum()
        total_lang_req = lang_req.sum()
        total_eng_met = eng_met.sum()
        total_lang_met = lang_met.sum()
        total_combined_req = total_req.sum()
        eng_sla = (total_eng_met / total_eng_req * 100) if total_eng_req > 0 else 100.0
        lang_sla = (total_lang_met / total_lang_req * 100) if total_lang_req > 0 else 100.0
        combined_sla = ((total_eng_met + total_lang_met) / total_combined_req * 100) if total_combined_req > 0 else 100.0

        daily_sla.append({
            "day": day,
            "english_required": round(total_eng_req, 1),
            "english_met": round(total_eng_met, 1),
            "english_sla": round(eng_sla, 2),
            "language_required": round(total_lang_req, 1),
            "language_met": round(total_lang_met, 1),
            "language_sla": round(lang_sla, 2),
            "combined_required": round(total_combined_req, 1),
            "combined_met": round(total_eng_met + total_lang_met, 1),
            "combined_sla": round(combined_sla, 2),
            "total_deployed": int(deployed.sum()),
        })

    # Hourly breakdown for charts
    hourly_sla = []
    for day in DAYS:
        eng_req = english_by_day[day]
        lang_req = language_by_day[day]
        total_req = combined[day]
        deployed = np.zeros(24)
        for a in agents:
            shift_id = a["schedule"].get(day)
            if shift_id:
                shift = next(s for s in SHIFTS if s["id"] == shift_id)
                for h in shift["hours"]:
                    deployed[h] += 1
        for h in range(24):
            eng_m = 0
            lang_m = 0
            if total_req[h] > 0:
                ratio_eng = eng_req[h] / total_req[h]
                ratio_lang = lang_req[h] / total_req[h]
                actual = min(deployed[h], total_req[h])
                eng_m = actual * ratio_eng
                lang_m = actual * ratio_lang
            hourly_sla.append({
                "day": day,
                "hour": f"{h:02d}:00",
                "english_req": int(eng_req[h]),
                "english_met": round(eng_m, 1),
                "language_req": int(lang_req[h]),
                "language_met": round(lang_m, 1),
                "total_req": int(total_req[h]),
                "deployed": int(deployed[h]),
            })

    return {"daily": daily_sla, "hourly": hourly_sla}


def build_summary(agents, combined) -> Dict:
    """Build overall summary stats."""
    total_shifts_assigned = sum(1 for a in agents for d in DAYS if a["schedule"].get(d))
    available_by_day = {}
    for day in DAYS:
        available_by_day[day] = sum(1 for a in agents if day not in a["off_days"])

    return {
        "total_agents": len(agents),
        "total_shifts_assigned": total_shifts_assigned,
        "available_by_day": available_by_day,
        "shift_patterns": len(SHIFTS),
    }
