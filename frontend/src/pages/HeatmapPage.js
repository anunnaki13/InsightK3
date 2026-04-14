import React, { useContext, useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { AppContext } from '../App';
import Layout from '../components/Layout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertTriangle, BarChart3, ClipboardList, Flame, Radar, RefreshCcw, ShieldAlert } from 'lucide-react';
import { toast } from 'sonner';

const heatmapTone = {
  green: 'bg-emerald-100 text-emerald-700',
  yellow: 'bg-amber-100 text-amber-700',
  orange: 'bg-orange-100 text-orange-700',
  red: 'bg-rose-100 text-rose-700',
};

const HeatmapPage = () => {
  const { API } = useContext(AppContext);
  const [areas, setAreas] = useState([]);
  const [kpis, setKpis] = useState(null);
  const [trend, setTrend] = useState([]);
  const [matrix, setMatrix] = useState([]);
  const [topRisks, setTopRisks] = useState([]);
  const [criticalAlerts, setCriticalAlerts] = useState([]);
  const [actionItems, setActionItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const summary = useMemo(() => ({
    redAreas: areas.filter((item) => item.heatmap_color === 'red').length,
    criticalRisks: topRisks.filter((item) => item.risk_rating === 'Critical').length,
    openActions: actionItems.length,
    criticalAlerts: criticalAlerts.length,
  }), [areas, topRisks, actionItems, criticalAlerts]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [areasRes, kpisRes, trendRes, matrixRes, topRisksRes, criticalAlertsRes, actionItemsRes] = await Promise.all([
        axios.get(`${API}/heatmap/areas`),
        axios.get(`${API}/heatmap/unit-kpis`),
        axios.get(`${API}/heatmap/unit-kpis/trend`),
        axios.get(`${API}/heatmap/risk-matrix-data`),
        axios.get(`${API}/heatmap/top-risks`),
        axios.get(`${API}/heatmap/critical-alerts`),
        axios.get(`${API}/heatmap/action-items`),
      ]);
      setAreas(areasRes.data.items || []);
      setKpis(kpisRes.data || null);
      setTrend(trendRes.data.items || []);
      setMatrix(matrixRes.data.cells || []);
      setTopRisks(topRisksRes.data.items || []);
      setCriticalAlerts(criticalAlertsRes.data.items || []);
      setActionItems(actionItemsRes.data.items || []);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal memuat heatmap dashboard');
    } finally {
      setLoading(false);
    }
  };

  const handleRecalculate = async () => {
    try {
      await axios.post(`${API}/heatmap/recalculate`);
      toast.success('Heatmap recalculated');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal recalculate heatmap');
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex h-96 items-center justify-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-[22px] bg-slate-950 text-white shadow-[0_20px_50px_rgba(15,23,42,0.24)]">
            <div className="h-6 w-6 animate-spin rounded-full border-[3px] border-white/40 border-t-white" />
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6" data-testid="heatmap-page">
        <section className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
          <Card className="overflow-hidden rounded-[30px] border-0 bg-[linear-gradient(135deg,#102542_0%,#1b4965_58%,#2c6e91_100%)] text-white shadow-[0_32px_90px_rgba(16,37,66,0.24)]">
            <CardContent className="p-7 md:p-8">
              <p className="text-[11px] font-bold uppercase tracking-[0.28em] text-sky-100/75">Module E</p>
              <h1 className="mt-3 text-4xl font-extrabold leading-tight md:text-5xl">Dashboard konsolidasi risiko unit sekarang mulai terbentuk.</h1>
              <p className="mt-4 max-w-2xl text-sm leading-6 text-sky-50/80 md:text-base">
                Heatmap area, KPI unit, risk matrix, top risks, alerts, dan action items sekarang ditarik dari modul audit, ERM, survey, dan equipment.
              </p>
            </CardContent>
          </Card>

          <Card className="rounded-[30px] border-white/70 bg-white/80 shadow-[0_24px_70px_rgba(45,68,58,0.10)] backdrop-blur-xl">
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <CardTitle className="text-lg">Executive Pulse</CardTitle>
              <Button variant="outline" className="rounded-[16px]" onClick={handleRecalculate}>
                <RefreshCcw className="mr-2 h-4 w-4" />
                Recalculate
              </Button>
            </CardHeader>
            <CardContent className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-[20px] bg-rose-50 px-4 py-3">
                <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-rose-700">Red Areas</p>
                <p className="mt-2 text-3xl font-extrabold text-rose-800">{summary.redAreas}</p>
              </div>
              <div className="rounded-[20px] bg-slate-50 px-4 py-3">
                <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Open Actions</p>
                <p className="mt-2 text-3xl font-extrabold text-slate-950">{summary.openActions}</p>
              </div>
              <div className="rounded-[20px] bg-amber-50 px-4 py-3">
                <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-amber-700">Critical Risks</p>
                <p className="mt-2 text-3xl font-extrabold text-amber-800">{summary.criticalRisks}</p>
              </div>
              <div className="rounded-[20px] bg-sky-50 px-4 py-3">
                <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-sky-700">Critical Alerts</p>
                <p className="mt-2 text-3xl font-extrabold text-sky-800">{summary.criticalAlerts}</p>
              </div>
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-5 xl:grid-cols-[0.95fr_1.05fr]">
          <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-xl">
                <Radar className="h-5 w-5 text-sky-700" />
                Area Heatmap
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {areas.map((area) => (
                <div key={area.area_code} className="rounded-[22px] border border-slate-100 bg-slate-50/80 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className={`rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.16em] ${heatmapTone[area.heatmap_color] || 'bg-slate-100 text-slate-700'}`}>{area.heatmap_color}</span>
                        <span className="rounded-full bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-500">{area.area_code}</span>
                      </div>
                      <h3 className="mt-3 text-lg font-bold text-slate-950">{area.area_name}</h3>
                      <p className="mt-2 text-sm text-slate-600">
                        Risk critical {area.risk_critical_count} • Equipment warning {area.equipment_warning} • Findings overdue {area.findings_overdue}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-3xl font-extrabold text-slate-950">{area.heatmap_score}</p>
                      <p className="text-xs text-slate-500">heatmap score</p>
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <div className="space-y-5">
            <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-xl">
                  <BarChart3 className="h-5 w-5 text-slate-700" />
                  Unit KPIs
                </CardTitle>
              </CardHeader>
              <CardContent className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-[20px] bg-slate-50 px-4 py-3">
                  <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">SMK3 Achievement</p>
                  <p className="mt-2 text-2xl font-extrabold text-slate-950">{kpis?.smk3_achievement_pct}%</p>
                </div>
                <div className="rounded-[20px] bg-slate-50 px-4 py-3">
                  <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">SMK3 Grade</p>
                  <p className="mt-2 text-2xl font-extrabold text-slate-950">{kpis?.smk3_grade}</p>
                </div>
                <div className="rounded-[20px] bg-slate-50 px-4 py-3">
                  <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Equipment Readiness</p>
                  <p className="mt-2 text-2xl font-extrabold text-slate-950">{kpis?.equipment_overall_readiness}%</p>
                </div>
                <div className="rounded-[20px] bg-slate-50 px-4 py-3">
                  <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Latest UW Grade</p>
                  <p className="mt-2 text-2xl font-extrabold text-slate-950">{kpis?.latest_survey_grade}</p>
                </div>
              </CardContent>
            </Card>

            <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-xl">
                  <Flame className="h-5 w-5 text-rose-600" />
                  Top Risks
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {topRisks.map((item) => (
                  <div key={item.id} className="rounded-[20px] bg-slate-50 px-4 py-3">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-semibold text-slate-950">{item.title}</p>
                        <p className="text-xs text-slate-500">{item.area_code} • {item.risk_rating}</p>
                      </div>
                      <p className="text-lg font-extrabold text-slate-950">{item.risk_score}</p>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </section>

        <section className="grid gap-5 xl:grid-cols-[1.02fr_0.98fr]">
          <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-xl">
                <ShieldAlert className="h-5 w-5 text-amber-600" />
                Critical Alerts
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {criticalAlerts.length === 0 ? (
                <div className="rounded-[20px] bg-slate-50 p-6 text-sm text-slate-500">Tidak ada critical alert.</div>
              ) : (
                criticalAlerts.slice(0, 12).map((item) => (
                  <div key={`${item.source}-${item.id}`} className="rounded-[20px] bg-slate-50 px-4 py-3">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-semibold text-slate-950">{item.title}</p>
                        <p className="mt-1 text-sm text-slate-600">{item.message}</p>
                      </div>
                      <span className={`rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.16em] ${item.severity === 'critical' ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-700'}`}>{item.severity}</span>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-xl">
                <ClipboardList className="h-5 w-5 text-slate-700" />
                Action Items
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {actionItems.slice(0, 14).map((item) => (
                <div key={`${item.source}-${item.id}`} className="rounded-[20px] bg-slate-50 px-4 py-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-semibold text-slate-950">{item.title}</p>
                      <p className="text-xs text-slate-500">{item.source} • {item.area_code || 'unit-wide'} • {item.status}</p>
                    </div>
                    <span className="rounded-full bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-600">{item.priority}</span>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-5 xl:grid-cols-[0.95fr_1.05fr]">
          <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
            <CardHeader>
              <CardTitle className="text-xl">Risk Matrix</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {matrix.map((cell) => (
                <div key={`${cell.likelihood}-${cell.impact}`} className="rounded-[18px] bg-slate-50 px-4 py-3 text-sm text-slate-700">
                  Likelihood {cell.likelihood} x Impact {cell.impact}: <span className="font-semibold">{cell.count}</span> item
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
            <CardHeader>
              <CardTitle className="text-xl">KPI Trend</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {trend.map((item) => (
                <div key={item.period} className="rounded-[20px] bg-slate-50 px-4 py-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-semibold text-slate-950">{item.period}</p>
                      <p className="text-xs text-slate-500">SMK3 {item.smk3_achievement_pct}% • Equipment {item.equipment_overall_readiness}%</p>
                    </div>
                    <p className="text-lg font-extrabold text-slate-950">{item.findings_open_total}</p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </section>
      </div>
    </Layout>
  );
};

export default HeatmapPage;
