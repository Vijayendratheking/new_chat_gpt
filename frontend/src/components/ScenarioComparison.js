import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
} from "recharts";
import {
  Plus, Trash, ArrowsClockwise, Scales, CaretDown, CaretUp, CheckSquare, Square,
} from "@phosphor-icons/react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const DAYS_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

const SCENARIO_COLORS = ["#0033CC", "#FF6600", "#00C853", "#9C27B0", "#FF1744"];

const DEFAULT_PROFILES = [
  { off_days: ["Saturday", "Sunday"], count: 108 },
  { off_days: ["Sunday", "Monday"], count: 26 },
  { off_days: ["Monday", "Tuesday"], count: 26 },
  { off_days: ["Tuesday", "Wednesday"], count: 26 },
  { off_days: ["Wednesday", "Thursday"], count: 26 },
];

const OFF_DAY_OPTIONS = [
  ["Saturday", "Sunday"],
  ["Sunday", "Monday"],
  ["Monday", "Tuesday"],
  ["Tuesday", "Wednesday"],
  ["Wednesday", "Thursday"],
  ["Thursday", "Friday"],
  ["Friday", "Saturday"],
];

export default function ScenarioComparison() {
  const [savedScenarios, setSavedScenarios] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showBuilder, setShowBuilder] = useState(false);

  // Scenario builder state
  const [scenarioName, setScenarioName] = useState("");
  const [profiles, setProfiles] = useState(JSON.parse(JSON.stringify(DEFAULT_PROFILES)));
  const [building, setBuilding] = useState(false);

  const totalAgents = profiles.reduce((s, p) => s + p.count, 0);

  const fetchScenarios = useCallback(async () => {
    try {
      const resp = await axios.get(`${API}/schedules`);
      setSavedScenarios(resp.data);
    } catch (e) {
      console.error(e);
    }
  }, []);

  useEffect(() => { fetchScenarios(); }, [fetchScenarios]);

  const toggleSelect = (id) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : prev.length < 5 ? [...prev, id] : prev
    );
  };

  const runComparison = async () => {
    if (selectedIds.length < 2) return;
    setLoading(true);
    try {
      const resp = await axios.post(`${API}/compare`, { ids: selectedIds });
      setComparison(resp.data.scenarios);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const deleteScenario = async (id) => {
    try {
      await axios.delete(`${API}/schedule/${id}`);
      setSavedScenarios(prev => prev.filter(s => s.id !== id));
      setSelectedIds(prev => prev.filter(x => x !== id));
      if (comparison) {
        setComparison(prev => prev?.filter(s => s.id !== id));
      }
    } catch (e) {
      console.error(e);
    }
  };

  const updateProfileCount = (idx, val) => {
    setProfiles(prev => {
      const next = [...prev];
      next[idx] = { ...next[idx], count: Math.max(0, val) };
      return next;
    });
  };

  const addProfile = (offDays) => {
    if (!profiles.find(p => p.off_days.join(",") === offDays.join(","))) {
      setProfiles(prev => [...prev, { off_days: offDays, count: 0 }]);
    }
  };

  const removeProfile = (idx) => {
    setProfiles(prev => prev.filter((_, i) => i !== idx));
  };

  const runScenario = async () => {
    if (!scenarioName.trim()) return;
    setBuilding(true);
    try {
      const formData = new FormData();
      formData.append("name", scenarioName.trim());
      formData.append("off_day_profiles", JSON.stringify(profiles));
      const resp = await axios.post(`${API}/run-scenario`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      await fetchScenarios();
      setShowBuilder(false);
      setScenarioName("");
      setSelectedIds(prev => [...prev, resp.data.id].slice(0, 5));
    } catch (e) {
      console.error(e);
    } finally {
      setBuilding(false);
    }
  };

  // Comparison chart data
  const slaCompareData = comparison ? DAYS_SHORT.map((d, i) => {
    const row = { day: d };
    comparison.forEach((sc, si) => {
      const dayData = sc.sla?.daily?.[i];
      if (dayData) {
        row[`eng_${si}`] = dayData.english_sla;
        row[`lang_${si}`] = dayData.language_sla;
        row[`combined_${si}`] = dayData.combined_sla;
      }
    });
    return row;
  }) : [];

  const radarData = comparison ? [
    { metric: "Eng SLA" },
    { metric: "Lang SLA" },
    { metric: "Combined SLA" },
    { metric: "Agents Used" },
    { metric: "Eng Coverage" },
    { metric: "Lang Coverage" },
  ].map(item => {
    comparison.forEach((sc, si) => {
      const avg = sc.sla?.daily?.reduce((s, r) => s + r.combined_sla, 0) / 7 || 0;
      const avgEng = sc.sla?.daily?.reduce((s, r) => s + r.english_sla, 0) / 7 || 0;
      const avgLang = sc.sla?.daily?.reduce((s, r) => s + r.language_sla, 0) / 7 || 0;
      const agents = sc.summary?.total_agents || 0;
      const engShifts = sc.summary?.english_shifts || 0;
      const langShifts = sc.summary?.language_shifts || 0;
      const total = engShifts + langShifts;
      if (item.metric === "Eng SLA") item[`s${si}`] = avgEng;
      else if (item.metric === "Lang SLA") item[`s${si}`] = avgLang;
      else if (item.metric === "Combined SLA") item[`s${si}`] = avg;
      else if (item.metric === "Agents Used") item[`s${si}`] = (agents / 250) * 100;
      else if (item.metric === "Eng Coverage") item[`s${si}`] = total > 0 ? (engShifts / total) * 100 : 0;
      else if (item.metric === "Lang Coverage") item[`s${si}`] = total > 0 ? (langShifts / total) * 100 : 0;
    });
    return item;
  }) : [];

  return (
    <div data-testid="scenario-comparison">
      {/* Scenario Builder */}
      <div className="export-bar">
        <span className="section-title">Scenario Comparison</span>
        <button
          data-testid="toggle-builder-btn"
          className="btn btn-primary btn-sm"
          onClick={() => setShowBuilder(!showBuilder)}
        >
          {showBuilder ? <CaretUp size={14} /> : <Plus size={14} />}
          {showBuilder ? "Close Builder" : "New Scenario"}
        </button>
      </div>

      {showBuilder && (
        <div className="scenario-builder" data-testid="scenario-builder">
          <div className="builder-header">
            <div className="file-input-group" style={{ flex: 1, maxWidth: 360 }}>
              <label htmlFor="scenario-name">Scenario Name</label>
              <input
                data-testid="scenario-name-input"
                id="scenario-name"
                className="search-input"
                style={{ width: "100%" }}
                placeholder='e.g. "Weekend Heavy" or "Balanced Split"'
                value={scenarioName}
                onChange={e => setScenarioName(e.target.value)}
              />
            </div>
            <div className="agent-counter">
              <span className="card-label">Total Agents</span>
              <span className={`card-value ${totalAgents !== 212 ? "text-warn" : ""}`} data-testid="agent-counter">{totalAgents}</span>
              {totalAgents !== 212 && <span className="text-warn-hint">(default: 212)</span>}
            </div>
          </div>

          <div className="profiles-grid" data-testid="profiles-grid">
            {profiles.map((p, idx) => (
              <div key={idx} className="profile-card" data-testid={`profile-card-${idx}`}>
                <div className="profile-label">{p.off_days.join(" / ")}</div>
                <div className="profile-controls">
                  <button className="btn-icon" onClick={() => updateProfileCount(idx, p.count - 1)}>-</button>
                  <input
                    data-testid={`profile-count-${idx}`}
                    type="number"
                    className="profile-input"
                    value={p.count}
                    onChange={e => updateProfileCount(idx, parseInt(e.target.value) || 0)}
                    min={0}
                  />
                  <button className="btn-icon" onClick={() => updateProfileCount(idx, p.count + 1)}>+</button>
                  <button className="btn-icon btn-icon-danger" onClick={() => removeProfile(idx)}>
                    <Trash size={12} />
                  </button>
                </div>
              </div>
            ))}

            {/* Add profile dropdown */}
            {OFF_DAY_OPTIONS.filter(o => !profiles.find(p => p.off_days.join(",") === o.join(","))).length > 0 && (
              <div className="profile-card profile-add">
                <select
                  data-testid="add-profile-select"
                  className="profile-select"
                  defaultValue=""
                  onChange={e => { if (e.target.value) { addProfile(e.target.value.split(",")); e.target.value = ""; } }}
                >
                  <option value="">+ Add off-day profile...</option>
                  {OFF_DAY_OPTIONS
                    .filter(o => !profiles.find(p => p.off_days.join(",") === o.join(",")))
                    .map(o => <option key={o.join(",")} value={o.join(",")}>{o.join(" / ")}</option>)
                  }
                </select>
              </div>
            )}
          </div>

          <div style={{ display: "flex", gap: 8, alignItems: "center", marginTop: 16 }}>
            <button
              data-testid="run-scenario-btn"
              className="btn btn-primary"
              onClick={runScenario}
              disabled={building || !scenarioName.trim() || totalAgents === 0}
            >
              {building ? <ArrowsClockwise size={14} /> : <Scales size={14} />}
              {building ? "Computing..." : "Run Scenario"}
            </button>
            <button className="btn btn-secondary btn-sm" onClick={() => setProfiles(JSON.parse(JSON.stringify(DEFAULT_PROFILES)))}>
              Reset to Default
            </button>
          </div>
        </div>
      )}

      {/* Saved Scenarios List */}
      <div style={{ marginTop: 24 }}>
        <div className="selector-label" style={{ marginBottom: 8 }}>
          Saved Scenarios ({savedScenarios.length}) — Select 2-5 to compare
        </div>

        {savedScenarios.length === 0 && (
          <div className="empty-state" data-testid="empty-scenarios">
            No scenarios yet. Run a schedule or create a new scenario above.
          </div>
        )}

        <div className="scenario-list" data-testid="scenario-list">
          {savedScenarios.map((sc, i) => {
            const isSelected = selectedIds.includes(sc.id);
            const avgSla = sc.sla?.daily ? (sc.sla.daily.reduce((s, r) => s + r.combined_sla, 0) / 7).toFixed(1) : "—";
            return (
              <div
                key={sc.id}
                className={`scenario-item ${isSelected ? "selected" : ""}`}
                data-testid={`scenario-item-${i}`}
                onClick={() => toggleSelect(sc.id)}
              >
                <div className="scenario-check">
                  {isSelected ? <CheckSquare size={18} weight="fill" color={SCENARIO_COLORS[selectedIds.indexOf(sc.id)] || "#0033CC"} />
                    : <Square size={18} color="#94A3B8" />}
                </div>
                <div className="scenario-info">
                  <div className="scenario-name">{sc.name || "Unnamed Schedule"}</div>
                  <div className="scenario-meta">
                    {sc.summary?.total_agents || "?"} agents | {sc.summary?.english_shifts || 0} eng + {sc.summary?.language_shifts || 0} lang shifts
                  </div>
                </div>
                <div className="scenario-sla">
                  <span className="font-mono">{avgSla}%</span>
                  <span className="scenario-meta">Avg SLA</span>
                </div>
                <button
                  className="btn-icon btn-icon-danger"
                  data-testid={`delete-scenario-${i}`}
                  onClick={e => { e.stopPropagation(); deleteScenario(sc.id); }}
                >
                  <Trash size={14} />
                </button>
              </div>
            );
          })}
        </div>

        {savedScenarios.length >= 2 && (
          <div style={{ marginTop: 12 }}>
            <button
              data-testid="compare-btn"
              className="btn btn-primary"
              onClick={runComparison}
              disabled={selectedIds.length < 2 || loading}
            >
              <Scales size={16} />
              {loading ? "Loading..." : `Compare ${selectedIds.length} Scenarios`}
            </button>
          </div>
        )}
      </div>

      {/* Comparison Results */}
      {comparison && comparison.length >= 2 && (
        <div className="comparison-results" data-testid="comparison-results">
          <div className="section-title" style={{ marginBottom: 16, marginTop: 32 }}>
            Side-by-Side Comparison
          </div>

          {/* Summary cards row */}
          <div className="compare-cards" data-testid="compare-summary-cards">
            {comparison.map((sc, si) => (
              <div key={sc.id} className="compare-card" style={{ borderTop: `3px solid ${SCENARIO_COLORS[si]}` }}>
                <div className="compare-card-name" style={{ color: SCENARIO_COLORS[si] }}>{sc.name || "Unnamed"}</div>
                <div className="compare-stat">
                  <span className="card-label">Agents</span>
                  <span className="card-value" style={{ fontSize: 22 }}>{sc.summary?.total_agents}</span>
                </div>
                <div className="compare-stat">
                  <span className="card-label">Eng Shifts</span>
                  <span className="card-value" style={{ fontSize: 22 }}>{sc.summary?.english_shifts}</span>
                </div>
                <div className="compare-stat">
                  <span className="card-label">Lang Shifts</span>
                  <span className="card-value" style={{ fontSize: 22 }}>{sc.summary?.language_shifts}</span>
                </div>
                <div className="compare-stat">
                  <span className="card-label">Avg SLA</span>
                  <span className="card-value" style={{ fontSize: 22 }}>
                    {(sc.sla?.daily?.reduce((s, r) => s + r.combined_sla, 0) / 7 || 0).toFixed(1)}%
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Combined SLA comparison chart */}
          <div className="chart-container" style={{ marginTop: 16 }}>
            <div className="chart-title">Combined SLA% by Day</div>
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={slaCompareData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="day" tick={{ fontSize: 11, fontFamily: "IBM Plex Mono" }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11, fontFamily: "IBM Plex Mono" }} />
                <Tooltip contentStyle={{ fontFamily: "IBM Plex Mono", fontSize: 12 }} formatter={(v) => `${v?.toFixed(1)}%`} />
                <Legend wrapperStyle={{ fontFamily: "IBM Plex Mono", fontSize: 11 }} />
                {comparison.map((sc, si) => (
                  <Bar key={si} dataKey={`combined_${si}`} name={sc.name || `Scenario ${si + 1}`} fill={SCENARIO_COLORS[si]} />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Radar chart */}
          <div className="chart-container" style={{ marginTop: 16 }}>
            <div className="chart-title">Performance Radar</div>
            <ResponsiveContainer width="100%" height={360}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#E2E8F0" />
                <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11, fontFamily: "IBM Plex Mono" }} />
                <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 9, fontFamily: "IBM Plex Mono" }} />
                {comparison.map((sc, si) => (
                  <Radar key={si} name={sc.name || `Scenario ${si + 1}`} dataKey={`s${si}`}
                    stroke={SCENARIO_COLORS[si]} fill={SCENARIO_COLORS[si]} fillOpacity={0.15} strokeWidth={2} />
                ))}
                <Legend wrapperStyle={{ fontFamily: "IBM Plex Mono", fontSize: 11 }} />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          {/* Detailed SLA table */}
          <div className="table-wrapper" style={{ marginTop: 16 }} data-testid="compare-sla-table">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Day</th>
                  {comparison.map((sc, si) => (
                    <th key={si} className="num" colSpan={3} style={{ borderBottom: `2px solid ${SCENARIO_COLORS[si]}` }}>
                      {sc.name || `Scenario ${si + 1}`}
                    </th>
                  ))}
                </tr>
                <tr>
                  <th></th>
                  {comparison.map((_, si) => (
                    <React.Fragment key={si}>
                      <th className="num" style={{ fontSize: 10 }}>Eng%</th>
                      <th className="num" style={{ fontSize: 10 }}>Lang%</th>
                      <th className="num" style={{ fontSize: 10 }}>Comb%</th>
                    </React.Fragment>
                  ))}
                </tr>
              </thead>
              <tbody>
                {DAYS.map((day, di) => (
                  <tr key={day}>
                    <td style={{ fontWeight: 600 }}>{day}</td>
                    {comparison.map((sc, si) => {
                      const d = sc.sla?.daily?.[di] || {};
                      return (
                        <React.Fragment key={si}>
                          <td className="num">{d.english_sla?.toFixed(1) || "—"}%</td>
                          <td className="num">{d.language_sla?.toFixed(1) || "—"}%</td>
                          <td className="num" style={{ fontWeight: 600 }}>{d.combined_sla?.toFixed(1) || "—"}%</td>
                        </React.Fragment>
                      );
                    })}
                  </tr>
                ))}
                {/* Averages row */}
                <tr className="total-row">
                  <td style={{ fontWeight: 700 }}>Average</td>
                  {comparison.map((sc, si) => {
                    const daily = sc.sla?.daily || [];
                    const avgE = daily.length ? (daily.reduce((s, r) => s + r.english_sla, 0) / daily.length).toFixed(1) : "—";
                    const avgL = daily.length ? (daily.reduce((s, r) => s + r.language_sla, 0) / daily.length).toFixed(1) : "—";
                    const avgC = daily.length ? (daily.reduce((s, r) => s + r.combined_sla, 0) / daily.length).toFixed(1) : "—";
                    return (
                      <React.Fragment key={si}>
                        <td className="num">{avgE}%</td>
                        <td className="num">{avgL}%</td>
                        <td className="num" style={{ fontWeight: 700 }}>{avgC}%</td>
                      </React.Fragment>
                    );
                  })}
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
