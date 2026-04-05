import { useState, useCallback } from "react";
import "./App.css";
import axios from "axios";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area, Legend,
} from "recharts";
import {
  Upload, Play, DownloadSimple, Table, ChartBar, Users, Gauge,
  CaretLeft, CaretRight, MagnifyingGlass, ArrowsClockwise, FileXls, Scales,
} from "@phosphor-icons/react";
import ScenarioComparison from "./components/ScenarioComparison";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const DAYS_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function App() {
  const [combinedFile, setCombinedFile] = useState(null);
  const [englishFile, setEnglishFile] = useState(null);
  const [languageFile, setLanguageFile] = useState(null);
  const [uploadMode, setUploadMode] = useState("combined"); // "combined" or "separate"
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [activeTab, setActiveTab] = useState("shiftwise");
  const [selectedDay, setSelectedDay] = useState("Monday");
  const [gapProject, setGapProject] = useState("total");
  const [rosterPage, setRosterPage] = useState(0);
  const [rosterSearch, setRosterSearch] = useState("");
  const ROSTER_PAGE_SIZE = 25;

  const runSchedule = useCallback(async () => {
    setLoading(true);
    try {
      const formData = new FormData();
      if (uploadMode === "combined" && combinedFile) {
        formData.append("combined_file", combinedFile);
      } else {
        if (englishFile) formData.append("english_file", englishFile);
        if (languageFile) formData.append("language_file", languageFile);
      }
      const resp = await axios.post(`${API}/run-schedule`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(resp.data);
      setActiveTab("shiftwise");
      setRosterPage(0);
    } catch (e) {
      console.error("Schedule failed:", e);
    } finally {
      setLoading(false);
    }
  }, [uploadMode, combinedFile, englishFile, languageFile]);

  const downloadTemplate = () => {
    window.open(`${API}/sample-template`, "_blank");
  };

  const exportFile = useCallback((type) => {
    if (!result?.id) return;
    window.open(`${API}/export/${result.id}/${type}`, "_blank");
  }, [result]);

  const getShiftClass = (shift) => {
    if (shift === "OFF") return "shift-off";
    if (shift.startsWith("L")) return "shift-lang";
    const num = parseInt(shift.replace("E", ""));
    if (num <= 11) return "shift-morning";
    if (num <= 16) return "shift-afternoon";
    return "shift-night";
  };

  const getSLAClass = (val) => {
    if (val >= 95) return "sla-high";
    if (val >= 80) return "sla-mid";
    return "sla-low";
  };

  const gapClass = (v) => {
    if (v > 0) return "gap-positive";
    if (v < 0) return "gap-negative";
    return "gap-zero";
  };

  // Roster filtering + pagination
  const filteredRoster = result?.roster?.filter(r =>
    r.agent_id.toLowerCase().includes(rosterSearch.toLowerCase()) ||
    r.off_days.toLowerCase().includes(rosterSearch.toLowerCase())
  ) || [];
  const totalRosterPages = Math.ceil(filteredRoster.length / ROSTER_PAGE_SIZE);
  const pagedRoster = filteredRoster.slice(
    rosterPage * ROSTER_PAGE_SIZE,
    (rosterPage + 1) * ROSTER_PAGE_SIZE
  );

  // Gap data for selected day + project
  const gapChartData = result?.gap_analysis?.map(row => {
    const prefix = `${selectedDay}_`;
    if (gapProject === "english") {
      return { hour: row.interval, required: row[`${prefix}eng_req`], deployed: row[`${prefix}eng_deployed`], gap: row[`${prefix}eng_gap`] };
    } else if (gapProject === "language") {
      return { hour: row.interval, required: row[`${prefix}lang_req`], deployed: row[`${prefix}lang_deployed`], gap: row[`${prefix}lang_gap`] };
    }
    return { hour: row.interval, required: row[`${prefix}total_req`], deployed: row[`${prefix}total_deployed`], gap: row[`${prefix}total_gap`] };
  }) || [];

  // SLA chart data
  const slaChartData = result?.sla?.daily?.map(row => ({
    day: row.day.substring(0, 3),
    english: row.english_sla,
    language: row.language_sla,
    combined: row.combined_sla,
  })) || [];

  // Shiftwise chart - split by project
  const engShiftChart = result?.shiftwise
    ?.filter(r => r.project === "English" && !r.shift_id.includes("TOTAL"))
    .map(r => ({
      shift: r.shift_id,
      ...DAYS.reduce((acc, d, i) => ({ ...acc, [DAYS_SHORT[i]]: r[d] }), {}),
    })) || [];

  const langShiftChart = result?.shiftwise
    ?.filter(r => r.project === "Language" && !r.shift_id.includes("TOTAL"))
    .map(r => ({
      shift: r.shift_id,
      ...DAYS.reduce((acc, d, i) => ({ ...acc, [DAYS_SHORT[i]]: r[d] }), {}),
    })) || [];

  return (
    <div className="app-shell">
      <header className="app-header" data-testid="app-header">
        <h1>Cross-Skill Scheduler</h1>
        <span className="header-meta">212 Agents / 14 Shifts / 7 Days</span>
      </header>

      <main className="main-content">
        {/* Upload Panel */}
        <div className="upload-panel" data-testid="upload-panel">
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Upload size={20} weight="bold" />
            <span className="mono-label">Upload Requirements (.xlsx) or Use Defaults</span>
          </div>

          <button data-testid="download-template-btn" className="btn btn-secondary btn-sm" onClick={downloadTemplate}>
            <FileXls size={16} weight="bold" /> Download Sample Template (.xlsx)
          </button>

          {/* Upload Mode Toggle */}
          <div className="upload-mode-toggle" data-testid="upload-mode-toggle">
            <button
              data-testid="mode-combined-btn"
              className={`mode-btn ${uploadMode === "combined" ? "active" : ""}`}
              onClick={() => setUploadMode("combined")}
            >
              Single File (2 sheets)
            </button>
            <button
              data-testid="mode-separate-btn"
              className={`mode-btn ${uploadMode === "separate" ? "active" : ""}`}
              onClick={() => setUploadMode("separate")}
            >
              Separate Files
            </button>
          </div>

          {uploadMode === "combined" ? (
            <div className="file-input-group" style={{ width: "100%", maxWidth: 480 }}>
              <label htmlFor="combined-file">Combined Excel (sheets: English & Language)</label>
              <input
                data-testid="combined-file-input"
                id="combined-file"
                type="file"
                accept=".xlsx"
                onChange={e => setCombinedFile(e.target.files[0])}
              />
              {combinedFile && <span style={{ fontSize: 12, color: "#00C853" }}>{combinedFile.name}</span>}
              <span className="file-hint">Upload a single .xlsx file with an "English" sheet and a "Language" sheet — just like the template</span>
            </div>
          ) : (
            <div className="upload-grid">
              <div className="file-input-group">
                <label htmlFor="english-file">English Requirements</label>
                <input
                  data-testid="english-file-input"
                  id="english-file"
                  type="file"
                  accept=".xlsx,.csv"
                  onChange={e => setEnglishFile(e.target.files[0])}
                />
                {englishFile && <span style={{ fontSize: 12, color: "#00C853" }}>{englishFile.name}</span>}
              </div>
              <div className="file-input-group">
                <label htmlFor="language-file">Language Requirements</label>
                <input
                  data-testid="language-file-input"
                  id="language-file"
                  type="file"
                  accept=".xlsx,.csv"
                  onChange={e => setLanguageFile(e.target.files[0])}
                />
                {languageFile && <span style={{ fontSize: 12, color: "#00C853" }}>{languageFile.name}</span>}
              </div>
            </div>
          )}

          <button
            data-testid="run-schedule-btn"
            className="btn btn-primary"
            onClick={runSchedule}
            disabled={loading}
          >
            <Play size={16} weight="bold" />
            {loading ? "Computing Schedule..." : "Run Greedy Scheduler"}
          </button>
          {uploadMode === "combined" && !combinedFile && (
            <span style={{ fontSize: 12, color: "#64748B" }}>No file selected — will use default requirement data</span>
          )}
          {uploadMode === "separate" && !englishFile && !languageFile && (
            <span style={{ fontSize: 12, color: "#64748B" }}>No files selected — will use default requirement data</span>
          )}
        </div>

        {/* Loading */}
        {loading && (
          <div className="loading-overlay" data-testid="loading-overlay">
            <div className="spinner"></div>
            <span className="loading-text">Running greedy optimization for 212 agents across 14 shift patterns...</span>
          </div>
        )}

        {/* Results */}
        {result && !loading && (
          <>
            {/* Summary Cards */}
            <div className="summary-grid" data-testid="summary-grid">
              <div className="summary-card">
                <div className="card-label">Total Agents</div>
                <div className="card-value" data-testid="total-agents">{result.summary.total_agents}</div>
              </div>
              <div className="summary-card">
                <div className="card-label">English Shifts</div>
                <div className="card-value" data-testid="english-shifts">{result.summary.english_shifts}</div>
                <div className="card-sub">{result.summary.english_patterns} patterns</div>
              </div>
              <div className="summary-card">
                <div className="card-label">Language Shifts</div>
                <div className="card-value" data-testid="language-shifts">{result.summary.language_shifts}</div>
                <div className="card-sub">{result.summary.language_patterns} patterns</div>
              </div>
              <div className="summary-card">
                <div className="card-label">Avg Combined SLA</div>
                <div className="card-value" data-testid="avg-sla">
                  {(result.sla.daily.reduce((s, r) => s + r.combined_sla, 0) / 7).toFixed(1)}%
                </div>
              </div>
            </div>

            {/* Tabs */}
            <div className="tabs-bar" data-testid="tabs-bar">
              {[
                { id: "shiftwise", label: "Shift Counts", icon: <Table size={14} /> },
                { id: "gap", label: "Gap Dashboard", icon: <ChartBar size={14} /> },
                { id: "roster", label: "Agent Roster", icon: <Users size={14} /> },
                { id: "sla", label: "SLA Analysis", icon: <Gauge size={14} /> },
                { id: "compare", label: "Compare", icon: <Scales size={14} /> },
              ].map(tab => (
                <button
                  key={tab.id}
                  data-testid={`tab-${tab.id}`}
                  className={`tab-item ${activeTab === tab.id ? "active" : ""}`}
                  onClick={() => setActiveTab(tab.id)}
                >
                  {tab.icon} {tab.label}
                </button>
              ))}
            </div>

            {/* === SHIFTWISE TAB === */}
            {activeTab === "shiftwise" && (
              <div data-testid="shiftwise-panel">
                <div className="export-bar">
                  <span className="section-title">Shift-Wise Agent Count</span>
                  <button data-testid="export-shiftwise-btn" className="btn btn-secondary btn-sm" onClick={() => exportFile("shiftwise")}>
                    <DownloadSimple size={14} /> Export .xlsx
                  </button>
                </div>

                {/* Charts side-by-side */}
                <div className="chart-row">
                  <div className="chart-container" style={{ flex: 1 }}>
                    <div className="chart-title">English Shifts by Day</div>
                    <ResponsiveContainer width="100%" height={260}>
                      <BarChart data={engShiftChart}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                        <XAxis dataKey="shift" tick={{ fontSize: 10, fontFamily: "IBM Plex Mono" }} />
                        <YAxis tick={{ fontSize: 10, fontFamily: "IBM Plex Mono" }} />
                        <Tooltip contentStyle={{ fontFamily: "IBM Plex Mono", fontSize: 11 }} />
                        <Legend wrapperStyle={{ fontFamily: "IBM Plex Mono", fontSize: 10 }} />
                        {DAYS_SHORT.map((d, i) => (
                          <Bar key={d} dataKey={d} fill={["#0033CC","#0055EE","#3377FF","#5599FF","#88BBFF","#FFCC00","#FF6600"][i]} />
                        ))}
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="chart-container" style={{ flex: 1 }}>
                    <div className="chart-title">Language Shifts by Day</div>
                    <ResponsiveContainer width="100%" height={260}>
                      <BarChart data={langShiftChart}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                        <XAxis dataKey="shift" tick={{ fontSize: 10, fontFamily: "IBM Plex Mono" }} />
                        <YAxis tick={{ fontSize: 10, fontFamily: "IBM Plex Mono" }} />
                        <Tooltip contentStyle={{ fontFamily: "IBM Plex Mono", fontSize: 11 }} />
                        <Legend wrapperStyle={{ fontFamily: "IBM Plex Mono", fontSize: 10 }} />
                        {DAYS_SHORT.map((d, i) => (
                          <Bar key={d} dataKey={d} fill={["#0033CC","#0055EE","#3377FF","#5599FF","#88BBFF","#FFCC00","#FF6600"][i]} />
                        ))}
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Table */}
                <div className="table-wrapper" data-testid="shiftwise-table">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Shift</th>
                        <th>Project</th>
                        <th>Time Range</th>
                        {DAYS.map(d => <th key={d} className="num">{d.substring(0, 3)}</th>)}
                        <th className="num">Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.shiftwise.map((row, i) => (
                        <tr key={i} className={row.shift_id.includes("TOTAL") ? "total-row" : ""}>
                          <td><span className="font-mono" style={{ fontWeight: 600 }}>{row.shift_id}</span></td>
                          <td>
                            <span className={`project-badge ${row.project === "English" ? "project-eng" : row.project === "Language" ? "project-lang" : ""}`}>
                              {row.project}
                            </span>
                          </td>
                          <td className="font-mono" style={{ fontSize: 11 }}>{row.label}</td>
                          {DAYS.map(d => <td key={d} className="num">{row[d]}</td>)}
                          <td className="num" style={{ fontWeight: 600 }}>{row.total}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* === GAP DASHBOARD TAB === */}
            {activeTab === "gap" && (
              <div data-testid="gap-panel">
                <div className="export-bar">
                  <span className="section-title">Interval Gap Dashboard</span>
                  <button data-testid="export-gap-btn" className="btn btn-secondary btn-sm" onClick={() => exportFile("gap")}>
                    <DownloadSimple size={14} /> Export .xlsx
                  </button>
                </div>

                {/* Day + Project selector */}
                <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 16 }}>
                  <div>
                    <div className="selector-label">Day</div>
                    <div className="day-selector" data-testid="day-selector">
                      {DAYS.map(d => (
                        <button key={d} data-testid={`day-btn-${d.toLowerCase()}`}
                          className={`day-btn ${selectedDay === d ? "active" : ""}`}
                          onClick={() => setSelectedDay(d)}>{d.substring(0, 3)}</button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <div className="selector-label">Project</div>
                    <div className="day-selector" data-testid="project-selector">
                      {[{id:"total",label:"Combined"},{id:"english",label:"English"},{id:"language",label:"Language"}].map(p => (
                        <button key={p.id} data-testid={`project-btn-${p.id}`}
                          className={`day-btn ${gapProject === p.id ? "active" : ""}`}
                          onClick={() => setGapProject(p.id)}>{p.label}</button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Area chart */}
                <div className="chart-container">
                  <div className="chart-title">Required vs Deployed — {selectedDay} ({gapProject})</div>
                  <div className="chart-legend">
                    <div className="legend-item"><div className="legend-dot" style={{ background: "#FF0000" }}></div>Required</div>
                    <div className="legend-item"><div className="legend-dot" style={{ background: "#0033CC" }}></div>Deployed</div>
                  </div>
                  <ResponsiveContainer width="100%" height={320}>
                    <AreaChart data={gapChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                      <XAxis dataKey="hour" tick={{ fontSize: 10, fontFamily: "IBM Plex Mono" }} />
                      <YAxis tick={{ fontSize: 11, fontFamily: "IBM Plex Mono" }} />
                      <Tooltip contentStyle={{ fontFamily: "IBM Plex Mono", fontSize: 12 }} />
                      <Area type="monotone" dataKey="required" stroke="#FF0000" fill="#FEE2E2" strokeWidth={2} name="Required" />
                      <Area type="monotone" dataKey="deployed" stroke="#0033CC" fill="#DBEAFE" strokeWidth={2} name="Deployed" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>

                {/* Gap table */}
                <div className="table-wrapper" data-testid="gap-table">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Interval</th>
                        <th className="num">Required</th>
                        <th className="num">Deployed</th>
                        <th className="num">Gap</th>
                      </tr>
                    </thead>
                    <tbody>
                      {gapChartData.map((row, i) => (
                        <tr key={i}>
                          <td className="font-mono">{row.hour}</td>
                          <td className="num">{row.required}</td>
                          <td className="num">{row.deployed}</td>
                          <td className={`num ${gapClass(row.gap)}`}>
                            {row.gap > 0 ? "+" : ""}{row.gap}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* === AGENT ROSTER TAB === */}
            {activeTab === "roster" && (
              <div data-testid="roster-panel">
                <div className="export-bar">
                  <span className="section-title">Agent Roster ({filteredRoster.length} agents)</span>
                  <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                    <div style={{ position: "relative" }}>
                      <MagnifyingGlass size={14} style={{ position: "absolute", left: 10, top: 10, color: "#64748B" }} />
                      <input
                        data-testid="roster-search-input"
                        className="search-input"
                        style={{ paddingLeft: 32 }}
                        placeholder="Search agent or off-day..."
                        value={rosterSearch}
                        onChange={e => { setRosterSearch(e.target.value); setRosterPage(0); }}
                      />
                    </div>
                    <button data-testid="export-roster-btn" className="btn btn-secondary btn-sm" onClick={() => exportFile("roster")}>
                      <DownloadSimple size={14} /> Export .xlsx
                    </button>
                  </div>
                </div>
                <div className="table-wrapper" data-testid="roster-table">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Agent ID</th>
                        <th>Off Days</th>
                        {DAYS.map(d => <th key={d}>{d.substring(0, 3)}</th>)}
                      </tr>
                    </thead>
                    <tbody>
                      {pagedRoster.map((row, i) => (
                        <tr key={i}>
                          <td className="font-mono" style={{ fontWeight: 600 }}>{row.agent_id}</td>
                          <td style={{ fontSize: 12, color: "#64748B" }}>{row.off_days}</td>
                          {DAYS.map(d => (
                            <td key={d}>
                              <span className={`shift-badge ${getShiftClass(row[d])}`}>{row[d]}</span>
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="pagination" data-testid="roster-pagination">
                  <button className="btn btn-secondary btn-sm" onClick={() => setRosterPage(p => Math.max(0, p - 1))}
                    disabled={rosterPage === 0} data-testid="roster-prev-btn">
                    <CaretLeft size={14} /> Prev
                  </button>
                  <span className="page-info">Page {rosterPage + 1} of {totalRosterPages || 1}</span>
                  <button className="btn btn-secondary btn-sm" onClick={() => setRosterPage(p => Math.min(totalRosterPages - 1, p + 1))}
                    disabled={rosterPage >= totalRosterPages - 1} data-testid="roster-next-btn">
                    Next <CaretRight size={14} />
                  </button>
                </div>
              </div>
            )}

            {/* === SLA TAB === */}
            {activeTab === "sla" && (
              <div data-testid="sla-panel">
                <div className="export-bar">
                  <span className="section-title">SLA Analysis</span>
                  <button data-testid="export-sla-btn" className="btn btn-secondary btn-sm" onClick={() => exportFile("sla")}>
                    <DownloadSimple size={14} /> Export .xlsx
                  </button>
                </div>

                {/* SLA bar chart */}
                <div className="chart-container">
                  <div className="chart-title">SLA % by Day & Project</div>
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={slaChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                      <XAxis dataKey="day" tick={{ fontSize: 11, fontFamily: "IBM Plex Mono" }} />
                      <YAxis domain={[0, 100]} tick={{ fontSize: 11, fontFamily: "IBM Plex Mono" }} />
                      <Tooltip contentStyle={{ fontFamily: "IBM Plex Mono", fontSize: 12 }} formatter={(v) => `${v.toFixed(1)}%`} />
                      <Legend wrapperStyle={{ fontFamily: "IBM Plex Mono", fontSize: 11 }} />
                      <Bar dataKey="english" name="English SLA%" fill="#0033CC" />
                      <Bar dataKey="language" name="Language SLA%" fill="#FF6600" />
                      <Bar dataKey="combined" name="Combined SLA%" fill="#00C853" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* SLA Table */}
                <div className="table-wrapper" data-testid="sla-table">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Day</th>
                        <th className="num">Eng Req</th>
                        <th className="num">Eng Met</th>
                        <th className="num">Eng SLA</th>
                        <th className="num">Lang Req</th>
                        <th className="num">Lang Met</th>
                        <th className="num">Lang SLA</th>
                        <th className="num">Total Req</th>
                        <th className="num">Total Met</th>
                        <th className="num">Total SLA</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.sla.daily.map((row, i) => (
                        <tr key={i}>
                          <td style={{ fontWeight: 600 }}>{row.day}</td>
                          <td className="num">{row.english_required}</td>
                          <td className="num">{row.english_met}</td>
                          <td className="num"><span className={`sla-badge ${getSLAClass(row.english_sla)}`}>{row.english_sla}%</span></td>
                          <td className="num">{row.language_required}</td>
                          <td className="num">{row.language_met}</td>
                          <td className="num"><span className={`sla-badge ${getSLAClass(row.language_sla)}`}>{row.language_sla}%</span></td>
                          <td className="num">{row.combined_required}</td>
                          <td className="num">{row.combined_met}</td>
                          <td className="num"><span className={`sla-badge ${getSLAClass(row.combined_sla)}`}>{row.combined_sla}%</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Hourly breakdown */}
                <div style={{ marginTop: 24 }}>
                  <div className="day-selector" data-testid="sla-day-selector">
                    {DAYS.map(d => (
                      <button key={d} className={`day-btn ${selectedDay === d ? "active" : ""}`}
                        onClick={() => setSelectedDay(d)} data-testid={`sla-day-btn-${d.toLowerCase()}`}>
                        {d.substring(0, 3)}</button>
                    ))}
                  </div>
                  <div className="chart-container">
                    <div className="chart-title">Hourly Coverage — {selectedDay}</div>
                    <ResponsiveContainer width="100%" height={320}>
                      <AreaChart data={result.sla.hourly.filter(r => r.day === selectedDay)}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                        <XAxis dataKey="hour" tick={{ fontSize: 10, fontFamily: "IBM Plex Mono" }} />
                        <YAxis tick={{ fontSize: 11, fontFamily: "IBM Plex Mono" }} />
                        <Tooltip contentStyle={{ fontFamily: "IBM Plex Mono", fontSize: 12 }} />
                        <Legend wrapperStyle={{ fontFamily: "IBM Plex Mono", fontSize: 11 }} />
                        <Area type="monotone" dataKey="eng_req" stroke="#0033CC" fill="#DBEAFE" strokeWidth={2} name="English Req" />
                        <Area type="monotone" dataKey="eng_deployed" stroke="#002299" fill="transparent" strokeWidth={1.5} strokeDasharray="6 3" name="English Deployed" />
                        <Area type="monotone" dataKey="lang_req" stroke="#FF6600" fill="#FFF3E0" strokeWidth={2} name="Language Req" />
                        <Area type="monotone" dataKey="lang_deployed" stroke="#CC5200" fill="transparent" strokeWidth={1.5} strokeDasharray="6 3" name="Language Deployed" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            )}

            {/* === COMPARE TAB === */}
            {activeTab === "compare" && (
              <ScenarioComparison />
            )}

            {/* Re-run */}
            <div style={{ padding: "24px 0", display: "flex", justifyContent: "center" }}>
              <button data-testid="rerun-btn" className="btn btn-secondary" onClick={() => { setResult(null); window.scrollTo(0, 0); }}>
                <ArrowsClockwise size={16} /> New Schedule
              </button>
            </div>
          </>
        )}
      </main>
    </div>
  );
}

export default App;
