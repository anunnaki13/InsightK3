import React, { useContext, useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { AppContext } from '../App';
import Layout from '../components/Layout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { AlertTriangle, ClipboardList, Download, FileText, ImagePlus, Plus, RefreshCcw, ShieldAlert, Siren, Sparkles, Trash2 } from 'lucide-react';
import { toast } from 'sonner';

const emptySurveyForm = {
  survey_type: 'daily_walk',
  area_codes: [],
  planned_date: '',
  actual_date: '',
  surveyor_ids: '',
  summary_notes: '',
};

const emptyFindingForm = {
  survey_id: 'quick',
  area_code: '',
  sub_location: '',
  finding_type: 'unsafe_condition',
  description: '',
  severity: 'medium',
  potential_consequence: '',
  immediate_action: '',
  recommendation: '',
  deadline: '',
  related_clause_id: '',
};

const severityTone = {
  low: 'bg-emerald-100 text-emerald-700',
  medium: 'bg-sky-100 text-sky-700',
  high: 'bg-amber-100 text-amber-700',
  critical: 'bg-rose-100 text-rose-700',
};

const FieldSurveyPage = () => {
  const { API, user } = useContext(AppContext);
  const [areas, setAreas] = useState([]);
  const [surveyTypes, setSurveyTypes] = useState([]);
  const [findingTypes, setFindingTypes] = useState([]);
  const [severityLevels, setSeverityLevels] = useState([]);
  const [surveys, setSurveys] = useState([]);
  const [findings, setFindings] = useState([]);
  const [dashboard, setDashboard] = useState([]);
  const [overdue, setOverdue] = useState([]);
  const [selectedSurveyId, setSelectedSurveyId] = useState(null);
  const [selectedSurvey, setSelectedSurvey] = useState(null);
  const [surveyFindings, setSurveyFindings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [surveyDialogOpen, setSurveyDialogOpen] = useState(false);
  const [findingDialogOpen, setFindingDialogOpen] = useState(false);
  const [surveyForm, setSurveyForm] = useState(emptySurveyForm);
  const [findingForm, setFindingForm] = useState(emptyFindingForm);
  const [photoMap, setPhotoMap] = useState({});
  const [uploadingFindingId, setUploadingFindingId] = useState(null);
  const [deletingPhotoId, setDeletingPhotoId] = useState(null);
  const [generatingReport, setGeneratingReport] = useState(false);

  const canWrite = ['admin', 'risk_officer', 'surveyor'].includes(user?.role);

  const areaMap = useMemo(
    () => Object.fromEntries(areas.map((area) => [area.code, area.name])),
    [areas],
  );

  const metrics = useMemo(() => ({
    totalFindings: findings.length,
    openFindings: findings.filter((item) => item.status !== 'closed').length,
    criticalFindings: findings.filter((item) => item.severity === 'critical').length,
    autoLinked: findings.filter((item) => item.related_risk_id).length,
  }), [findings]);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (selectedSurveyId) {
      fetchSurveyDetail(selectedSurveyId);
    }
  }, [selectedSurveyId]);

  useEffect(() => {
    if (!selectedSurveyId && surveys[0]?.id) {
      setSelectedSurveyId(surveys[0].id);
      return;
    }
    if (selectedSurveyId && !surveys.some((survey) => survey.id === selectedSurveyId)) {
      setSelectedSurveyId(surveys[0]?.id || null);
    }
  }, [surveys, selectedSurveyId]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [
        areasRes,
        surveyTypesRes,
        findingTypesRes,
        severityRes,
        surveysRes,
        findingsRes,
        dashboardRes,
        overdueRes,
      ] = await Promise.all([
        axios.get(`${API}/risk/areas`),
        axios.get(`${API}/field-survey/survey-types`),
        axios.get(`${API}/field-survey/finding-types`),
        axios.get(`${API}/field-survey/severity-levels`),
        axios.get(`${API}/field-survey/surveys`),
        axios.get(`${API}/field-survey/findings`),
        axios.get(`${API}/field-survey/dashboard`),
        axios.get(`${API}/field-survey/findings/overdue`),
      ]);
      setAreas(areasRes.data || []);
      setSurveyTypes(surveyTypesRes.data || []);
      setFindingTypes(findingTypesRes.data || []);
      setSeverityLevels(severityRes.data || []);
      setSurveys(surveysRes.data.items || []);
      setFindings(findingsRes.data.items || []);
      const allFindings = findingsRes.data.items || [];
      if (allFindings.length > 0) {
        const photoEntries = await Promise.all(
          allFindings.map(async (item) => {
            const response = await axios.get(`${API}/field-survey/findings/${item.id}/photos`);
            return [item.id, response.data.items || []];
          }),
        );
        setPhotoMap(Object.fromEntries(photoEntries));
      } else {
        setPhotoMap({});
      }
      setDashboard(dashboardRes.data.areas || []);
      setOverdue(overdueRes.data.items || []);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal memuat workspace field survey');
    } finally {
      setLoading(false);
    }
  };

  const fetchSurveyDetail = async (surveyId) => {
    setDetailLoading(true);
    try {
      const response = await axios.get(`${API}/field-survey/surveys/${surveyId}`);
      setSelectedSurvey(response.data.survey);
      setSurveyFindings(response.data.findings || []);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal memuat detail field survey');
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCreateSurvey = async (event) => {
    event.preventDefault();
    try {
      await axios.post(`${API}/field-survey/surveys`, {
        ...surveyForm,
        surveyor_ids: surveyForm.surveyor_ids.split(',').map((item) => item.trim()).filter(Boolean),
      });
      toast.success('Field survey berhasil dibuat');
      setSurveyDialogOpen(false);
      setSurveyForm(emptySurveyForm);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal membuat field survey');
    }
  };

  const handleCreateFinding = async (event) => {
    event.preventDefault();
    try {
      await axios.post(`${API}/field-survey/findings`, {
        ...findingForm,
        survey_id: findingForm.survey_id === 'quick' ? null : findingForm.survey_id,
        deadline: findingForm.deadline || null,
        related_clause_id: findingForm.related_clause_id || null,
      });
      toast.success('Finding berhasil dicatat');
      setFindingDialogOpen(false);
      setFindingForm(emptyFindingForm);
      fetchData();
      if (selectedSurveyId) {
        fetchSurveyDetail(selectedSurveyId);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal mencatat finding');
    }
  };

  const handleCloseFinding = async (findingId) => {
    try {
      await axios.post(`${API}/field-survey/findings/${findingId}/close`, { close_note: 'Closed from workspace' });
      toast.success('Finding ditutup');
      fetchData();
      if (selectedSurveyId) {
        fetchSurveyDetail(selectedSurveyId);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal menutup finding');
    }
  };

  const handleCloseSurvey = async () => {
    if (!selectedSurveyId) return;
    try {
      await axios.put(`${API}/field-survey/surveys/${selectedSurveyId}/close`);
      toast.success('Survey ditutup');
      fetchData();
      fetchSurveyDetail(selectedSurveyId);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal menutup survey');
    }
  };

  const handleUploadFindingPhoto = async (findingId, file) => {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    setUploadingFindingId(findingId);
    try {
      await axios.post(`${API}/field-survey/findings/${findingId}/photos`, formData);
      toast.success('Foto finding berhasil diupload');
      fetchData();
      if (selectedSurveyId) {
        fetchSurveyDetail(selectedSurveyId);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal upload foto finding');
    } finally {
      setUploadingFindingId(null);
    }
  };

  const handleDownloadFindingPhoto = async (photo) => {
    try {
      const response = await axios.get(`${API}/field-survey/files/${photo.id}/download`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.download = photo.filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal mengunduh foto finding');
    }
  };

  const handleDeleteFindingPhoto = async (photoId) => {
    setDeletingPhotoId(photoId);
    try {
      await axios.delete(`${API}/field-survey/files/${photoId}`);
      toast.success('Foto finding dihapus');
      fetchData();
      if (selectedSurveyId) {
        fetchSurveyDetail(selectedSurveyId);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal menghapus foto finding');
    } finally {
      setDeletingPhotoId(null);
    }
  };

  const handleGenerateSurveyReport = async () => {
    if (!selectedSurveyId) return;
    setGeneratingReport(true);
    try {
      const response = await axios.post(`${API}/field-survey/surveys/${selectedSurveyId}/report`);
      const { filename, content } = response.data;
      const blob = new Blob([Uint8Array.from(atob(content), (char) => char.charCodeAt(0))], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success('Report field survey berhasil diunduh');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal membuat report field survey');
    } finally {
      setGeneratingReport(false);
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
      <div className="space-y-6" data-testid="field-survey-page">
        <section className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
          <Card className="overflow-hidden rounded-[30px] border-0 bg-[linear-gradient(135deg,#211c3d_0%,#384b7a_58%,#5a76a8_100%)] text-white shadow-[0_32px_90px_rgba(33,28,61,0.24)]">
            <CardContent className="p-7 md:p-8">
              <p className="text-[11px] font-bold uppercase tracking-[0.28em] text-indigo-100/75">Module C</p>
              <h1 className="mt-3 text-4xl font-extrabold leading-tight md:text-5xl">Field survey sekarang siap dipakai untuk patrol dan quick reporting.</h1>
              <p className="mt-4 max-w-2xl text-sm leading-6 text-indigo-50/80 md:text-base">
                Survey lapangan, temuan operasional, monitoring overdue, dan auto-link severity tinggi ke ERM sudah aktif dalam satu workspace.
              </p>
            </CardContent>
          </Card>

          <Card className="rounded-[30px] border-white/70 bg-white/80 shadow-[0_24px_70px_rgba(45,68,58,0.10)] backdrop-blur-xl">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Finding Snapshot</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-[20px] bg-slate-50 px-4 py-3">
                <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Total</p>
                <p className="mt-2 text-3xl font-extrabold text-slate-950">{metrics.totalFindings}</p>
              </div>
              <div className="rounded-[20px] bg-amber-50 px-4 py-3">
                <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-amber-700">Open</p>
                <p className="mt-2 text-3xl font-extrabold text-amber-800">{metrics.openFindings}</p>
              </div>
              <div className="rounded-[20px] bg-rose-50 px-4 py-3">
                <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-rose-700">Critical</p>
                <p className="mt-2 text-3xl font-extrabold text-rose-800">{metrics.criticalFindings}</p>
              </div>
              <div className="rounded-[20px] bg-emerald-50 px-4 py-3">
                <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-emerald-700">Linked ERM</p>
                <p className="mt-2 text-3xl font-extrabold text-emerald-800">{metrics.autoLinked}</p>
              </div>
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-5 xl:grid-cols-[0.92fr_1.08fr]">
          <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
            <CardHeader className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <CardTitle className="text-xl">Survey & Finding Actions</CardTitle>
                <p className="mt-1 text-sm text-slate-600">Buat survey patrol atau quick report finding dari halaman yang sama.</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button variant="outline" className="rounded-[16px]" onClick={fetchData}>
                  <RefreshCcw className="mr-2 h-4 w-4" />
                  Refresh
                </Button>
                {canWrite && (
                  <>
                    <Dialog open={surveyDialogOpen} onOpenChange={setSurveyDialogOpen}>
                      <DialogTrigger asChild>
                        <Button variant="outline" className="rounded-[16px]">
                          <ClipboardList className="mr-2 h-4 w-4" />
                          Survey Baru
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-2xl rounded-[28px]">
                        <DialogHeader>
                          <DialogTitle>Buat Field Survey</DialogTitle>
                        </DialogHeader>
                        <form onSubmit={handleCreateSurvey} className="grid gap-4 md:grid-cols-2">
                          <div className="space-y-2">
                            <Label>Tipe Survey</Label>
                            <Select value={surveyForm.survey_type} onValueChange={(value) => setSurveyForm({ ...surveyForm, survey_type: value })}>
                              <SelectTrigger className="h-12 rounded-[16px]"><SelectValue /></SelectTrigger>
                              <SelectContent>
                                {surveyTypes.map((item) => <SelectItem key={item} value={item}>{item}</SelectItem>)}
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="space-y-2">
                            <Label>Area</Label>
                            <Select value={surveyForm.area_codes[0] || ''} onValueChange={(value) => setSurveyForm({ ...surveyForm, area_codes: [value] })}>
                              <SelectTrigger className="h-12 rounded-[16px]"><SelectValue placeholder="Pilih area" /></SelectTrigger>
                              <SelectContent>
                                {areas.map((area) => <SelectItem key={area.code} value={area.code}>{area.name}</SelectItem>)}
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="space-y-2">
                            <Label>Planned Date</Label>
                            <Input type="date" value={surveyForm.planned_date} onChange={(event) => setSurveyForm({ ...surveyForm, planned_date: event.target.value })} className="h-12 rounded-[16px]" />
                          </div>
                          <div className="space-y-2">
                            <Label>Actual Date</Label>
                            <Input type="date" value={surveyForm.actual_date} onChange={(event) => setSurveyForm({ ...surveyForm, actual_date: event.target.value })} required className="h-12 rounded-[16px]" />
                          </div>
                          <div className="space-y-2 md:col-span-2">
                            <Label>Surveyor IDs</Label>
                            <Input value={surveyForm.surveyor_ids} onChange={(event) => setSurveyForm({ ...surveyForm, surveyor_ids: event.target.value })} placeholder="pisahkan dengan koma" className="h-12 rounded-[16px]" />
                          </div>
                          <div className="space-y-2 md:col-span-2">
                            <Label>Summary Notes</Label>
                            <Textarea value={surveyForm.summary_notes} onChange={(event) => setSurveyForm({ ...surveyForm, summary_notes: event.target.value })} rows={4} className="rounded-[16px]" />
                          </div>
                          <div className="md:col-span-2">
                            <Button type="submit" className="h-12 w-full rounded-[18px] bg-indigo-700 hover:bg-indigo-800">Simpan Survey</Button>
                          </div>
                        </form>
                      </DialogContent>
                    </Dialog>

                    <Dialog open={findingDialogOpen} onOpenChange={setFindingDialogOpen}>
                      <DialogTrigger asChild>
                        <Button className="rounded-[16px] bg-slate-950 hover:bg-slate-800">
                          <Plus className="mr-2 h-4 w-4" />
                          Quick Finding
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-3xl rounded-[28px]">
                        <DialogHeader>
                          <DialogTitle>Catat Field Finding</DialogTitle>
                        </DialogHeader>
                        <form onSubmit={handleCreateFinding} className="grid gap-4 md:grid-cols-2">
                          <div className="space-y-2">
                            <Label>Survey</Label>
                            <Select value={findingForm.survey_id} onValueChange={(value) => setFindingForm({ ...findingForm, survey_id: value })}>
                              <SelectTrigger className="h-12 rounded-[16px]"><SelectValue /></SelectTrigger>
                              <SelectContent>
                                <SelectItem value="quick">Quick report tanpa survey</SelectItem>
                                {surveys.map((survey) => <SelectItem key={survey.id} value={survey.id}>{survey.survey_code} • {survey.survey_type}</SelectItem>)}
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="space-y-2">
                            <Label>Area</Label>
                            <Select value={findingForm.area_code} onValueChange={(value) => setFindingForm({ ...findingForm, area_code: value })}>
                              <SelectTrigger className="h-12 rounded-[16px]"><SelectValue placeholder="Pilih area" /></SelectTrigger>
                              <SelectContent>
                                {areas.map((area) => <SelectItem key={area.code} value={area.code}>{area.name}</SelectItem>)}
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="space-y-2">
                            <Label>Finding Type</Label>
                            <Select value={findingForm.finding_type} onValueChange={(value) => setFindingForm({ ...findingForm, finding_type: value })}>
                              <SelectTrigger className="h-12 rounded-[16px]"><SelectValue /></SelectTrigger>
                              <SelectContent>
                                {findingTypes.map((item) => <SelectItem key={item} value={item}>{item}</SelectItem>)}
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="space-y-2">
                            <Label>Severity</Label>
                            <Select value={findingForm.severity} onValueChange={(value) => setFindingForm({ ...findingForm, severity: value })}>
                              <SelectTrigger className="h-12 rounded-[16px]"><SelectValue /></SelectTrigger>
                              <SelectContent>
                                {severityLevels.map((item) => <SelectItem key={item} value={item}>{item}</SelectItem>)}
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="space-y-2 md:col-span-2">
                            <Label>Sub Location</Label>
                            <Input value={findingForm.sub_location} onChange={(event) => setFindingForm({ ...findingForm, sub_location: event.target.value })} required className="h-12 rounded-[16px]" />
                          </div>
                          <div className="space-y-2 md:col-span-2">
                            <Label>Description</Label>
                            <Textarea value={findingForm.description} onChange={(event) => setFindingForm({ ...findingForm, description: event.target.value })} required rows={4} className="rounded-[16px]" />
                          </div>
                          <div className="space-y-2">
                            <Label>Potential Consequence</Label>
                            <Textarea value={findingForm.potential_consequence} onChange={(event) => setFindingForm({ ...findingForm, potential_consequence: event.target.value })} rows={3} className="rounded-[16px]" />
                          </div>
                          <div className="space-y-2">
                            <Label>Immediate Action</Label>
                            <Textarea value={findingForm.immediate_action} onChange={(event) => setFindingForm({ ...findingForm, immediate_action: event.target.value })} rows={3} className="rounded-[16px]" />
                          </div>
                          <div className="space-y-2 md:col-span-2">
                            <Label>Recommendation</Label>
                            <Textarea value={findingForm.recommendation} onChange={(event) => setFindingForm({ ...findingForm, recommendation: event.target.value })} required rows={3} className="rounded-[16px]" />
                          </div>
                          <div className="space-y-2">
                            <Label>Deadline</Label>
                            <Input type="date" value={findingForm.deadline} onChange={(event) => setFindingForm({ ...findingForm, deadline: event.target.value })} className="h-12 rounded-[16px]" />
                          </div>
                          <div className="space-y-2">
                            <Label>Clause ID</Label>
                            <Input value={findingForm.related_clause_id} onChange={(event) => setFindingForm({ ...findingForm, related_clause_id: event.target.value })} className="h-12 rounded-[16px]" />
                          </div>
                          <div className="md:col-span-2">
                            <Button type="submit" className="h-12 w-full rounded-[18px] bg-indigo-700 hover:bg-indigo-800">Simpan Finding</Button>
                          </div>
                        </form>
                      </DialogContent>
                    </Dialog>
                  </>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {surveys.length === 0 ? (
                <div className="rounded-[22px] bg-slate-50 p-10 text-center text-slate-500">
                  Belum ada survey. Quick report tetap bisa digunakan untuk temuan ad-hoc.
                </div>
              ) : (
                surveys.map((survey) => (
                  <button
                    key={survey.id}
                    type="button"
                    onClick={() => setSelectedSurveyId(survey.id)}
                    className={`w-full rounded-[22px] border p-4 text-left transition ${
                      selectedSurveyId === survey.id
                        ? 'border-indigo-800 bg-indigo-950 text-white shadow-[0_24px_60px_rgba(49,46,129,0.22)]'
                        : 'border-slate-100 bg-slate-50/70 text-slate-950 hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <span className={`rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.16em] ${selectedSurveyId === survey.id ? 'bg-white text-indigo-950' : 'bg-slate-950 text-white'}`}>{survey.survey_code}</span>
                          <span className={`rounded-full px-2.5 py-1 text-[11px] font-semibold ${selectedSurveyId === survey.id ? 'bg-white/15 text-white' : 'bg-white text-slate-500'}`}>{survey.survey_type}</span>
                        </div>
                        <p className="mt-3 text-lg font-bold">{(survey.area_codes || []).map((code) => areaMap[code] || code).join(', ')}</p>
                        <p className={`mt-2 text-sm ${selectedSurveyId === survey.id ? 'text-indigo-100' : 'text-slate-600'}`}>{survey.actual_date}</p>
                      </div>
                      <p className={`text-xs font-bold uppercase tracking-[0.16em] ${selectedSurveyId === survey.id ? 'text-indigo-100' : 'text-slate-500'}`}>{survey.status}</p>
                    </div>
                  </button>
                ))
              )}
            </CardContent>
          </Card>

          <div className="space-y-5">
            <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
              <CardHeader>
                <CardTitle className="text-xl">Survey Detail</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {detailLoading ? (
                  <div className="rounded-[20px] bg-slate-50 p-6 text-sm text-slate-500">Memuat detail survey...</div>
                ) : !selectedSurvey ? (
                  <div className="rounded-[20px] bg-slate-50 p-6 text-sm text-slate-500">Pilih survey untuk melihat temuan patrol.</div>
                ) : (
                  <>
                    <div className="rounded-[22px] bg-slate-950 p-5 text-white">
                      <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-slate-300">{selectedSurvey.survey_code}</p>
                      <h3 className="mt-3 text-2xl font-extrabold">{selectedSurvey.survey_type}</h3>
                      <p className="mt-3 text-sm leading-6 text-slate-200">{(selectedSurvey.area_codes || []).map((code) => areaMap[code] || code).join(', ')} • {selectedSurvey.actual_date}</p>
                    </div>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <div className="rounded-[20px] bg-slate-50 px-4 py-3">
                        <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Status</p>
                        <p className="mt-2 font-semibold text-slate-950">{selectedSurvey.status}</p>
                      </div>
                      <div className="rounded-[20px] bg-slate-50 px-4 py-3">
                        <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Findings</p>
                        <p className="mt-2 font-semibold text-slate-950">{surveyFindings.length}</p>
                      </div>
                    </div>
                    {surveyFindings.length > 0 && (
                      <Button variant="outline" onClick={handleGenerateSurveyReport} className="rounded-[16px]">
                        <FileText className="mr-2 h-4 w-4" />
                        {generatingReport ? 'Generating...' : 'Download Report'}
                      </Button>
                    )}
                    {canWrite && selectedSurvey.status !== 'closed' && (
                      <Button variant="outline" onClick={handleCloseSurvey} className="rounded-[16px]">
                        <ShieldAlert className="mr-2 h-4 w-4" />
                        Close Survey
                      </Button>
                    )}
                  </>
                )}
              </CardContent>
            </Card>

            <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-xl">
                  <Siren className="h-5 w-5 text-rose-600" />
                  Area Dashboard
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {dashboard.length === 0 ? (
                  <div className="rounded-[20px] bg-slate-50 p-6 text-sm text-slate-500">Belum ada agregasi dashboard.</div>
                ) : (
                  dashboard.map((row) => (
                    <div key={row._id} className="rounded-[20px] bg-slate-50 px-4 py-3">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="font-semibold text-slate-950">{areaMap[row._id] || row._id}</p>
                          <p className="text-xs text-slate-500">{row.open_count} open • {row.overdue_count} overdue</p>
                        </div>
                        <p className="text-lg font-extrabold text-slate-950">{row.critical_count}</p>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-xl">
                  <AlertTriangle className="h-5 w-5 text-amber-600" />
                  Overdue Findings
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {overdue.length === 0 ? (
                  <div className="rounded-[20px] bg-slate-50 p-6 text-sm text-slate-500">Tidak ada finding overdue.</div>
                ) : (
                  overdue.slice(0, 8).map((item) => (
                    <div key={item.id} className="rounded-[18px] bg-slate-50 px-4 py-3 text-sm text-slate-700">
                      <div className="flex items-center justify-between gap-3">
                        <span>{item.finding_code}</span>
                        <span className="font-semibold">{item.deadline}</span>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>
        </section>

        <section className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
          <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
            <CardHeader>
              <CardTitle className="text-xl">Latest Findings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {findings.length === 0 ? (
                <div className="rounded-[22px] bg-slate-50 p-10 text-center text-slate-500">Belum ada finding tercatat.</div>
              ) : (
                findings.slice(0, 14).map((item) => (
                  <div key={item.id} className="rounded-[22px] border border-slate-100 bg-slate-50/80 p-4">
                    <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="rounded-full bg-slate-950 px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.16em] text-white">{item.finding_code}</span>
                          <span className={`rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.16em] ${severityTone[item.severity] || 'bg-slate-100 text-slate-700'}`}>{item.severity}</span>
                          <span className="rounded-full bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-500">{item.status}</span>
                        </div>
                        <h3 className="mt-3 text-base font-bold text-slate-950">{item.sub_location}</h3>
                        <p className="mt-2 text-sm leading-6 text-slate-600">{item.description}</p>
                        <div className="mt-3 flex flex-wrap gap-4 text-sm text-slate-600">
                          <span>{areaMap[item.area_code] || item.area_code}</span>
                          <span>{item.finding_type}</span>
                          <span>{item.deadline || '-'}</span>
                        </div>
                        {item.related_risk_id && (
                          <div className="mt-3 rounded-[18px] border border-emerald-200 bg-emerald-50 p-3 text-sm text-slate-700">
                            Linked to ERM risk item: <span className="font-semibold">{item.related_risk_id}</span>
                          </div>
                        )}
                        <div className="mt-4 rounded-[18px] border border-dashed border-slate-200 bg-white/80 p-4">
                          <div className="flex flex-wrap items-center justify-between gap-3">
                            <div>
                              <p className="text-sm font-semibold text-slate-950">Photo Evidence</p>
                              <p className="text-xs text-slate-500">Lampirkan foto lapangan untuk finding ini.</p>
                            </div>
                            {canWrite && (
                              <div>
                                <input
                                  id={`field-photo-${item.id}`}
                                  type="file"
                                  accept="image/*,.pdf"
                                  className="hidden"
                                  onChange={(event) => {
                                    const file = event.target.files?.[0];
                                    handleUploadFindingPhoto(item.id, file);
                                    event.target.value = '';
                                  }}
                                />
                                <Button asChild variant="outline" className="rounded-[14px]">
                                  <label htmlFor={`field-photo-${item.id}`} className="cursor-pointer">
                                    <ImagePlus className="mr-2 h-4 w-4" />
                                    {uploadingFindingId === item.id ? 'Uploading...' : 'Upload'}
                                  </label>
                                </Button>
                              </div>
                            )}
                          </div>
                          <div className="mt-3 space-y-2">
                            {(photoMap[item.id] || []).length === 0 ? (
                              <p className="text-xs text-slate-500">Belum ada attachment.</p>
                            ) : (
                              (photoMap[item.id] || []).map((photo) => (
                                <div key={photo.id} className="flex flex-wrap items-center justify-between gap-3 rounded-[14px] bg-slate-50 px-3 py-2">
                                  <div className="min-w-0">
                                    <p className="truncate text-sm font-medium text-slate-950">{photo.filename}</p>
                                    <p className="text-xs text-slate-500">{Math.round((photo.size || 0) / 1024)} KB</p>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <Button type="button" size="sm" variant="outline" className="rounded-[12px]" onClick={() => handleDownloadFindingPhoto(photo)}>
                                      <Download className="h-4 w-4" />
                                    </Button>
                                    {canWrite && (
                                      <Button
                                        type="button"
                                        size="sm"
                                        variant="outline"
                                        className="rounded-[12px]"
                                        disabled={deletingPhotoId === photo.id}
                                        onClick={() => handleDeleteFindingPhoto(photo.id)}
                                      >
                                        <Trash2 className="h-4 w-4" />
                                      </Button>
                                    )}
                                  </div>
                                </div>
                              ))
                            )}
                          </div>
                        </div>
                      </div>
                      {canWrite && item.status !== 'closed' && (
                        <Button variant="outline" onClick={() => handleCloseFinding(item.id)} className="rounded-[16px]">
                          <Sparkles className="mr-2 h-4 w-4" />
                          Close
                        </Button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
            <CardHeader>
              <CardTitle className="text-xl">Survey Findings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {surveyFindings.length === 0 ? (
                <div className="rounded-[20px] bg-slate-50 p-6 text-sm text-slate-500">Belum ada finding pada survey yang dipilih.</div>
              ) : (
                surveyFindings.map((item) => (
                  <div key={item.id} className="rounded-[20px] bg-slate-50 px-4 py-3">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="font-semibold text-slate-950">{item.finding_code}</p>
                        <p className="text-xs text-slate-500">{item.sub_location}</p>
                      </div>
                      <span className={`rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.16em] ${severityTone[item.severity] || 'bg-slate-100 text-slate-700'}`}>{item.severity}</span>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </section>
      </div>
    </Layout>
  );
};

export default FieldSurveyPage;
