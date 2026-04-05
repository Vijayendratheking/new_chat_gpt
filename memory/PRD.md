# Cross-Skill Scheduler — PRD

## Original Problem Statement
Create a cross-skill schedule system in Python for 212 agents using a Greedy Search algorithm. The system evaluates thousands of shift combinations to find the best fit, considering off-day profiles, 9 authorized shift patterns (S07-S20, 9hrs each), and multi-project SLA requirements (English + Language). Outputs: Shiftwise Count DataFrame, Interval Gap Dashboard, Agent Roster Table, SLA Calculation.

## Architecture
- **Backend**: FastAPI (Python) with NumPy for array operations
- **Frontend**: React with Recharts for visualization
- **Database**: MongoDB for schedule persistence
- **Algorithm**: Greedy optimization with primary (gap coverage × 1000) and secondary (volume buffer × 1) scoring

## User Personas
- **Operations Manager**: Uploads requirement CSVs, runs scheduler, reviews SLA
- **Workforce Planner**: Analyzes gap dashboard, exports roster for execution

## Core Requirements (Static)
1. CSV upload for English & Language requirements
2. Greedy scheduling algorithm with 9 shift patterns
3. Off-day profile management (5 profiles, 212 agents)
4. 4 output views: Shiftwise, Gap Dashboard, Roster, SLA
5. CSV export for all views

## What's Been Implemented (Jan 2026)
- [x] Backend scheduler engine with greedy algorithm
- [x] Default requirement data seeded from user-provided image
- [x] CSV upload and parsing
- [x] All 4 dashboard views with charts and tables
- [x] Agent roster with pagination and search
- [x] CSV export functionality
- [x] MongoDB persistence for schedule results
- [x] Testing: Backend 100%, Frontend 98%

## Backlog
- P1: Editable off-day profiles via UI
- P1: Configurable shift definitions
- P2: Schedule comparison (A/B testing)
- P2: What-If simulator for staffing ROI
- P3: Real-time schedule updates via WebSocket
