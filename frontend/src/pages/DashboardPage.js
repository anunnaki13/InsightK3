import React, { useState, useEffect, useContext } from 'react';
import { AppContext } from '../App';
import { Link } from 'react-router-dom';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import {
  AlertTriangle,
  Archive,
  ArrowUpRight,
  BarChart3,
  BadgeCheck,
  CheckCircle2,
  Download,
  FileCheck,
  Layers3,
  ShieldAlert,
  TrendingUp,
  XCircle,
} from 'lucide-react';
import { toast } from 'sonner';

const surveyorMetricCards = (stats, evidenceProgress, documentedClauses) => [
  {
    key: 'total',
    title: 'Total Klausul',
    value: stats?.total_clauses || 0,
    note: 'Klausul audit yang harus dipenuhi',
    icon: FileCheck,
    accent: 'text-slate-900',
    tone: 'from-white to-slate-50',
  },
  {
    key: 'documented',
    title: 'Evidence Terkumpul',
    value: documentedClauses,
    note: `${evidenceProgress.toFixed(1)}% klausul sudah memiliki evidence`,
    icon: Layers3,
    accent: 'text-sky-700',
    tone: 'from-sky-50 to-white',
  },
  {
    key: 'progress',
    title: 'Progres Evidence',
    value: `${evidenceProgress.toFixed(1)}%`,
    note: 'Kemajuan pengumpulan evidence per seluruh kriteria',
    icon: BadgeCheck,
    accent: 'text-emerald-700',
    tone: 'from-emerald-50 to-white',
  },
  {
    key: 'files',
    title: 'Total File Evidence',
    value: stats?.total_evidence_files || 0,
    note: 'Jumlah seluruh file evidence terinput',
    icon: Archive,
    accent: 'text-indigo-700',
    tone: 'from-indigo-50 to-white',
  },
];

const standardMetricCards = (stats, completionPercentage) => [
  {
    key: 'total',
    title: 'Total Klausul',
    value: stats?.total_clauses || 0,
    note: 'Klausul audit yang harus dipenuhi',
    icon: FileCheck,
    accent: 'text-slate-900',
    tone: 'from-white to-slate-50',
  },
  {
    key: 'audited',
    title: 'Teraudit',
    value: stats?.audited_clauses || 0,
    note: `${completionPercentage.toFixed(1)}% evidence telah diperiksa`,
    icon: BarChart3,
    accent: 'text-sky-700',
    tone: 'from-sky-50 to-white',
  },
  {
    key: 'average',
    title: 'Skor AI',
    value: stats?.average_score?.toFixed(1) || '0.0',
    note: 'Referensi analisis evidence',
    icon: TrendingUp,
    accent: 'text-amber-700',
    tone: 'from-amber-50 to-white',
  },
  {
    key: 'achievement',
    title: 'Pencapaian Audit',
    value: `${stats?.achievement_percentage?.toFixed(1) || 0}%`,
    note: `${stats?.confirm_count || 0} klausul confirm oleh auditor`,
    icon: CheckCircle2,
    accent: 'text-emerald-700',
    tone: 'from-emerald-50 to-white',
  },
];

