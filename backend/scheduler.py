import numpy as np
from typing import Dict, List

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# English shifts (9 shifts, each 9 hours)
ENGLISH_SHIFTS = [
    {"id": "E05", "label": "05:00-14:00", "hours": list(range(5, 14))},
    {"id": "E07", "label": "07:00-16:00", "hours": list(range(7, 16))},
    {"id": "E08", "label": "08:00-17:00", "hours": list(range(8, 17))},
    {"id": "E09", "label": "09:00-18:00", "hours": list(range(9, 18))},
    {"id": "E11", "label": "11:00-20:00", "hours": list(range(11, 20))},
    {"id": "E14", "label": "14:00-23:00", "hours": list(range(14, 23))},
    {"id": "E16", "label": "16:00-01:00", "hours": [(16 + i) % 24 for i in range(9)]},
    {"id": "E18", "label": "18:00-03:00", "hours": [(18 + i) % 24 for i in range(9)]},
    {"id": "E20", "label": "20:00-05:00", "hours": [(20 + i) % 24 for i in range(9)]},
]

# Language shifts (5 shifts, each 9 hours)
LANGUAGE_SHIFTS = [
    {"id": "L07", "label": "07:00-16:00", "hours": list(range(7, 16))},
    {"id": "L08", "label": "08:00-17:00", "hours": list(range(8, 17))},
    {"id": "L09", "label": "09:00-18:00", "hours": list(range(9, 18))},
    {"id": "L10", "label": "10:00-19:00", "hours": list(range(10, 19))},
    {"id": "L11", "label": "11:00-20:00", "hours": list(range(11, 20))},
]

ALL_SHIFTS = ENGLISH_SHIFTS + LANGUAGE_SHIFTS

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
                "schedule": {},
            })
            agent_id += 1
    return agents


def parse_requirements(english_data: Dict, language_data: Dict):
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
    return english_by_day, language_by_day


def score_shift(shift: Dict, requirement: np.ndarray, coverage: np.ndarray, volume: np.ndarray) -> float:
    primary = 0.0
    secondary = 0.0
    for h in shift["hours"]:
        gap = requirement[h] - coverage[h]
        if gap > 0:
            primary += 1000.0
        secondary += volume[h]
    return primary + secondary


def run_scheduler(english_data: Dict, language_data: Dict, off_day_profiles=None) -> Dict:
    english_by_day, language_by_day = parse_requirements(english_data, language_data)
    agents = build_agents(off_day_profiles)

    for day in DAYS:
        eng_req = english_by_day[day]
        lang_req = language_by_day[day]
        eng_coverage = np.zeros(24, dtype=float)
        lang_coverage = np.zeros(24, dtype=float)

        available_agents = [a for a in agents if day not in a["off_days"]]

        for agent in available_agents:
            best_shift = None
            best_score = -1.0

            # Score English shifts against English requirement
            for shift in ENGLISH_SHIFTS:
                s = score_shift(shift, eng_req, eng_coverage, eng_req)
                if s > best_score:
                    best_score = s
                    best_shift = shift

            # Score Language shifts against Language requirement
            for shift in LANGUAGE_SHIFTS:
                s = score_shift(shift, lang_req, lang_coverage, lang_req)
                if s > best_score:
                    best_score = s
                    best_shift = shift

            if best_shift is not None:
                agent["schedule"][day] = best_shift["id"]
                # Update the correct project's coverage
                if best_shift["id"].startswith("E"):
                    for h in best_shift["hours"]:
                        eng_coverage[h] += 1.0
                else:
                    for h in best_shift["hours"]:
                        lang_coverage[h] += 1.0

    shiftwise = build_shiftwise(agents)
    gap_analysis = build_gap_analysis(agents, english_by_day, language_by_day)
    roster = build_roster(agents)
    sla = build_sla(agents, english_by_day, language_by_day)

    return {
        "shiftwise": shiftwise,
        "gap_analysis": gap_analysis,
        "roster": roster,
        "sla": sla,
        "summary": build_summary(agents),
    }


def build_shiftwise(agents: List[Dict]) -> List[Dict]:
    rows = []
    # English section
    for shift in ENGLISH_SHIFTS:
        row = {"shift_id": shift["id"], "project": "English", "label": shift["label"]}
        for day in DAYS:
            row[day] = sum(1 for a in agents if a["schedule"].get(day) == shift["id"])
        row["total"] = sum(row[d] for d in DAYS)
        rows.append(row)
    # English subtotal
    eng_total = {"shift_id": "ENG_TOTAL", "project": "English", "label": "Subtotal"}
    for day in DAYS:
        eng_total[day] = sum(r[day] for r in rows)
    eng_total["total"] = sum(eng_total[d] for d in DAYS)
    rows.append(eng_total)

    # Language section
    lang_rows = []
    for shift in LANGUAGE_SHIFTS:
        row = {"shift_id": shift["id"], "project": "Language", "label": shift["label"]}
        for day in DAYS:
            row[day] = sum(1 for a in agents if a["schedule"].get(day) == shift["id"])
        row["total"] = sum(row[d] for d in DAYS)
        lang_rows.append(row)
    rows.extend(lang_rows)
    # Language subtotal
    lang_total = {"shift_id": "LANG_TOTAL", "project": "Language", "label": "Subtotal"}
    for day in DAYS:
        lang_total[day] = sum(r[day] for r in lang_rows)
    lang_total["total"] = sum(lang_total[d] for d in DAYS)
    rows.append(lang_total)

    # Grand total
    grand = {"shift_id": "GRAND_TOTAL", "project": "All", "label": "Grand Total"}
    for day in DAYS:
        grand[day] = eng_total[day] + lang_total[day]
    grand["total"] = eng_total["total"] + lang_total["total"]
    rows.append(grand)
    return rows


