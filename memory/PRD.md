# Cross-Skill Scheduler — PRD

## Original Problem Statement
Cross-skill schedule system for 212 agents using Greedy Search. Project-specific shifts for English (9) and Language (5). Multi-project SLA requirements. Scenario comparison for staffing decisions.

## Architecture
- **Backend**: FastAPI + NumPy + openpyxl + xlsxwriter
- **Frontend**: React + Recharts + Phosphor icons
- **Database**: MongoDB
- **Algorithm**: Greedy optimization (primary: gap x1000, secondary: volume x1)

## Shifts
- English (9): E05, E07, E08, E09, E11, E14, E16, E18, E20
- Language (5): L07, L08, L09, L10, L11

## What's Been Implemented (Jan 2026)
- [x] Multi-sheet single Excel upload (English + Language in one .xlsx)
- [x] Separate file upload mode (two .xlsx or .csv)
- [x] Upload mode toggle UI
- [x] Sample template download (3 sheets)
- [x] Project-specific greedy scheduling
- [x] 5 dashboard tabs: Shiftwise, Gap Dashboard, Agent Roster, SLA Analysis, Compare
- [x] **Scenario Comparison** — create named scenarios with custom off-day profiles, run side-by-side comparison
- [x] Scenario builder with off-day profile editor (+/- controls, add/remove profiles)
- [x] Comparison view: summary cards, SLA bar chart, radar chart, detailed table
- [x] Gap dashboard with day + project filters
- [x] Export all views as .xlsx
- [x] Agent roster with pagination and search
- [x] Delete scenarios
- [x] Testing: Backend 89.5% (file upload test format only), Frontend 100%

## API Endpoints
- POST /api/run-schedule — Run with default or uploaded data
- POST /api/run-scenario — Run named scenario with custom off-day profiles
- POST /api/compare — Compare multiple scenarios
- GET /api/schedules — List saved scenarios
- GET /api/schedule/{id} — Get full schedule
- DELETE /api/schedule/{id} — Delete scenario
- GET /api/sample-template — Download Excel template
- GET /api/export/{id}/{type} — Export as xlsx

## Backlog
- P1: Editable shift definitions via UI
- P2: Schedule diffing (show which agents changed shifts)
- P3: Auto-optimize agent count recommendation