const DashboardPage = () => {
  const { API, user } = useContext(AppContext);
  const isSurveyor = user?.role === 'surveyor';
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notifications, setNotifications] = useState([]);
  const [criteriaClauseCache, setCriteriaClauseCache] = useState({});
  const [criteriaClauseLoading, setCriteriaClauseLoading] = useState({});
  const [criteriaMissingOpen, setCriteriaMissingOpen] = useState({});
  const [auditorFindingOpen, setAuditorFindingOpen] = useState({ major: false, minor: false });
  const [auditorFindingLoading, setAuditorFindingLoading] = useState(false);
  const [auditorFindingItems, setAuditorFindingItems] = useState({ major: [], minor: [] });

  useEffect(() => {
    fetchDashboard();
  }, [API]);

  useEffect(() => {
    if (!isSurveyor) {
      fetchNotifications();
    }
  }, [API, isSurveyor]);

  const fetchDashboard = async () => {
    try {
      const response = await axios.get(`${API}/audit/dashboard`);
      setStats(response.data);
    } catch (error) {
      toast.error('Gagal memuat data dashboard');
    } finally {
      setLoading(false);
    }
  };

  const fetchNotifications = async () => {
    try {
      const response = await axios.get(`${API}/recommendations/notifications`);
      setNotifications(response.data.notifications || []);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  const downloadEvidenceArchive = async (url, fallbackFilename) => {
    try {
      toast.info('Menyiapkan file evidence...');
      const response = await axios.get(url, { responseType: 'blob' });
      const disposition = response.headers['content-disposition'] || '';
      const filenameMatch = disposition.match(/filename="?([^"]+)"?/i);
      const filename = filenameMatch?.[1] || fallbackFilename;
      const blobUrl = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(blobUrl);
      toast.success('Download evidence dimulai');
    } catch (error) {
      console.error('Error downloading evidence:', error);
      toast.error(error.response?.data?.detail || 'Gagal mengunduh evidence');
    }
  };

  const handleDownloadAllEvidence = () => {
    toast.info('Download massal semua evidence dimatikan agar web tetap stabil. Gunakan export per kriteria.');
  };

  const handleDownloadCriteriaEvidence = (criteriaId, criteriaName) => {
    const safeCriteriaName = String(criteriaName || 'Kriteria').replace(/[\\/:*?"<>|]/g, '-');
    downloadEvidenceArchive(
      `${API}/audit/download-criteria-evidence/${criteriaId}`,
      `Evidence_${safeCriteriaName}.zip`
    );
  };

  const loadCriteriaClauseItems = async (criteriaId) => {
    if (!criteriaId || criteriaClauseCache[criteriaId] || criteriaClauseLoading[criteriaId]) {
      return;
    }

    setCriteriaClauseLoading((prev) => ({ ...prev, [criteriaId]: true }));
    try {
      const clausesResponse = await axios.get(`${API}/clauses?criteria_id=${criteriaId}`);
      const clauseDocs = await Promise.all(
        clausesResponse.data.map(async (clause) => {
          const docsResponse = await axios.get(`${API}/clauses/${clause.id}/documents`);
          return {
            ...clause,
            document_count: docsResponse.data.length,
          };
        })
      );

      setCriteriaClauseCache((prev) => ({ ...prev, [criteriaId]: clauseDocs }));
    } catch (error) {
      console.error('Error loading criteria clauses:', error);
      toast.error('Gagal memuat klausul kriteria');
    } finally {
      setCriteriaClauseLoading((prev) => ({ ...prev, [criteriaId]: false }));
    }
  };

  const toggleCriteriaMissing = (criteriaId) => {
    const nextOpen = !criteriaMissingOpen[criteriaId];
    setCriteriaMissingOpen((prev) => ({ ...prev, [criteriaId]: nextOpen }));
    if (nextOpen) {
      loadCriteriaClauseItems(criteriaId);
    }
  };

  const loadAuditorFindingItems = async () => {
    if (auditorFindingLoading) {
      return;
    }

    if ((auditorFindingItems.major.length > 0 || auditorFindingItems.minor.length > 0) && auditorFindingItems.loaded) {
      return;
    }

    setAuditorFindingLoading(true);
    try {
      const criteriaResponse = await axios.get(`${API}/criteria`);
      const findings = { major: [], minor: [] };

      for (const criteria of criteriaResponse.data) {
        const clausesResponse = await axios.get(`${API}/clauses?criteria_id=${criteria.id}`);
        const clauseFindings = await Promise.all(
          clausesResponse.data.map(async (clause) => {
            try {
              const resultResponse = await axios.get(`${API}/audit/results/${clause.id}`);
              const result = resultResponse.data;
              if (!result?.auditor_status || !['non-confirm-major', 'non-confirm-minor'].includes(result.auditor_status)) {
                return null;
              }

              return {
                id: result.id || clause.id,
                clause_id: clause.id,
                clause_number: clause.clause_number,
                clause_title: clause.title,
                criteria_id: criteria.id,
                criteria_name: criteria.name,
                auditor_status: result.auditor_status,
              };
            } catch (error) {
              return null;
            }
          })
        );

        clauseFindings.filter(Boolean).forEach((item) => {
          if (item.auditor_status === 'non-confirm-major') {
            findings.major.push(item);
          } else if (item.auditor_status === 'non-confirm-minor') {
            findings.minor.push(item);
          }
        });
      }

      setAuditorFindingItems({ ...findings, loaded: true });
    } catch (error) {
      console.error('Error loading auditor findings:', error);
      toast.error('Gagal memuat temuan auditor');
    } finally {
      setAuditorFindingLoading(false);
    }
  };

  const toggleAuditorFinding = async (type) => {
    const nextOpen = !auditorFindingOpen[type];
    setAuditorFindingOpen((prev) => ({ ...prev, [type]: nextOpen }));
    if (nextOpen && auditorFindingItems[type].length === 0) {
      await loadAuditorFindingItems();
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex h-96 items-center justify-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-[22px] bg-emerald-900 text-white shadow-[0_20px_50px_rgba(15,95,83,0.24)]">
            <div className="h-6 w-6 animate-spin rounded-full border-[3px] border-white/40 border-t-white" />
          </div>
        </div>
      </Layout>
    );
  }

  if (isSurveyor) {
    const documentedClauses = stats?.criteria_scores?.reduce((sum, criteria) => sum + (criteria.documented_clauses || 0), 0) || 0;
    const totalEvidenceFiles = stats?.total_evidence_files || 0;
    const evidenceProgress = stats ? (documentedClauses / (stats.total_clauses || 1)) * 100 : 0;
    const cards = surveyorMetricCards(stats, evidenceProgress, documentedClauses);

    return (
      <Layout>
        <div className="space-y-6" data-testid="dashboard-page">
          <section className="grid gap-5 xl:grid-cols-[1.5fr_0.9fr]">
            <Card className="overflow-hidden rounded-[30px] border-0 bg-[linear-gradient(135deg,#123c36_0%,#1f5c53_58%,#2f7569_100%)] text-white shadow-[0_32px_90px_rgba(18,60,54,0.28)]">
              <CardContent className="p-7 md:p-8">
                <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
                  <div className="max-w-2xl">
                    <p className="text-[11px] font-bold uppercase tracking-[0.28em] text-emerald-100/75">Audit Overview</p>
                    <h1 className="mt-3 text-4xl font-extrabold leading-tight md:text-5xl">Ringkasan pengumpulan evidence SMK3.</h1>
                    <p className="mt-4 max-w-xl text-sm leading-6 text-emerald-50/80 md:text-base">
                      Pantau total klausul dan progres pengumpulan evidence dalam satu workspace operasional yang terpusat.
                    </p>
                    <div className="mt-6 flex flex-wrap items-center gap-3 text-xs text-emerald-50/75">
                      <span className="rounded-full border border-white/15 bg-white/10 px-3 py-1.5">PP 50/2012</span>
                      <span className="rounded-full border border-white/15 bg-white/10 px-3 py-1.5">Permenaker 26/2014</span>
                      <span className="rounded-full border border-white/15 bg-white/10 px-3 py-1.5">Evidence-driven review</span>
                    </div>
                  </div>

                  <div className="grid w-full gap-3 sm:grid-cols-3 lg:w-[360px] lg:grid-cols-1">
                    <div className="rounded-[24px] border border-white/12 bg-white/10 p-4 backdrop-blur-sm">
                      <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-emerald-100/70">Completion</p>
                      <p className="mt-2 text-3xl font-extrabold">{evidenceProgress.toFixed(1)}%</p>
                      <p className="mt-1 text-xs text-emerald-50/70">Progres pengumpulan evidence</p>
                    </div>
                    <Button
                      onClick={handleDownloadAllEvidence}
                      className="h-auto min-w-0 justify-between gap-3 whitespace-normal rounded-[24px] bg-white px-4 py-4 text-left text-slate-900 hover:bg-emerald-50"
                      data-testid="download-all-evidence-button"
                    >
                      <div className="min-w-0 flex-1">
                        <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-emerald-700">Evidence Export</p>
                        <p className="mt-1 break-words text-sm font-bold leading-snug sm:text-base">Gunakan export per kriteria</p>
                      </div>
                      <Archive className="h-5 w-5 shrink-0 text-emerald-700" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="rounded-[30px] border-white/70 bg-white/78 shadow-[0_24px_70px_rgba(45,68,58,0.10)] backdrop-blur-xl">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <ShieldAlert className="h-5 w-5 text-amber-600" />
                  Evidence Window
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-5">
                <div>
                  <div className="mb-2 flex items-center justify-between text-sm font-medium text-slate-700">
                    <span>Progress Evidence</span>
                    <span>{evidenceProgress.toFixed(1)}%</span>
                  </div>
                  <Progress value={evidenceProgress} className="h-2.5 rounded-full bg-sky-100" indicatorClassName="bg-sky-500" />
                </div>

                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
                  <div className="rounded-[22px] bg-sky-50 p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.2em] text-sky-700">Evidence</p>
                    <p className="mt-2 text-2xl font-extrabold text-sky-800">{documentedClauses}</p>
                  </div>
                  <div className="rounded-[22px] bg-indigo-50 p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-700">Total File</p>
                    <p className="mt-2 text-2xl font-extrabold text-indigo-800">{totalEvidenceFiles}</p>
                  </div>
                  <div className="rounded-[22px] bg-emerald-50 p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700">Total Klausul</p>
                    <p className="mt-2 text-2xl font-extrabold text-emerald-800">{stats?.total_clauses || 0}</p>
                  </div>
                  <div className="rounded-[22px] bg-amber-50 p-4 sm:col-span-2 xl:col-span-1">
                    <p className="text-xs font-semibold uppercase tracking-[0.2em] text-amber-700">Belum Ada Evidence</p>
                    <p className="mt-2 text-2xl font-extrabold text-amber-800">{Math.max((stats?.total_clauses || 0) - documentedClauses, 0)}</p>
                  </div>
                </div>

                <div className="rounded-[24px] border border-dashed border-slate-200 bg-slate-50/80 p-4 text-sm text-slate-600">
                  Prioritas saat ini adalah mempercepat klausul yang belum memiliki evidence.
                </div>
              </CardContent>
            </Card>
          </section>

          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {cards.map((card) => {
              const Icon = card.icon;
              return (
                <Card key={card.key} className={`rounded-[28px] border-white/70 bg-gradient-to-br ${card.tone} shadow-[0_18px_50px_rgba(39,60,52,0.08)]`}>
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">{card.title}</p>
                        <p className={`mt-3 text-4xl font-extrabold ${card.accent}`}>{card.value}</p>
                        <p className="mt-2 text-sm text-slate-600">{card.note}</p>
                      </div>
                      <div className="flex h-12 w-12 items-center justify-center rounded-[18px] bg-white/85 text-slate-700 shadow-sm">
                        <Icon className="h-5 w-5" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </section>

          <Card className="rounded-[30px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]" data-testid="criteria-scores-card">
            <CardHeader className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <CardTitle className="text-xl">Performa Per Kriteria Audit</CardTitle>
                <p className="mt-1 text-sm text-slate-600">Kriteria diurutkan sebagai panel progres pengumpulan evidence.</p>
              </div>
              <div className="rounded-full bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-500">
                {stats?.criteria_scores?.length || 0} kriteria
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {stats?.criteria_scores?.map((criteria) => (
                  <div key={criteria.id} className="rounded-[24px] border border-slate-100 bg-slate-50/70 p-4 md:p-5" data-testid="criteria-score-item">
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="text-lg font-bold text-slate-900">{criteria.name}</h3>
                          {criteria.audited_clauses > 0 && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDownloadCriteriaEvidence(criteria.id, criteria.name)}
                              className="h-8 rounded-full px-3 text-xs text-sky-700 hover:bg-sky-50 hover:text-sky-800"
                              data-testid="download-criteria-evidence-button"
                            >
                              <Download className="mr-1.5 h-3.5 w-3.5" />
                              Export evidence
                            </Button>
                          )}
                        </div>
                        <div className="mt-3 flex flex-wrap items-center gap-4 text-sm text-slate-600">
                          <span>{criteria.documented_clauses || 0}/{criteria.total_clauses} klausul sudah ada evidence</span>
                          <span>{criteria.evidence_files || 0} file evidence</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-6">
                        <div>
                          <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Evidence Progress</p>
                          <p className="mt-1 text-3xl font-extrabold text-sky-700">
                            {criteria.documentation_percentage?.toFixed(1) || '0.0'}%
                          </p>
                        </div>
                        <div className="hidden h-12 w-px bg-slate-200 md:block" />
                        <div className="text-sm text-slate-600">
                          <p className="font-semibold text-slate-800">{criteria.documented_clauses || 0} evidence clause</p>
                          <p>{criteria.evidence_files || 0} total file</p>
                          <p>{Math.max((criteria.total_clauses || 0) - (criteria.documented_clauses || 0), 0)} klausul kosong</p>
                        </div>
                      </div>
                    </div>

                    <div className="mt-4 space-y-3">
                      <div>
                        <div className="mb-1.5 flex items-center justify-between text-xs font-medium text-slate-500">
                          <span>Progress evidence per kriteria</span>
                          <span>{criteria.documented_clauses || 0}/{criteria.total_clauses}</span>
                        </div>
                        <Progress
                          value={criteria.documentation_percentage || 0}
                          className="h-2.5 rounded-full bg-sky-100"
                          indicatorClassName="bg-sky-500"
                        />
                      </div>
                    </div>

                    <div className="mt-4 rounded-[20px] border border-slate-200 bg-white/85 p-3">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">Klausul Kosong</p>
                          <p className="mt-1 text-xs text-slate-600">Tab kecil untuk klausul yang belum punya evidence.</p>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 rounded-full px-3 text-xs text-slate-600 hover:bg-slate-100"
                          onClick={() => toggleCriteriaMissing(criteria.id)}
                          data-testid="toggle-criteria-missing-button"
                        >
                          {criteriaMissingOpen[criteria.id] ? 'Tutup' : 'Muat daftar'}
                        </Button>
                      </div>

                      {criteriaMissingOpen[criteria.id] && (
                        <div className="mt-3">
                          {criteriaClauseLoading[criteria.id] ? (
                            <p className="text-sm text-slate-500">Memuat klausul...</p>
                          ) : (() => {
                            const clauses = criteriaClauseCache[criteria.id] || [];
                            const missingClauses = clauses.filter((clause) => (clause.document_count || 0) === 0);

                            if (missingClauses.length === 0) {
                              return <p className="text-sm text-slate-500">Tidak ada klausul kosong pada kriteria ini.</p>;
                            }

                            return (
                              <div className="flex gap-2 overflow-x-auto pb-1">
                                {missingClauses.map((clause) => (
                                  <Link
                                    key={clause.id}
                                    to={`/audit?clause=${clause.id}`}
                                    className="inline-flex shrink-0 items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700 transition hover:border-sky-300 hover:bg-sky-50 hover:text-sky-800"
                                    data-testid="criteria-missing-clause-link"
                                  >
                                    <span className="whitespace-nowrap">{clause.clause_number}</span>
                                    <span className="max-w-[240px] truncate font-normal text-slate-500">{clause.title}</span>
                                  </Link>
                                ))}
                              </div>
                            );
                          })()}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-4 xl:grid-cols-1">
            <Card className="rounded-[28px] border-white/70 bg-white/80">
              <CardContent className="p-6">
                <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Evidence Note</p>
                <p className="mt-4 text-sm leading-6 text-slate-700">
                  Fokus dashboard ini hanya pada total klausul, progres pengumpulan evidence, dan klausul yang masih kosong.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </Layout>
    );
  }

  const documentedClauses = stats?.criteria_scores?.reduce((sum, criteria) => sum + (criteria.documented_clauses || 0), 0) || 0;
  const totalEvidenceFiles = stats?.total_evidence_files || 0;
  const evidenceProgress = stats ? (documentedClauses / (stats.total_clauses || 1)) * 100 : 0;
  const completionPercentage = stats ? (stats.audited_clauses / stats.total_clauses) * 100 : 0;
  const cards = standardMetricCards(stats, completionPercentage);

  return (
    <Layout>
      <div className="space-y-6" data-testid="dashboard-page">
        <section className="grid gap-5 xl:grid-cols-[1.5fr_0.9fr]">
          <Card className="overflow-hidden rounded-[30px] border-0 bg-[linear-gradient(135deg,#123c36_0%,#1f5c53_58%,#2f7569_100%)] text-white shadow-[0_32px_90px_rgba(18,60,54,0.28)]">
            <CardContent className="p-7 md:p-8">
              <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
                <div className="max-w-2xl">
                  <p className="text-[11px] font-bold uppercase tracking-[0.28em] text-emerald-100/75">Audit Overview</p>
                  <h1 className="mt-3 text-4xl font-extrabold leading-tight md:text-5xl">Ringkasan audit keselamatan dan kepatuhan SMK3.</h1>
                  <p className="mt-4 max-w-xl text-sm leading-6 text-emerald-50/80 md:text-base">
                    Pantau progress klausul, keputusan auditor, dan evidence readiness dalam satu workspace operasional yang terpusat.
                  </p>
                  <div className="mt-6 flex flex-wrap items-center gap-3 text-xs text-emerald-50/75">
                    <span className="rounded-full border border-white/15 bg-white/10 px-3 py-1.5">PP 50/2012</span>
                    <span className="rounded-full border border-white/15 bg-white/10 px-3 py-1.5">Permenaker 26/2014</span>
                    <span className="rounded-full border border-white/15 bg-white/10 px-3 py-1.5">Evidence-driven review</span>
                  </div>
                </div>

                <div className="grid w-full gap-3 sm:grid-cols-3 lg:w-[360px] lg:grid-cols-1">
                  <div className="rounded-[24px] border border-white/12 bg-white/10 p-4 backdrop-blur-sm">
                    <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-emerald-100/70">Completion</p>
                    <p className="mt-2 text-3xl font-extrabold">{completionPercentage.toFixed(1)}%</p>
                    <p className="mt-1 text-xs text-emerald-50/70">Audit evidence telah diproses</p>
                  </div>
                  <div className="rounded-[24px] border border-white/12 bg-white/10 p-4 backdrop-blur-sm">
                    <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-emerald-100/70">Auditor Rated</p>
                    <p className="mt-2 text-3xl font-extrabold">{stats?.auditor_assessed_clauses || 0}</p>
                    <p className="mt-1 text-xs text-emerald-50/70">Klausul sudah punya keputusan final</p>
                  </div>
                  <Button
                    onClick={handleDownloadAllEvidence}
                    className="h-auto min-w-0 justify-between gap-3 whitespace-normal rounded-[24px] bg-white px-4 py-4 text-left text-slate-900 hover:bg-emerald-50"
                    data-testid="download-all-evidence-button"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-emerald-700">Evidence Export</p>
                      <p className="mt-1 break-words text-sm font-bold leading-snug sm:text-base">Gunakan export per kriteria</p>
                    </div>
                    <Archive className="h-5 w-5 shrink-0 text-emerald-700" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="rounded-[30px] border-white/70 bg-white/78 shadow-[0_24px_70px_rgba(45,68,58,0.10)] backdrop-blur-xl">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-2 text-lg">
                <ShieldAlert className="h-5 w-5 text-amber-600" />
                Quality Window
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              <div>
                <div className="mb-2 flex items-center justify-between text-sm font-medium text-slate-700">
                  <span>Progress Audit</span>
                  <span>{completionPercentage.toFixed(1)}%</span>
                </div>
                <Progress value={completionPercentage} className="h-2.5 rounded-full bg-slate-200" />
              </div>

              <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
                <div className="rounded-[22px] bg-emerald-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700">Confirm</p>
                  <p className="mt-2 text-2xl font-extrabold text-emerald-800">{stats?.confirm_count || 0}</p>
                </div>
                <div className="rounded-[22px] bg-amber-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-amber-700">NC Minor</p>
                  <p className="mt-2 text-2xl font-extrabold text-amber-800">{stats?.non_confirm_minor_count || 0}</p>
                </div>
                <div className="rounded-[22px] bg-rose-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-rose-700">NC Major</p>
                  <p className="mt-2 text-2xl font-extrabold text-rose-800">{stats?.non_confirm_major_count || 0}</p>
                </div>
              </div>

              <div className="rounded-[24px] border border-dashed border-slate-200 bg-slate-50/80 p-4 text-sm text-slate-600">
                Prioritas manajemen saat ini adalah mempercepat klausul yang sudah punya evidence tetapi belum memiliki keputusan auditor final.
              </div>
            </CardContent>
          </Card>
          </section>

          <Card className="rounded-[30px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]" data-testid="evidence-coverage-card">
            <CardHeader className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <CardTitle className="text-xl">Pemenuhan Dokumen</CardTitle>
                <p className="mt-1 text-sm text-slate-600">Progress pengumpulan evidence seluruh klausul.</p>
              </div>
              <div className="rounded-full bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-500">
                {documentedClauses}/{stats?.total_clauses || 0} klausul
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="mb-2 flex items-center justify-between text-sm font-medium text-slate-700">
                  <span>Progress evidence</span>
                  <span>{evidenceProgress.toFixed(1)}%</span>
                </div>
                <Progress value={evidenceProgress} className="h-2.5 rounded-full bg-sky-100" indicatorClassName="bg-sky-500" />
              </div>
              <div className="grid gap-3 sm:grid-cols-3">
                <div className="rounded-[22px] bg-sky-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-sky-700">Evidence</p>
                  <p className="mt-2 text-2xl font-extrabold text-sky-800">{documentedClauses}</p>
                </div>
                <div className="rounded-[22px] bg-indigo-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-700">Total File</p>
                  <p className="mt-2 text-2xl font-extrabold text-indigo-800">{totalEvidenceFiles}</p>
                </div>
                <div className="rounded-[22px] bg-emerald-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700">Sudah Upload</p>
                  <p className="mt-2 text-2xl font-extrabold text-emerald-800">{stats?.audited_clauses || 0}</p>
                </div>
                <div className="rounded-[22px] bg-amber-50 p-4 sm:col-span-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-amber-700">Belum Upload</p>
                  <p className="mt-2 text-2xl font-extrabold text-amber-800">{Math.max((stats?.total_clauses || 0) - documentedClauses, 0)}</p>
                </div>
              </div>
            </CardContent>
          </Card>

        {notifications.length > 0 && (
          <Card className="rounded-[28px] border border-amber-200/60 bg-[linear-gradient(180deg,#fff9ef_0%,#fff3df_100%)] shadow-[0_22px_55px_rgba(120,88,20,0.10)]" data-testid="notifications-card">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-amber-900">
                <AlertTriangle className="h-5 w-5" />
                Notifikasi Deadline
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3 lg:grid-cols-3">
                {notifications.slice(0, 3).map((notif) => (
                  <div key={notif.id} className="rounded-[24px] border border-white/80 bg-white/80 p-4" data-testid="notification-item">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-bold text-slate-900">{notif.clause_number}</p>
                        <p className="mt-1 text-sm text-slate-600">{notif.clause_title}</p>
                      </div>
                      <span className={`rounded-full px-2 py-1 text-[10px] font-bold uppercase tracking-[0.18em] ${
                        notif.urgency === 'critical' ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-700'
                      }`}>
                        {notif.urgency}
                      </span>
                    </div>
                    <p className="mt-4 line-clamp-3 text-sm leading-6 text-slate-600">{notif.recommendation}</p>
                    <p className={`mt-4 text-xs font-semibold ${notif.urgency === 'critical' ? 'text-rose-700' : 'text-amber-700'}`}>
                      {notif.days_left <= 0 ? 'Sudah melewati deadline' : `${notif.days_left} hari menuju deadline`}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {cards.map((card) => {
            const Icon = card.icon;
            return (
              <Card key={card.key} className={`rounded-[28px] border-white/70 bg-gradient-to-br ${card.tone} shadow-[0_18px_50px_rgba(39,60,52,0.08)]`}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">{card.title}</p>
                      <p className={`mt-3 text-4xl font-extrabold ${card.accent}`}>{card.value}</p>
                      <p className="mt-2 text-sm text-slate-600">{card.note}</p>
                    </div>
                    <div className="flex h-12 w-12 items-center justify-center rounded-[18px] bg-white/85 text-slate-700 shadow-sm">
                      <Icon className="h-5 w-5" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </section>

        {stats?.auditor_assessed_clauses > 0 && (
          <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]" data-testid="auditor-assessment-breakdown">
            <CardHeader>
              <CardTitle className="text-xl">Breakdown Penilaian Auditor</CardTitle>
              <p className="text-sm text-slate-600">
                {stats?.auditor_assessed_clauses} dari {stats?.total_clauses} klausul telah memiliki keputusan auditor.
              </p>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-3">
              <div className="rounded-[24px] bg-emerald-50 p-5">
                <CheckCircle2 className="h-6 w-6 text-emerald-600" />
                <p className="mt-4 text-3xl font-extrabold text-emerald-800">{stats?.confirm_count || 0}</p>
                <p className="mt-1 text-sm font-medium text-emerald-700">Confirm</p>
                <p className="mt-2 text-sm text-slate-600">Klausul dinilai memenuhi persyaratan.</p>
              </div>
              <div className="rounded-[24px] bg-amber-50 p-5">
                <AlertTriangle className="h-6 w-6 text-amber-600" />
                <p className="mt-4 text-3xl font-extrabold text-amber-800">{stats?.non_confirm_minor_count || 0}</p>
                <p className="mt-1 text-sm font-medium text-amber-700">Non-Confirm Minor</p>
                <p className="mt-2 text-sm text-slate-600">Masih ada gap kecil yang perlu ditutup.</p>
              </div>
              <div className="rounded-[24px] bg-rose-50 p-5">
                <XCircle className="h-6 w-6 text-rose-600" />
                <p className="mt-4 text-3xl font-extrabold text-rose-800">{stats?.non_confirm_major_count || 0}</p>
                <p className="mt-1 text-sm font-medium text-rose-700">Non-Confirm Major</p>
                <p className="mt-2 text-sm text-slate-600">Perlu tindakan prioritas dan pengawasan cepat.</p>
              </div>
            </CardContent>

            <CardContent className="pt-0">
              <div className="grid gap-4 lg:grid-cols-2">
                {[
                  { key: 'major', title: 'Non-Confirm Major', tone: 'rose' },
                  { key: 'minor', title: 'Non-Confirm Minor', tone: 'amber' },
                ].map((group) => {
                  const items = auditorFindingItems[group.key] || [];
                  return (
                    <div key={group.key} className="rounded-[24px] border border-slate-200 bg-slate-50/80 p-4">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="text-sm font-bold text-slate-900">{group.title}</p>
                          <p className="mt-1 text-xs text-slate-500">{(items.length || (group.key === 'major' ? stats?.non_confirm_major_count : stats?.non_confirm_minor_count) || 0)} klausul temuan</p>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          className={`h-8 rounded-full px-3 text-xs ${group.tone === 'rose' ? 'text-rose-700 hover:bg-rose-50' : 'text-amber-700 hover:bg-amber-50'}`}
                          onClick={() => toggleAuditorFinding(group.key)}
                          data-testid={`toggle-${group.key}-findings-button`}
                        >
                          {auditorFindingOpen[group.key] ? 'Tutup' : 'Lihat'}
                        </Button>
                      </div>

                      {auditorFindingOpen[group.key] && (
                        <div className="mt-4">
                          {auditorFindingLoading ? (
                            <p className="text-sm text-slate-500">Memuat klausul temuan...</p>
                          ) : items.length === 0 ? (
                            <p className="text-sm text-slate-500">Tidak ada temuan pada kategori ini.</p>
                          ) : (
                            <div className="flex gap-2 overflow-x-auto pb-1">
                              {items
                                .filter((item) => (group.key === 'major' ? item.auditor_status === 'non-confirm-major' : item.auditor_status === 'non-confirm-minor'))
                                .map((item) => (
                                  <Link
                                    key={item.id}
                                    to={`/audit?clause=${item.clause_id}`}
                                    className="inline-flex shrink-0 items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 transition hover:border-sky-300 hover:bg-sky-50 hover:text-sky-800"
                                    data-testid="finding-clause-link"
                                  >
                                    <span className="whitespace-nowrap">{item.clause_number}</span>
                                    <span className="max-w-[240px] truncate font-normal text-slate-500">{item.clause_title}</span>
                                  </Link>
                                ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        )}

        <Card className="rounded-[30px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]" data-testid="criteria-scores-card">
          <CardHeader className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <CardTitle className="text-xl">Performa Per Kriteria Audit</CardTitle>
              <p className="mt-1 text-sm text-slate-600">Kriteria diurutkan sebagai panel kesiapan operasional untuk audit dan tindak lanjut.</p>
            </div>
            <div className="rounded-full bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-500">
              {stats?.criteria_scores?.length || 0} kriteria
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {stats?.criteria_scores?.map((criteria) => (
                <div key={criteria.id} className="rounded-[24px] border border-slate-100 bg-slate-50/70 p-4 md:p-5" data-testid="criteria-score-item">
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-lg font-bold text-slate-900">{criteria.name}</h3>
                        <span className={`rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.18em] ${
                          criteria.strength === 'strong'
                            ? 'bg-emerald-100 text-emerald-700'
                            : criteria.strength === 'moderate'
                              ? 'bg-amber-100 text-amber-700'
                              : 'bg-rose-100 text-rose-700'
                        }`}>
                          {criteria.strength_label || (criteria.strength === 'strong' ? 'Memuaskan' : criteria.strength === 'moderate' ? 'Baik' : 'Kurang')}
                        </span>
                        {criteria.audited_clauses > 0 && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDownloadCriteriaEvidence(criteria.id, criteria.name)}
                            className="h-8 rounded-full px-3 text-xs text-sky-700 hover:bg-sky-50 hover:text-sky-800"
                            data-testid="download-criteria-evidence-button"
                          >
                            <Download className="mr-1.5 h-3.5 w-3.5" />
                            Export evidence
                          </Button>
                        )}
                      </div>
                      <div className="mt-3 flex flex-wrap items-center gap-4 text-sm text-slate-600">
                        <span>{criteria.audited_clauses}/{criteria.total_clauses} klausul teraudit</span>
                        <span>{criteria.auditor_assessed_clauses} keputusan auditor</span>
                        <span>{criteria.evidence_files || 0} file evidence</span>
                        <span className="font-medium text-slate-700">Avg AI {criteria.average_score?.toFixed(1) || '0.0'}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-6">
                      <div>
                        <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Achievement</p>
                        <p className={`mt-1 text-3xl font-extrabold ${
                          criteria.strength === 'strong'
                            ? 'text-emerald-700'
                            : criteria.strength === 'moderate'
                              ? 'text-amber-700'
                              : 'text-rose-700'
                        }`}>
                          {criteria.achievement_percentage?.toFixed(1) || '0.0'}%
                        </p>
                      </div>
                      <div className="hidden h-12 w-px bg-slate-200 md:block" />
                      <div className="text-sm text-slate-600">
                        <p className="font-semibold text-slate-800">{criteria.confirm_count} confirm</p>
                        <p>{criteria.non_confirm_minor_count} NC minor</p>
                        <p>{criteria.non_confirm_major_count} NC major</p>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4">
                    <Progress value={criteria.achievement_percentage || 0} className="h-2.5 rounded-full bg-white" />
                  </div>

                  <div className="mt-4 rounded-[20px] border border-slate-200 bg-white/85 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">Klausul Belum Upload</p>
                        <p className="mt-1 text-xs text-slate-600">Klik klausul untuk langsung ke halaman evidence.</p>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 rounded-full px-3 text-xs text-slate-600 hover:bg-slate-100"
                        onClick={() => toggleCriteriaMissing(criteria.id)}
                        data-testid="toggle-criteria-missing-button"
                      >
                        {criteriaMissingOpen[criteria.id] ? 'Tutup' : 'Lihat'}
                      </Button>
                    </div>

                    {criteriaMissingOpen[criteria.id] && (
                      <div className="mt-3">
                        {criteriaClauseLoading[criteria.id] ? (
                          <p className="text-sm text-slate-500">Memuat klausul...</p>
                        ) : (() => {
                          const clauses = criteriaClauseCache[criteria.id] || [];
                          const missingClauses = clauses.filter((clause) => (clause.document_count || 0) === 0);

                          if (missingClauses.length === 0) {
                            return <p className="text-sm text-slate-500">Semua klausul pada kriteria ini sudah memiliki evidence.</p>;
                          }

                          return (
                            <div className="flex gap-2 overflow-x-auto pb-1">
                              {missingClauses.map((clause) => (
                                <Link
                                  key={clause.id}
                                  to={`/audit?clause=${clause.id}`}
                                  className="inline-flex shrink-0 items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700 transition hover:border-sky-300 hover:bg-sky-50 hover:text-sky-800"
                                  data-testid="criteria-missing-clause-link"
                                >
                                  <span className="whitespace-nowrap">{clause.clause_number}</span>
                                  <span className="max-w-[240px] truncate font-normal text-slate-500">{clause.title}</span>
                                </Link>
                              ))}
                            </div>
                          );
                        })()}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-4 xl:grid-cols-3">
          <Card className="rounded-[28px] border-white/70 bg-white/80 xl:col-span-2">
            <CardContent className="flex h-full flex-col justify-between p-6">
              <div>
                <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Management Note</p>
                <p className="mt-4 text-2xl font-extrabold leading-tight text-slate-950">
                  Pastikan setiap klausul yang sudah punya evidence juga bergerak menuju keputusan auditor final dan tindak lanjut yang terdokumentasi.
                </p>
              </div>
              <div className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-emerald-700">
                Focus on readiness, decision quality, and closure discipline
                <ArrowUpRight className="h-4 w-4" />
              </div>
            </CardContent>
          </Card>

          <Card className="rounded-[28px] border-white/70 bg-white/80">
            <CardContent className="p-6">
              <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Standar Penilaian</p>
              <div className="mt-5 space-y-3 text-sm">
                <div className="flex items-center gap-3 rounded-[18px] bg-emerald-50 px-4 py-3 text-emerald-800">
                  <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
                  85-100%: Memuaskan
                </div>
                <div className="flex items-center gap-3 rounded-[18px] bg-amber-50 px-4 py-3 text-amber-800">
                  <span className="h-2.5 w-2.5 rounded-full bg-amber-500" />
                  60-84%: Baik
                </div>
                <div className="flex items-center gap-3 rounded-[18px] bg-rose-50 px-4 py-3 text-rose-800">
                  <span className="h-2.5 w-2.5 rounded-full bg-rose-500" />
                  0-59%: Kurang
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </Layout>
  );
};

export default DashboardPage;
