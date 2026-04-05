# Cross-Skill Scheduler — PRD

## Original Problem Statement
Create a cross-skill schedule system in Python for 212 agents using a Greedy Search algorithm. The system evaluates shift combinations to find the best fit, considering off-day profiles, project-specific shifts, and multi-project SLA requirements (English + Language).

## Architecture
- **Backend**: FastAPI (Python) with NumPy, openpyxl, xlsxwriter
- **Frontend**: React with Recharts for visualization, Phosphor icons
- **Database**: MongoDB for schedule persistence
- **Algorithm**: Greedy optimization with primary (gap coverage x 1000) + secondary (volume buffer x 1) scoring

## Shift Definitions
### English (9 shifts)
E05: 05:00-14:00, E07: 07:00-16:00, E08: 08:00-17:00, E09: 09:00-18:00, E11: 11:00-20:00, E14: 14:00-23:00, E16: 16:00-01:00, E18: 18:00-03:00, E20: 20:00-05:00

### Language (5 shifts)
L07: 07:00-16:00, L08: 08:00-17:00, L09: 09:00-18:00, L10: 10:00-19:00, L11: 11:00-20:00

## What's Been Implemented (Jan 2026)
- [x] Excel (.xlsx) file upload + CSV fallback
- [x] Sample template download with formatted sheets (English, Language, Shift Reference)
- [x] Project-specific greedy scheduling (English shifts vs Language shifts)
- [x] 4 dashboard views: Shiftwise Count, Gap Dashboard, Agent Roster, SLA Analysis
- [x] Gap dashboard with day + project filters (Combined/English/Language)
- [x] Export all views as .xlsx
- [x] Agent roster with pagination and search
- [x] Default requirement data seeded from user-provided image
- [x] Testing: Backend 100%, Frontend 99%

## Off-Day Profiles (Default)
- 108 agents: Sat/Sun off
- 26 agents: Sun/Mon off
- 26 agents: Mon/Tue off
- 26 agents: Tue/Wed off
- 26 agents: Wed/Thu off

## Backlog
- P1: Editable off-day profiles via UI
- P1: Configurable shift definitions via UI
- P2: What-If simulator for staffing ROI
- P2: Schedule comparison (A/B testing)
- P3: Multi-sheet Excel upload (single file with English + Language sheets)