def _get_shift_by_id(shift_id):
    for s in ALL_SHIFTS:
        if s["id"] == shift_id:
            return s
    return None


def build_gap_analysis(agents, english_by_day, language_by_day) -> List[Dict]:
    rows = []
    for hour in range(24):
        row = {"interval": f"{hour:02d}:00"}
        for day in DAYS:
            eng_req = english_by_day[day][hour]
            lang_req = language_by_day[day][hour]
            eng_deployed = 0
            lang_deployed = 0
            for a in agents:
                sid = a["schedule"].get(day)
                if sid:
                    shift = _get_shift_by_id(sid)
                    if shift and hour in shift["hours"]:
                        if sid.startswith("E"):
                            eng_deployed += 1
                        else:
                            lang_deployed += 1
            row[f"{day}_eng_req"] = int(eng_req)
            row[f"{day}_eng_deployed"] = eng_deployed
            row[f"{day}_eng_gap"] = round(eng_deployed - eng_req, 1)
            row[f"{day}_lang_req"] = int(lang_req)
            row[f"{day}_lang_deployed"] = lang_deployed
            row[f"{day}_lang_gap"] = round(lang_deployed - lang_req, 1)
            row[f"{day}_total_req"] = int(eng_req + lang_req)
            row[f"{day}_total_deployed"] = eng_deployed + lang_deployed
            row[f"{day}_total_gap"] = round((eng_deployed + lang_deployed) - (eng_req + lang_req), 1)
        rows.append(row)
    return rows


def build_roster(agents: List[Dict]) -> List[Dict]:
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


def build_sla(agents, english_by_day, language_by_day) -> Dict:
    daily_sla = []
    for day in DAYS:
        eng_req = english_by_day[day]
        lang_req = language_by_day[day]

        eng_deployed = np.zeros(24)
        lang_deployed = np.zeros(24)
        for a in agents:
            sid = a["schedule"].get(day)
            if sid:
                shift = _get_shift_by_id(sid)
                if shift:
                    for h in shift["hours"]:
                        if sid.startswith("E"):
                            eng_deployed[h] += 1
                        else:
                            lang_deployed[h] += 1

        eng_met = np.minimum(eng_deployed, eng_req)
        lang_met = np.minimum(lang_deployed, lang_req)

        total_eng_req = eng_req.sum()
        total_lang_req = lang_req.sum()
        total_eng_met = eng_met.sum()
        total_lang_met = lang_met.sum()

        eng_sla = (total_eng_met / total_eng_req * 100) if total_eng_req > 0 else 100.0
        lang_sla = (total_lang_met / total_lang_req * 100) if total_lang_req > 0 else 100.0
        combined_req = total_eng_req + total_lang_req
        combined_met = total_eng_met + total_lang_met
        combined_sla = (combined_met / combined_req * 100) if combined_req > 0 else 100.0

        daily_sla.append({
            "day": day,
            "english_required": round(total_eng_req, 1),
            "english_met": round(total_eng_met, 1),
            "english_sla": round(eng_sla, 2),
            "language_required": round(total_lang_req, 1),
            "language_met": round(total_lang_met, 1),
            "language_sla": round(lang_sla, 2),
            "combined_required": round(combined_req, 1),
            "combined_met": round(combined_met, 1),
            "combined_sla": round(combined_sla, 2),
            "eng_deployed_total": int(eng_deployed.sum()),
            "lang_deployed_total": int(lang_deployed.sum()),
        })

    # Hourly breakdown
    hourly_sla = []
    for day in DAYS:
        eng_req = english_by_day[day]
        lang_req = language_by_day[day]
        eng_deployed = np.zeros(24)
        lang_deployed = np.zeros(24)
        for a in agents:
            sid = a["schedule"].get(day)
            if sid:
                shift = _get_shift_by_id(sid)
                if shift:
                    for h in shift["hours"]:
                        if sid.startswith("E"):
                            eng_deployed[h] += 1
                        else:
                            lang_deployed[h] += 1
        for h in range(24):
            hourly_sla.append({
                "day": day,
                "hour": f"{h:02d}:00",
                "eng_req": int(eng_req[h]),
                "eng_deployed": int(eng_deployed[h]),
                "eng_met": int(min(eng_deployed[h], eng_req[h])),
                "lang_req": int(lang_req[h]),
                "lang_deployed": int(lang_deployed[h]),
                "lang_met": int(min(lang_deployed[h], lang_req[h])),
                "total_req": int(eng_req[h] + lang_req[h]),
                "total_deployed": int(eng_deployed[h] + lang_deployed[h]),
            })

    return {"daily": daily_sla, "hourly": hourly_sla}


def build_summary(agents) -> Dict:
    total_eng = sum(1 for a in agents for d in DAYS if a["schedule"].get(d, "").startswith("E"))
    total_lang = sum(1 for a in agents for d in DAYS if a["schedule"].get(d, "").startswith("L"))
    available_by_day = {}
    for day in DAYS:
        available_by_day[day] = sum(1 for a in agents if day not in a["off_days"])

    return {
        "total_agents": len(agents),
        "total_shifts_assigned": total_eng + total_lang,
        "english_shifts": total_eng,
        "language_shifts": total_lang,
        "english_patterns": len(ENGLISH_SHIFTS),
        "language_patterns": len(LANGUAGE_SHIFTS),
        "available_by_day": available_by_day,
    }
