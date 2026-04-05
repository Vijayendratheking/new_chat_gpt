# Cross-Skill Scheduler — PRD

## Original Problem Statement
Create a cross-skill schedule system in Python for 212 agents using a Greedy Search algorithm. Project-specific shifts for English (9 patterns) and Language (5 patterns). Multi-project SLA requirements.

## Architecture
- **Backend**: FastAPI (Python) with NumPy, openpyxl, xlsxwriter
- **Frontend**: React with Recharts, Phosphor icons
- **Database**: MongoDB for schedule persistence
- **Algorithm**: Greedy optimization — primary (gap coverage x 1000) + secondary (volume buffer x 1)

## Shift Definitions
### English (9 shifts): E05 05:00-14:00, E07 07:00-16:00, E08 08:00-17:00, E09 09:00-18:00, E11 11:00-20:00, E14 14:00-23:00, E16 16:00-01:00, E18 18:00-03:00, E20 20:00-05:00
### Language (5 shifts): L07 07:00-16:00, L08 08:00-17:00, L09 09:00-18:00, L10 10:00-19:00, L11 11:00-20:00

## What's Been Implemented (Jan 2026)
- [x] Multi-sheet single Excel upload (English + Language sheets in one .xlsx)
- [x] Separate file upload mode (two individual .xlsx or .csv files)
- [x] Upload mode toggle UI (Single File / Separate Files)
- [x] Sample template download with 3 sheets (English, Language, Shift Reference)
- [x] Project-specific greedy scheduling engine
- [x] 4 dashboard views: Shiftwise Count, Gap Dashboard, Agent Roster, SLA Analysis
- [x] Gap dashboard with day + project filters (Combined/English/Language)
- [x] Export all views as .xlsx with formatting
- [x] Agent roster with pagination and search
- [x] Testing: Backend 100%, Frontend 100%

## Off-Day Profiles (Default)
- 108: Sat/Sun, 26: Sun/Mon, 26: Mon/Tue, 26: Tue/Wed, 26: Wed/Thu

## Backlog
- P1: Editable off-day profiles via UI
- P1: Configurable shift definitions via UI
- P2: What-If simulator for staffing ROI
- P2: Schedule comparison (A/B testing)
