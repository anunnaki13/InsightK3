import React, { useState, useEffect, useContext } from 'react';
import { AppContext } from '../App';
import { Link } from 'react-router-dom';
import axios from 'axios';
import Layout from '../components/Layout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Download, FileText, Loader2, ShieldCheck, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import { loadSurveyorNotes } from '../lib/surveyorNotes';

const reportItems = [
  'Statistik audit keseluruhan',
  'Pencapaian audit berbasis penilaian auditor',
  'Breakdown Confirm dan Non-Confirm per kriteria',
  'Detail penilaian auditor per klausul',
  'Catatan auditor dan tanggal kesepakatan',
  'Analisis AI sebagai referensi pendukung',
];

const ReportsPage = () => {
  const { API, user } = useContext(AppContext);
  const [generating, setGenerating] = useState(false);
  const [criteria, setCriteria] = useState([]);
  const [clauses, setClauses] = useState([]);
  const [surveyNotes, setSurveyNotes] = useState([]);
  const [detailMode, setDetailMode] = useState('all');
  const isSurveyor = user?.role === 'surveyor';

  useEffect(() => {
    if (!isSurveyor) {
      return;
    }

    const loadSurveyorReportData = async () => {
      try {
        const [criteriaRes, clausesRes] = await Promise.all([
          axios.get(`${API}/criteria`),
          axios.get(`${API}/clauses`),
        ]);
        setCriteria(criteriaRes.data);
        setClauses(clausesRes.data);
        setSurveyNotes(loadSurveyorNotes(user?.id));
      } catch (error) {
        toast.error('Gagal memuat data laporan surveyor');
      }
    };

    loadSurveyorReportData();
  }, [API, isSurveyor, user?.id]);

  const handleGenerateReport = async () => {
    setGenerating(true);
    try {
      const response = await axios.post(`${API}/reports/generate`, {
        detail_mode: detailMode,
      });
      const { filename, content } = response.data;

      const blob = new Blob([Uint8Array.from(atob(content), (char) => char.charCodeAt(0))], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(link);

      toast.success('Laporan berhasil diunduh!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal membuat laporan');
    } finally {
      setGenerating(false);
    }
  };

  if (isSurveyor) {
    const notesByClause = surveyNotes.reduce((acc, note) => {
      const current = acc[note.clause_id] || [];
      return { ...acc, [note.clause_id]: [...current, note] };
    }, {});
    const clausesByCriteria = clauses.reduce((acc, clause) => {
      const current = acc[clause.criteria_id] || [];
      return { ...acc, [clause.criteria_id]: [...current, clause] };
    }, {});
    const criteriaWithNotes = criteria
      .map((criterion) => {
        const criterionClauses = clausesByCriteria[criterion.id] || [];
        const noteClauses = criterionClauses
          .filter((clause) => (notesByClause[clause.id] || []).length > 0)
          .map((clause) => ({
            ...clause,
            notes: notesByClause[clause.id] || [],
          }));

        return {
          ...criterion,
          clauses: noteClauses,
          note_count: noteClauses.reduce((sum, clause) => sum + clause.notes.length, 0),
        };
      })
      .filter((criterion) => criterion.clauses.length > 0);

    const documentedClauses = criteriaWithNotes.reduce((sum, criterion) => sum + criterion.clauses.length, 0);
    const totalDocuments = surveyNotes.length;

    return (
      <Layout>
        <div className="space-y-6" data-testid="reports-page">
          <section className="grid gap-5 xl:grid-cols-[1.35fr_0.95fr]">
            <Card className="overflow-hidden rounded-[30px] border-0 bg-[linear-gradient(135deg,#123c36_0%,#1f5c53_58%,#2f7569_100%)] text-white shadow-[0_32px_90px_rgba(18,60,54,0.28)]">
              <CardContent className="p-7 md:p-8">
                <p className="text-[11px] font-bold uppercase tracking-[0.28em] text-emerald-100/75">Surveyor Report</p>
                <h1 className="mt-3 text-4xl font-extrabold leading-tight md:text-5xl">Laporan catatan surveyor.</h1>
                <p className="mt-4 max-w-2xl text-sm leading-6 text-emerald-50/80 md:text-base">
                  Halaman ini khusus untuk surveyor. Isinya ringkasan klausul yang sudah punya catatan, total catatan, dan akses cepat ke klausul yang terkait.
                </p>

                <div className="mt-7 grid gap-3 sm:grid-cols-3">
                  <div className="rounded-[22px] border border-white/14 bg-white/10 p-4">
                    <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-emerald-100/70">Klausul</p>
                    <p className="mt-2 text-2xl font-extrabold">{documentedClauses}</p>
                    <p className="mt-1 text-xs text-emerald-50/70">punya catatan</p>
                  </div>
                  <div className="rounded-[22px] border border-white/14 bg-white/10 p-4">
                    <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-emerald-100/70">Catatan</p>
                    <p className="mt-2 text-2xl font-extrabold">{totalDocuments}</p>
                    <p className="mt-1 text-xs text-emerald-50/70">total catatan tersimpan</p>
                  </div>
                  <div className="rounded-[22px] border border-white/14 bg-white/10 p-4">
                    <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-emerald-100/70">Mode</p>
                    <p className="mt-2 text-2xl font-extrabold">Notes</p>
                    <p className="mt-1 text-xs text-emerald-50/70">tanpa penilaian auditor</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="rounded-[30px] border-white/70 bg-white/80 shadow-[0_24px_70px_rgba(45,68,58,0.10)] backdrop-blur-xl" data-testid="report-card">
              <CardHeader className="pb-2">
                <div className="flex items-center gap-3">
                  <div className="flex h-12 w-12 items-center justify-center rounded-[18px] bg-emerald-50 text-emerald-700">
                    <FileText className="h-5 w-5" />
                  </div>
                  <div>
                    <CardTitle className="text-xl">Catatan Surveyor</CardTitle>
                    <p className="mt-1 text-sm text-slate-600">Dropdown mengikuti 12 kriteria dan hanya menampilkan klausul yang punya catatan.</p>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-5">
                <div className="space-y-3">
                  {criteriaWithNotes.length === 0 ? (
                    <div className="rounded-[18px] bg-slate-50 px-4 py-5 text-sm text-slate-500">
                      Belum ada catatan surveyor untuk ditampilkan.
                    </div>
                  ) : (
                    criteriaWithNotes.map((criterion) => (
                      <details key={criterion.id} className="rounded-[22px] border border-slate-200 bg-slate-50/80 p-4">
                        <summary className="flex cursor-pointer list-none items-center justify-between gap-3">
                          <div>
                            <p className="text-sm font-bold text-slate-900">{criterion.name}</p>
                            <p className="mt-1 text-xs text-slate-500">
                              {criterion.clauses.length} klausul dengan catatan • {criterion.note_count} catatan
                            </p>
                          </div>
                          <span className="rounded-full bg-white px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">
                            buka
                          </span>
                        </summary>

                        <div className="mt-4 space-y-3">
                          {criterion.clauses.map((clause) => (
                            <div key={clause.id} className="rounded-[18px] border border-white bg-white p-3">
                              <div className="flex items-start justify-between gap-3">
                                <Link
                                  to={`/audit?clause=${clause.id}`}
                                  className="min-w-0 flex-1"
                                >
                                  <p className="text-sm font-semibold text-slate-900">{clause.clause_number}</p>
                                  <p className="mt-1 text-xs text-slate-500">{clause.title}</p>
                                </Link>
                                <p className="text-xs font-semibold text-emerald-700">{clause.notes.length} catatan</p>
                              </div>
                              <div className="mt-3 space-y-2">
                                {clause.notes.map((note) => (
                                  <div key={note.id} className="rounded-[16px] bg-slate-50 px-3 py-2">
                                    <p className="text-sm leading-6 text-slate-700 whitespace-pre-line">{note.note_text}</p>
                                    <p className="mt-1 text-[11px] text-slate-500">
                                      {new Date(note.created_at).toLocaleString('id-ID')}
                                    </p>
                                  </div>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      </details>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </section>

        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6" data-testid="reports-page">
        <section className="grid gap-5 xl:grid-cols-[1.35fr_0.95fr]">
          <Card className="overflow-hidden rounded-[30px] border-0 bg-[linear-gradient(135deg,#0f3f47_0%,#155f6c_62%,#2b7d89_100%)] text-white shadow-[0_32px_90px_rgba(18,60,72,0.26)]">
            <CardContent className="p-7 md:p-8">
              <p className="text-[11px] font-bold uppercase tracking-[0.28em] text-cyan-100/75">Reporting Suite</p>
              <h1 className="mt-3 text-4xl font-extrabold leading-tight md:text-5xl">Generate laporan audit yang siap dibawa ke forum manajemen.</h1>
              <p className="mt-4 max-w-2xl text-sm leading-6 text-cyan-50/80 md:text-base">
                Paket laporan PDF dirancang untuk memberi ringkasan eksekutif, detail temuan, dan jejak keputusan auditor dalam format yang rapi dan konsisten.
              </p>

              <div className="mt-7 grid gap-3 sm:grid-cols-3">
                <div className="rounded-[22px] border border-white/14 bg-white/10 p-4">
                  <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-cyan-100/70">Output</p>
                  <p className="mt-2 text-2xl font-extrabold">PDF</p>
                  <p className="mt-1 text-xs text-cyan-50/70">Siap arsip dan distribusi</p>
                </div>
                <div className="rounded-[22px] border border-white/14 bg-white/10 p-4">
                  <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-cyan-100/70">Audience</p>
                  <p className="mt-2 text-2xl font-extrabold">Mgmt</p>
                  <p className="mt-1 text-xs text-cyan-50/70">Mudah dibawa ke review pimpinan</p>
                </div>
                <div className="rounded-[22px] border border-white/14 bg-white/10 p-4">
                  <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-cyan-100/70">Coverage</p>
                  <p className="mt-2 text-2xl font-extrabold">Full</p>
                  <p className="mt-1 text-xs text-cyan-50/70">Ringkasan dan detail klausul</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="rounded-[30px] border-white/70 bg-white/80 shadow-[0_24px_70px_rgba(45,68,58,0.10)] backdrop-blur-xl" data-testid="report-card">
            <CardHeader className="pb-2">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-[18px] bg-cyan-50 text-cyan-700">
                  <FileText className="h-5 w-5" />
                </div>
                <div>
                  <CardTitle className="text-xl">Laporan Lengkap</CardTitle>
                  <p className="mt-1 text-sm text-slate-600">Ringkasan dan detail audit semua kriteria.</p>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="space-y-3">
                {reportItems.map((item) => (
                  <div key={item} className="flex items-center gap-3 rounded-[18px] bg-slate-50 px-4 py-3 text-sm text-slate-700">
                    <ShieldCheck className="h-4 w-4 text-emerald-600" />
                    {item}
                  </div>
                ))}
              </div>

              <div className="space-y-2 rounded-[18px] border border-slate-200 bg-white p-4">
                <Label htmlFor="report-detail-mode" className="text-sm font-semibold text-slate-900">
                  Detail PDF
                </Label>
                <Select value={detailMode} onValueChange={setDetailMode}>
                  <SelectTrigger id="report-detail-mode" className="h-11 rounded-[14px]" data-testid="report-detail-mode">
                    <SelectValue placeholder="Pilih detail laporan" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Semua detail klausul</SelectItem>
                    <SelectItem value="findings">Temuan / non-confirm saja</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs leading-5 text-slate-500">
                  Pilih semua klausul atau batasi PDF hanya pada klausul temuan auditor.
                </p>
              </div>

              <Button
                onClick={handleGenerateReport}
                disabled={generating}
                className="h-12 w-full rounded-[18px] bg-slate-950 text-white hover:bg-slate-800"
                data-testid="generate-report-button"
              >
                {generating ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Membuat Laporan...
                  </>
                ) : (
                  <>
                    <Download className="mr-2 h-4 w-4" />
                    Generate dan Download PDF
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-5 lg:grid-cols-2">
          <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]" data-testid="info-card">
            <CardHeader>
              <CardTitle className="text-xl">Informasi Laporan</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm text-slate-600">
              <div className="rounded-[22px] bg-slate-50 p-4">
                <h4 className="font-semibold text-slate-900">Format Laporan</h4>
                <p className="mt-2">Laporan dihasilkan dalam format PDF profesional yang mencakup semua data audit terkini dalam struktur yang mudah dibaca.</p>
              </div>
              <div className="rounded-[22px] bg-slate-50 p-4">
                <h4 className="font-semibold text-slate-900">Isi Laporan</h4>
                <p className="mt-2">Ringkasan eksekutif, skor per kriteria, detail hasil audit, dan area yang perlu ditingkatkan ditata agar langsung bisa dipakai untuk review.</p>
              </div>
              <div className="rounded-[22px] bg-slate-50 p-4">
                <h4 className="font-semibold text-slate-900">Penggunaan</h4>
                <p className="mt-2">Cocok untuk presentasi manajemen, dokumentasi formal audit, dan bahan pengendalian tindak lanjut secara periodik.</p>
              </div>
            </CardContent>
          </Card>

          <Card className="rounded-[28px] border-0 bg-[linear-gradient(135deg,#f7f8ee_0%,#edf6f2_52%,#e7f0f7_100%)] shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
            <CardContent className="p-6">
              <div className="flex items-start gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-[18px] bg-white text-emerald-700 shadow-sm">
                  <Sparkles className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-xl font-extrabold text-slate-950">Praktik Penggunaan yang Disarankan</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-600">
                    Laporan akan paling bernilai jika diperlakukan sebagai artefak pengambilan keputusan, bukan sekadar output administrasi.
                  </p>
                </div>
              </div>

              <div className="mt-6 space-y-3 text-sm">
                <div className="rounded-[20px] bg-white/80 px-4 py-3 text-slate-700">Generate laporan secara berkala untuk tracking progress dan closure.</div>
                <div className="rounded-[20px] bg-white/80 px-4 py-3 text-slate-700">Bagikan ke stakeholder utama untuk menjaga transparansi temuan dan tindak lanjut.</div>
                <div className="rounded-[20px] bg-white/80 px-4 py-3 text-slate-700">Gunakan sebagai basis action plan dan prioritas intervensi audit berikutnya.</div>
                <div className="rounded-[20px] bg-white/80 px-4 py-3 text-slate-700">Simpan sebagai jejak historis yang konsisten antar periode audit.</div>
              </div>
            </CardContent>
          </Card>
        </section>
      </div>
    </Layout>
  );
};

export default ReportsPage;
