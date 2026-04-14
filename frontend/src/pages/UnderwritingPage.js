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
import { Building2, CheckCircle2, ClipboardList, Download, FileText, ImagePlus, Plus, RefreshCcw, ShieldAlert, Sparkles, Trash2 } from 'lucide-react';
import { toast } from 'sonner';

const emptySurveyForm = {
  title: '',
  survey_type: 'renewal',
  insurance_company: '',
  policy_number: '',
  planned_date: '',
  area_code: '',
  lead_surveyor_id: '',
  surveyor_ids: '',
  insurance_rep_name: '',
  notes: '',
};

const surveyTypeLabel = {
  renewal: 'Renewal',
  new_policy: 'New Policy',
  mid_term: 'Mid Term',
  post_loss: 'Post Loss',
};

const gradeTone = {
  A: 'bg-emerald-100 text-emerald-700',
  B: 'bg-sky-100 text-sky-700',
  C: 'bg-amber-100 text-amber-700',
  D: 'bg-rose-100 text-rose-700',
};

const UnderwritingPage = () => {
  const { API, user } = useContext(AppContext);
  const [areas, setAreas] = useState([]);
  const [categories, setCategories] = useState([]);
  const [surveys, setSurveys] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [selectedSurveyId, setSelectedSurveyId] = useState(null);
  const [selectedSurvey, setSelectedSurvey] = useState(null);
  const [checklistItems, setChecklistItems] = useState([]);
  const [scoreBreakdown, setScoreBreakdown] = useState(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [surveyForm, setSurveyForm] = useState(emptySurveyForm);
  const [drafts, setDrafts] = useState({});
  const [savingItemId, setSavingItemId] = useState(null);
  const [photoMap, setPhotoMap] = useState({});
  const [uploadingItemId, setUploadingItemId] = useState(null);
  const [deletingPhotoId, setDeletingPhotoId] = useState(null);
  const [generatingReport, setGeneratingReport] = useState(false);

  const canManage = ['admin', 'risk_officer'].includes(user?.role);
  const canFill = ['admin', 'risk_officer', 'surveyor'].includes(user?.role);

  const areaMap = useMemo(
    () => Object.fromEntries(areas.map((area) => [area.code, area.name])),
    [areas],
  );

  const surveyMetrics = useMemo(() => ({
    total: surveys.length,
    completed: surveys.filter((survey) => survey.status === 'completed').length,
    submitted: surveys.filter((survey) => survey.status === 'submitted').length,
    inProgress: surveys.filter((survey) => survey.status === 'in_progress').length,
  }), [surveys]);

  useEffect(() => {
    fetchReferenceData();
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

  const fetchReferenceData = async () => {
    setLoading(true);
    try {
      const [areasRes, categoriesRes, templatesRes, surveysRes] = await Promise.all([
        axios.get(`${API}/risk/areas`),
        axios.get(`${API}/underwriting/categories`),
        axios.get(`${API}/underwriting/checklist-templates`),
        axios.get(`${API}/underwriting/surveys?limit=100`),
      ]);
      setAreas(areasRes.data || []);
      setCategories(categoriesRes.data || []);
      setTemplates(templatesRes.data || []);
      setSurveys(surveysRes.data.items || []);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal memuat workspace underwriting');
    } finally {
      setLoading(false);
    }
  };

  const fetchSurveys = async () => {
    const response = await axios.get(`${API}/underwriting/surveys?limit=100`);
    setSurveys(response.data.items || []);
  };

  const fetchSurveyDetail = async (surveyId) => {
    setDetailLoading(true);
    try {
      const [detailRes, scoreRes] = await Promise.all([
        axios.get(`${API}/underwriting/surveys/${surveyId}`),
        axios.get(`${API}/underwriting/surveys/${surveyId}/score`),
      ]);
      setSelectedSurvey(detailRes.data.survey);
      setChecklistItems(detailRes.data.checklist_items || []);
      setScoreBreakdown(scoreRes.data);
      setDrafts(
        Object.fromEntries(
          (detailRes.data.checklist_items || []).map((item) => [
            item.id,
            {
              score: item.score?.toString() || '',
              finding: item.finding || '',
              recommendation: item.recommendation || '',
            },
          ]),
        ),
      );
      const items = detailRes.data.checklist_items || [];
      if (items.length > 0) {
        const photoEntries = await Promise.all(
          items.map(async (item) => {
            const response = await axios.get(`${API}/underwriting/checklist-items/${item.id}/photos`);
            return [item.id, response.data.items || []];
          }),
        );
        setPhotoMap(Object.fromEntries(photoEntries));
      } else {
        setPhotoMap({});
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal memuat detail underwriting survey');
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCreateSurvey = async (event) => {
    event.preventDefault();
    try {
      await axios.post(`${API}/underwriting/surveys`, {
        ...surveyForm,
        surveyor_ids: surveyForm.surveyor_ids
          .split(',')
          .map((item) => item.trim())
          .filter(Boolean),
      });
      toast.success('Underwriting survey berhasil dibuat');
      setDialogOpen(false);
      setSurveyForm(emptySurveyForm);
      fetchSurveys();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal membuat underwriting survey');
    }
  };

  const handleGenerateChecklist = async () => {
    if (!selectedSurveyId) return;
    try {
      await axios.post(`${API}/underwriting/surveys/${selectedSurveyId}/generate-checklist`);
      toast.success('Checklist underwriting berhasil dibuat');
      fetchSurveyDetail(selectedSurveyId);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal membuat checklist');
    }
  };

  const handleStartSurvey = async () => {
    if (!selectedSurveyId) return;
    try {
      await axios.post(`${API}/underwriting/surveys/${selectedSurveyId}/start`);
      toast.success('Survey dimulai');
      fetchSurveys();
      fetchSurveyDetail(selectedSurveyId);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal memulai survey');
    }
  };

  const handleCompleteSurvey = async () => {
    if (!selectedSurveyId) return;
    try {
      await axios.post(`${API}/underwriting/surveys/${selectedSurveyId}/complete`);
      toast.success('Survey diselesaikan');
      fetchSurveys();
      fetchSurveyDetail(selectedSurveyId);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal menyelesaikan survey');
    }
  };

  const handleSubmitSurvey = async () => {
    if (!selectedSurveyId) return;
    try {
      await axios.post(`${API}/underwriting/surveys/${selectedSurveyId}/submit`);
      toast.success('Survey disubmit');
      fetchSurveys();
      fetchSurveyDetail(selectedSurveyId);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal submit survey');
    }
  };

  const handleSaveChecklistItem = async (itemId) => {
    const draft = drafts[itemId];
    if (!draft) return;
    setSavingItemId(itemId);
    try {
      await axios.put(`${API}/underwriting/checklist-items/${itemId}`, {
        score: draft.score === '' ? null : Number(draft.score),
        finding: draft.finding || null,
        recommendation: draft.recommendation || null,
      });
      toast.success('Checklist item diperbarui');
      fetchSurveyDetail(selectedSurveyId);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal memperbarui checklist item');
    } finally {
      setSavingItemId(null);
    }
  };

  const handleUploadPhoto = async (itemId, file) => {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    setUploadingItemId(itemId);
    try {
      await axios.post(`${API}/underwriting/checklist-items/${itemId}/photos`, formData);
      toast.success('Foto underwriting berhasil diupload');
      fetchSurveyDetail(selectedSurveyId);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal upload foto underwriting');
    } finally {
      setUploadingItemId(null);
    }
  };

  const handleDownloadPhoto = async (photo) => {
    try {
      const response = await axios.get(`${API}/underwriting/files/${photo.id}/download`, {
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
      toast.error(error.response?.data?.detail || 'Gagal mengunduh foto underwriting');
    }
  };

  const handleDeletePhoto = async (photoId) => {
    setDeletingPhotoId(photoId);
    try {
      await axios.delete(`${API}/underwriting/files/${photoId}`);
      toast.success('Foto underwriting dihapus');
      fetchSurveyDetail(selectedSurveyId);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal menghapus foto underwriting');
    } finally {
      setDeletingPhotoId(null);
    }
  };

  const handleGenerateReport = async () => {
    if (!selectedSurveyId) return;
    setGeneratingReport(true);
    try {
      const response = await axios.post(`${API}/underwriting/surveys/${selectedSurveyId}/report`);
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
      toast.success('Report underwriting berhasil diunduh');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal membuat report underwriting');
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
      <div className="space-y-6" data-testid="underwriting-page">
        <section className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
          <Card className="overflow-hidden rounded-[30px] border-0 bg-[linear-gradient(135deg,#132a13_0%,#235347_58%,#2f6f6d_100%)] text-white shadow-[0_32px_90px_rgba(19,42,19,0.24)]">
            <CardContent className="p-7 md:p-8">
              <p className="text-[11px] font-bold uppercase tracking-[0.28em] text-emerald-100/75">Module B</p>
              <h1 className="mt-3 text-4xl font-extrabold leading-tight md:text-5xl">Underwriting survey sekarang sudah punya fondasi operasional.</h1>
              <p className="mt-4 max-w-2xl text-sm leading-6 text-emerald-50/80 md:text-base">
                Digitalisasi survey, generate checklist template, auto-scoring per kategori, dan integrasi awal ke ERM untuk temuan kritikal sudah aktif.
              </p>
            </CardContent>
          </Card>

          <Card className="rounded-[30px] border-white/70 bg-white/80 shadow-[0_24px_70px_rgba(45,68,58,0.10)] backdrop-blur-xl">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Survey Snapshot</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-[20px] bg-slate-50 px-4 py-3">
                <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Total</p>
                <p className="mt-2 text-3xl font-extrabold text-slate-950">{surveyMetrics.total}</p>
              </div>
              <div className="rounded-[20px] bg-sky-50 px-4 py-3">
                <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-sky-700">In Progress</p>
                <p className="mt-2 text-3xl font-extrabold text-sky-800">{surveyMetrics.inProgress}</p>
              </div>
              <div className="rounded-[20px] bg-emerald-50 px-4 py-3">
                <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-emerald-700">Completed</p>
                <p className="mt-2 text-3xl font-extrabold text-emerald-800">{surveyMetrics.completed}</p>
              </div>
              <div className="rounded-[20px] bg-amber-50 px-4 py-3">
                <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-amber-700">Submitted</p>
                <p className="mt-2 text-3xl font-extrabold text-amber-800">{surveyMetrics.submitted}</p>
              </div>
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
          <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
            <CardHeader className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <CardTitle className="text-xl">Survey List</CardTitle>
                <p className="mt-1 text-sm text-slate-600">Daftar underwriting survey yang sudah terdaftar di workspace.</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button variant="outline" className="rounded-[16px]" onClick={fetchSurveys}>
                  <RefreshCcw className="mr-2 h-4 w-4" />
                  Refresh
                </Button>
                {canManage && (
                  <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                    <DialogTrigger asChild>
                      <Button className="rounded-[16px] bg-slate-950 hover:bg-slate-800">
                        <Plus className="mr-2 h-4 w-4" />
                        Survey Baru
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-2xl rounded-[28px]">
                      <DialogHeader>
                        <DialogTitle>Buat Underwriting Survey</DialogTitle>
                      </DialogHeader>
                      <form onSubmit={handleCreateSurvey} className="grid gap-4 md:grid-cols-2">
                        <div className="space-y-2 md:col-span-2">
                          <Label>Judul Survey</Label>
                          <Input value={surveyForm.title} onChange={(event) => setSurveyForm({ ...surveyForm, title: event.target.value })} required className="h-12 rounded-[16px]" />
                        </div>
                        <div className="space-y-2">
                          <Label>Tipe Survey</Label>
                          <Select value={surveyForm.survey_type} onValueChange={(value) => setSurveyForm({ ...surveyForm, survey_type: value })}>
                            <SelectTrigger className="h-12 rounded-[16px]">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="renewal">Renewal</SelectItem>
                              <SelectItem value="new_policy">New Policy</SelectItem>
                              <SelectItem value="mid_term">Mid Term</SelectItem>
                              <SelectItem value="post_loss">Post Loss</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-2">
                          <Label>Area</Label>
                          <Select value={surveyForm.area_code} onValueChange={(value) => setSurveyForm({ ...surveyForm, area_code: value })}>
                            <SelectTrigger className="h-12 rounded-[16px]">
                              <SelectValue placeholder="Pilih area" />
                            </SelectTrigger>
                            <SelectContent>
                              {areas.map((area) => (
                                <SelectItem key={area.code} value={area.code}>{area.name}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-2">
                          <Label>Insurance Company</Label>
                          <Input value={surveyForm.insurance_company} onChange={(event) => setSurveyForm({ ...surveyForm, insurance_company: event.target.value })} required className="h-12 rounded-[16px]" />
                        </div>
                        <div className="space-y-2">
                          <Label>Policy Number</Label>
                          <Input value={surveyForm.policy_number} onChange={(event) => setSurveyForm({ ...surveyForm, policy_number: event.target.value })} className="h-12 rounded-[16px]" />
                        </div>
                        <div className="space-y-2">
                          <Label>Planned Date</Label>
                          <Input type="date" value={surveyForm.planned_date} onChange={(event) => setSurveyForm({ ...surveyForm, planned_date: event.target.value })} required className="h-12 rounded-[16px]" />
                        </div>
                        <div className="space-y-2">
                          <Label>Lead Surveyor ID</Label>
                          <Input value={surveyForm.lead_surveyor_id} onChange={(event) => setSurveyForm({ ...surveyForm, lead_surveyor_id: event.target.value })} required className="h-12 rounded-[16px]" />
                        </div>
                        <div className="space-y-2">
                          <Label>Surveyor IDs</Label>
                          <Input value={surveyForm.surveyor_ids} onChange={(event) => setSurveyForm({ ...surveyForm, surveyor_ids: event.target.value })} placeholder="pisahkan dengan koma" className="h-12 rounded-[16px]" />
                        </div>
                        <div className="space-y-2">
                          <Label>Insurance Representative</Label>
                          <Input value={surveyForm.insurance_rep_name} onChange={(event) => setSurveyForm({ ...surveyForm, insurance_rep_name: event.target.value })} className="h-12 rounded-[16px]" />
                        </div>
                        <div className="space-y-2 md:col-span-2">
                          <Label>Notes</Label>
                          <Textarea value={surveyForm.notes} onChange={(event) => setSurveyForm({ ...surveyForm, notes: event.target.value })} rows={4} className="rounded-[16px]" />
                        </div>
                        <div className="md:col-span-2">
                          <Button type="submit" className="h-12 w-full rounded-[18px] bg-emerald-700 hover:bg-emerald-800">
                            Simpan Survey
                          </Button>
                        </div>
                      </form>
                    </DialogContent>
                  </Dialog>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {surveys.length === 0 ? (
                <div className="rounded-[22px] bg-slate-50 p-10 text-center text-slate-500">
                  Belum ada underwriting survey. Modul ini siap menerima survey pertama.
                </div>
              ) : (
                surveys.map((survey) => (
                  <button
                    key={survey.id}
                    type="button"
                    onClick={() => setSelectedSurveyId(survey.id)}
                    className={`w-full rounded-[22px] border p-4 text-left transition ${
                      selectedSurveyId === survey.id
                        ? 'border-emerald-800 bg-emerald-950 text-white shadow-[0_24px_60px_rgba(6,78,59,0.22)]'
                        : 'border-slate-100 bg-slate-50/70 text-slate-950 hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className={`rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.16em] ${
                            selectedSurveyId === survey.id ? 'bg-white text-emerald-950' : 'bg-slate-950 text-white'
                          }`}>
                            {survey.survey_code}
                          </span>
                          <span className={`rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.16em] ${gradeTone[survey.risk_grade] || 'bg-slate-100 text-slate-600'}`}>
                            {survey.risk_grade || 'Draft'}
                          </span>
                        </div>
                        <h3 className="mt-3 text-lg font-bold">{survey.title}</h3>
                        <p className={`mt-2 text-sm ${selectedSurveyId === survey.id ? 'text-emerald-100' : 'text-slate-600'}`}>
                          {surveyTypeLabel[survey.survey_type] || survey.survey_type} • {areaMap[survey.area_code] || survey.area_code}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className={`text-xs font-semibold uppercase tracking-[0.16em] ${selectedSurveyId === survey.id ? 'text-emerald-100' : 'text-slate-500'}`}>
                          {survey.status}
                        </p>
                        <p className={`mt-2 text-lg font-extrabold ${selectedSurveyId === survey.id ? 'text-white' : 'text-slate-950'}`}>
                          {survey.overall_score ?? '-'}
                        </p>
                      </div>
                    </div>
                  </button>
                ))
              )}
            </CardContent>
          </Card>

          <div className="space-y-5">
            <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-xl">
                  <Building2 className="h-5 w-5 text-emerald-700" />
                  Survey Detail
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {detailLoading ? (
                  <div className="rounded-[20px] bg-slate-50 p-6 text-sm text-slate-500">Memuat detail survey...</div>
                ) : !selectedSurvey ? (
                  <div className="rounded-[20px] bg-slate-50 p-6 text-sm text-slate-500">Pilih survey untuk melihat detail underwriting.</div>
                ) : (
                  <>
                    <div className="rounded-[22px] bg-slate-950 p-5 text-white">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="rounded-full bg-white px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.16em] text-slate-950">{selectedSurvey.survey_code}</span>
                        <span className={`rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.16em] ${gradeTone[selectedSurvey.risk_grade] || 'bg-slate-100 text-slate-700'}`}>
                          {selectedSurvey.risk_grade || 'Draft'}
                        </span>
                      </div>
                      <h3 className="mt-3 text-2xl font-extrabold">{selectedSurvey.title}</h3>
                      <p className="mt-3 text-sm leading-6 text-slate-200">
                        {selectedSurvey.insurance_company} • {surveyTypeLabel[selectedSurvey.survey_type] || selectedSurvey.survey_type} • {areaMap[selectedSurvey.area_code] || selectedSurvey.area_code}
                      </p>
                    </div>

                    <div className="grid gap-3 sm:grid-cols-2">
                      <div className="rounded-[20px] bg-slate-50 px-4 py-3">
                        <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Status</p>
                        <p className="mt-2 font-semibold text-slate-950">{selectedSurvey.status}</p>
                      </div>
                      <div className="rounded-[20px] bg-slate-50 px-4 py-3">
                        <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Planned Date</p>
                        <p className="mt-2 font-semibold text-slate-950">{selectedSurvey.planned_date}</p>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      {selectedSurvey && checklistItems.length > 0 && (
                        <Button variant="outline" onClick={handleGenerateReport} className="rounded-[16px]">
                          <FileText className="mr-2 h-4 w-4" />
                          {generatingReport ? 'Generating...' : 'Download Report'}
                        </Button>
                      )}
                      {canManage && checklistItems.length === 0 && (
                        <Button onClick={handleGenerateChecklist} className="rounded-[16px] bg-slate-950 hover:bg-slate-800">
                          <ClipboardList className="mr-2 h-4 w-4" />
                          Generate Checklist
                        </Button>
                      )}
                      {canFill && selectedSurvey.status === 'planned' && (
                        <Button variant="outline" onClick={handleStartSurvey} className="rounded-[16px]">
                          <Sparkles className="mr-2 h-4 w-4" />
                          Start Survey
                        </Button>
                      )}
                      {canFill && checklistItems.length > 0 && selectedSurvey.status !== 'completed' && selectedSurvey.status !== 'submitted' && (
                        <Button variant="outline" onClick={handleCompleteSurvey} className="rounded-[16px]">
                          <CheckCircle2 className="mr-2 h-4 w-4" />
                          Complete Survey
                        </Button>
                      )}
                      {canManage && selectedSurvey.status === 'completed' && (
                        <Button variant="outline" onClick={handleSubmitSurvey} className="rounded-[16px]">
                          <ShieldAlert className="mr-2 h-4 w-4" />
                          Submit Survey
                        </Button>
                      )}
                    </div>
                  </>
                )}
              </CardContent>
            </Card>

            <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
              <CardHeader>
                <CardTitle className="text-xl">Score Breakdown</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {!scoreBreakdown ? (
                  <div className="rounded-[20px] bg-slate-50 p-6 text-sm text-slate-500">Belum ada data scoring.</div>
                ) : (
                  <>
                    <div className="grid gap-3 sm:grid-cols-3">
                      <div className="rounded-[20px] bg-slate-50 px-4 py-3">
                        <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Overall</p>
                        <p className="mt-2 text-2xl font-extrabold text-slate-950">{scoreBreakdown.overall_score}</p>
                      </div>
                      <div className="rounded-[20px] bg-slate-50 px-4 py-3">
                        <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Grade</p>
                        <p className="mt-2 text-2xl font-extrabold text-slate-950">{scoreBreakdown.risk_grade}</p>
                      </div>
                      <div className="rounded-[20px] bg-slate-50 px-4 py-3">
                        <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Critical</p>
                        <p className="mt-2 text-2xl font-extrabold text-slate-950">{scoreBreakdown.total_critical_findings}</p>
                      </div>
                    </div>
                    <div className="space-y-3">
                      {categories.map((category) => {
                        const score = scoreBreakdown.category_scores?.[category.code];
                        return (
                          <div key={category.code} className="rounded-[20px] bg-slate-50 px-4 py-3">
                            <div className="flex items-center justify-between gap-3">
                              <div>
                                <p className="font-semibold text-slate-950">{category.name}</p>
                                <p className="text-xs text-slate-500">{score?.items_assessed || 0}/{score?.total_items || 0} assessed • bobot {category.weight}</p>
                              </div>
                              <p className="text-lg font-extrabold text-slate-950">{score?.raw_score || 0}</p>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </div>
        </section>

        <section className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
          <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
            <CardHeader>
              <CardTitle className="text-xl">Checklist Workspace</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {checklistItems.length === 0 ? (
                <div className="rounded-[22px] bg-slate-50 p-10 text-center text-slate-500">
                  Checklist belum tersedia. Generate checklist terlebih dahulu dari template underwriting.
                </div>
              ) : (
                checklistItems.map((item) => (
                  <div key={item.id} className="rounded-[22px] border border-slate-100 bg-slate-50/80 p-4">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="rounded-full bg-slate-950 px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.16em] text-white">{item.item_code}</span>
                      <span className="rounded-full bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-500">{item.category_code}</span>
                      {item.is_critical && (
                        <span className="rounded-full bg-rose-100 px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.16em] text-rose-700">Critical</span>
                      )}
                    </div>
                    <h3 className="mt-3 text-base font-bold text-slate-950">{item.item_description}</h3>
                    <div className="mt-4 grid gap-3 md:grid-cols-[140px_1fr_1fr_auto]">
                      <div className="space-y-2">
                        <Label>Score</Label>
                        <Select
                          value={drafts[item.id]?.score || ''}
                          onValueChange={(value) => setDrafts({ ...drafts, [item.id]: { ...drafts[item.id], score: value } })}
                        >
                          <SelectTrigger className="h-11 rounded-[16px] bg-white">
                            <SelectValue placeholder="Score" />
                          </SelectTrigger>
                          <SelectContent>
                            {[0, 1, 2, 3, 4].map((value) => (
                              <SelectItem key={value} value={String(value)}>{value}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label>Finding</Label>
                        <Textarea
                          value={drafts[item.id]?.finding || ''}
                          onChange={(event) => setDrafts({ ...drafts, [item.id]: { ...drafts[item.id], finding: event.target.value } })}
                          rows={3}
                          className="rounded-[16px] bg-white"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Recommendation</Label>
                        <Textarea
                          value={drafts[item.id]?.recommendation || ''}
                          onChange={(event) => setDrafts({ ...drafts, [item.id]: { ...drafts[item.id], recommendation: event.target.value } })}
                          rows={3}
                          className="rounded-[16px] bg-white"
                        />
                      </div>
                      <div className="flex items-end">
                        <Button
                          onClick={() => handleSaveChecklistItem(item.id)}
                          disabled={!canFill || savingItemId === item.id}
                          className="h-11 rounded-[16px] bg-emerald-700 hover:bg-emerald-800"
                        >
                          {savingItemId === item.id ? 'Saving...' : 'Save'}
                        </Button>
                      </div>
                    </div>
                    <div className="mt-4 rounded-[18px] border border-dashed border-slate-200 bg-white/80 p-4">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <p className="text-sm font-semibold text-slate-950">Photo Evidence</p>
                          <p className="text-xs text-slate-500">Upload foto untuk item underwriting ini.</p>
                        </div>
                        {canFill && (
                          <div>
                            <input
                              id={`underwriting-photo-${item.id}`}
                              type="file"
                              accept="image/*,.pdf"
                              className="hidden"
                              onChange={(event) => {
                                const file = event.target.files?.[0];
                                handleUploadPhoto(item.id, file);
                                event.target.value = '';
                              }}
                            />
                            <Button asChild variant="outline" className="rounded-[14px]">
                              <label htmlFor={`underwriting-photo-${item.id}`} className="cursor-pointer">
                                <ImagePlus className="mr-2 h-4 w-4" />
                                {uploadingItemId === item.id ? 'Uploading...' : 'Upload'}
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
                                <Button type="button" size="sm" variant="outline" className="rounded-[12px]" onClick={() => handleDownloadPhoto(photo)}>
                                  <Download className="h-4 w-4" />
                                </Button>
                                {canFill && (
                                  <Button
                                    type="button"
                                    size="sm"
                                    variant="outline"
                                    className="rounded-[12px]"
                                    disabled={deletingPhotoId === photo.id}
                                    onClick={() => handleDeletePhoto(photo.id)}
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
                ))
              )}
            </CardContent>
          </Card>

          <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
            <CardHeader>
              <CardTitle className="text-xl">Template Coverage</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {categories.map((category) => {
                const count = templates.filter((item) => item.category_code === category.code).length;
                return (
                  <div key={category.code} className="rounded-[20px] bg-slate-50 px-4 py-3">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="font-semibold text-slate-950">{category.name}</p>
                        <p className="text-xs text-slate-500">{category.code}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-extrabold text-slate-950">{count}</p>
                        <p className="text-xs text-slate-500">template items</p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        </section>
      </div>
    </Layout>
  );
};

export default UnderwritingPage;
