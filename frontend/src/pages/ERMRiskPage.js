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
import { AlertTriangle, CalendarClock, Plus, RefreshCcw, ShieldAlert, Sparkles, Wand2 } from 'lucide-react';
import { toast } from 'sonner';

const emptyForm = {
  title: '',
  description: '',
  area_code: '',
  risk_category: '',
  likelihood: '3',
  impact: '3',
  residual_likelihood: '3',
  residual_impact: '3',
  target_date: '',
};

const emptyFilters = {
  area_code: 'all',
  category: 'all',
  risk_rating: 'all',
  status: 'all',
};

const ratingTone = {
  Critical: 'bg-rose-100 text-rose-700',
  High: 'bg-amber-100 text-amber-700',
  Medium: 'bg-sky-100 text-sky-700',
  Low: 'bg-emerald-100 text-emerald-700',
  'Very Low': 'bg-emerald-100 text-emerald-700',
};

const ERMRiskPage = () => {
  const { API, user } = useContext(AppContext);
  const [items, setItems] = useState([]);
  const [areas, setAreas] = useState([]);
  const [categories, setCategories] = useState([]);
  const [areaSummary, setAreaSummary] = useState([]);
  const [matrix, setMatrix] = useState([]);
  const [historyItems, setHistoryItems] = useState([]);
  const [selectedRiskId, setSelectedRiskId] = useState(null);
  const [filters, setFilters] = useState(emptyFilters);
  const [loading, setLoading] = useState(true);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState(emptyForm);
  const [aiLoadingId, setAiLoadingId] = useState(null);

  const canWrite = ['admin', 'auditor', 'risk_officer'].includes(user?.role);

  useEffect(() => {
    fetchReferenceData();
  }, []);

  useEffect(() => {
    if (areas.length > 0) {
      fetchRegisterData();
    }
  }, [areas, filters]);

  useEffect(() => {
    if (selectedRiskId) {
      fetchRiskHistory(selectedRiskId);
    }
  }, [selectedRiskId]);

  const areaMap = useMemo(
    () => Object.fromEntries(areas.map((area) => [area.code, area.name])),
    [areas],
  );

  const metrics = useMemo(() => {
    const critical = items.filter((item) => item.risk_rating === 'Critical').length;
    const high = items.filter((item) => item.risk_rating === 'High').length;
    const active = items.filter((item) => item.status !== 'Archived').length;
    return { total: items.length, critical, high, active };
  }, [items]);

  const selectedRisk = useMemo(
    () => items.find((item) => item.id === selectedRiskId) || items[0] || null,
    [items, selectedRiskId],
  );

  useEffect(() => {
    if (!selectedRiskId && items[0]?.id) {
      setSelectedRiskId(items[0].id);
      return;
    }

    if (selectedRiskId && !items.some((item) => item.id === selectedRiskId)) {
      setSelectedRiskId(items[0]?.id || null);
    }
  }, [items, selectedRiskId]);

  const fetchReferenceData = async () => {
    setLoading(true);
    try {
      const [areasRes, categoriesRes] = await Promise.all([
        axios.get(`${API}/risk/areas`),
        axios.get(`${API}/risk/categories`),
      ]);
      setAreas(areasRes.data || []);
      setCategories(categoriesRes.data || []);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal memuat referensi ERM Risk Register');
      setLoading(false);
    }
  };

  const fetchRegisterData = async () => {
    try {
      const params = new URLSearchParams({ limit: '100' });
      if (filters.area_code !== 'all') params.set('area_code', filters.area_code);
      if (filters.category !== 'all') params.set('category', filters.category);
      if (filters.risk_rating !== 'all') params.set('risk_rating', filters.risk_rating);
      if (filters.status !== 'all') params.set('status', filters.status);

      const [itemsRes, byAreaRes, matrixRes] = await Promise.all([
        axios.get(`${API}/risk/items?${params.toString()}`),
        axios.get(`${API}/risk/by-area`),
        axios.get(`${API}/risk/matrix`),
      ]);

      setItems(itemsRes.data.items || []);
      setAreaSummary(byAreaRes.data.areas || []);
      setMatrix(matrixRes.data.cells || []);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal memuat register ERM');
    } finally {
      setLoading(false);
    }
  };

  const fetchRiskHistory = async (riskId) => {
    setHistoryLoading(true);
    try {
      const response = await axios.get(`${API}/risk/items/${riskId}/history`);
      setHistoryItems(response.data.items || []);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal memuat histori risk item');
    } finally {
      setHistoryLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/risk/items`, {
        ...formData,
        likelihood: Number(formData.likelihood),
        impact: Number(formData.impact),
        residual_likelihood: Number(formData.residual_likelihood),
        residual_impact: Number(formData.residual_impact),
        target_date: formData.target_date || null,
      });
      toast.success('Risk item berhasil ditambahkan');
      setDialogOpen(false);
      setFormData(emptyForm);
      fetchRegisterData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal menambahkan risk item');
    }
  };

  const handleAiAssess = async (riskId) => {
    setAiLoadingId(riskId);
    try {
      await axios.post(`${API}/risk/items/${riskId}/ai-assess`);
      toast.success('AI assessment selesai');
      fetchRegisterData();
      if (riskId === selectedRiskId) {
        fetchRiskHistory(riskId);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal menjalankan AI assessment');
    } finally {
      setAiLoadingId(null);
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

  return (
    <Layout>
      <div className="space-y-6" data-testid="erm-risk-page">
        <section className="grid gap-5 xl:grid-cols-[1.25fr_0.95fr]">
          <Card className="overflow-hidden rounded-[30px] border-0 bg-[linear-gradient(135deg,#3a1c1c_0%,#63332b_58%,#87514a_100%)] text-white shadow-[0_32px_90px_rgba(58,28,28,0.24)]">
            <CardContent className="p-7 md:p-8">
              <p className="text-[11px] font-bold uppercase tracking-[0.28em] text-rose-100/75">ERM Risk Register</p>
              <h1 className="mt-3 text-4xl font-extrabold leading-tight md:text-5xl">Mulai memusatkan risk register operasional di dalam InsightK3.</h1>
              <p className="mt-4 max-w-2xl text-sm leading-6 text-rose-50/80 md:text-base">
                Fondasi modul A sudah aktif: master area, scoring risiko, AI-assisted assessment, agregasi per area, dan register risiko dasar.
              </p>
            </CardContent>
          </Card>

          <Card className="rounded-[30px] border-white/70 bg-white/80 shadow-[0_24px_70px_rgba(45,68,58,0.10)] backdrop-blur-xl">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Register Snapshot</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3 sm:grid-cols-2 xl:grid-cols-2">
              <div className="rounded-[20px] bg-slate-50 px-4 py-3">
                <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Total</p>
                <p className="mt-2 text-3xl font-extrabold text-slate-950">{metrics.total}</p>
              </div>
              <div className="rounded-[20px] bg-rose-50 px-4 py-3">
                <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-rose-700">Critical</p>
                <p className="mt-2 text-3xl font-extrabold text-rose-800">{metrics.critical}</p>
              </div>
              <div className="rounded-[20px] bg-amber-50 px-4 py-3">
                <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-amber-700">High</p>
                <p className="mt-2 text-3xl font-extrabold text-amber-800">{metrics.high}</p>
              </div>
              <div className="rounded-[20px] bg-emerald-50 px-4 py-3">
                <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-emerald-700">Active</p>
                <p className="mt-2 text-3xl font-extrabold text-emerald-800">{metrics.active}</p>
              </div>
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
          <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
            <CardHeader className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <CardTitle className="text-xl">Risk Register Workspace</CardTitle>
                <p className="mt-1 text-sm text-slate-600">Filter operasional untuk memilah register aktif dengan cepat.</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button variant="outline" className="rounded-[16px]" onClick={fetchRegisterData}>
                  <RefreshCcw className="mr-2 h-4 w-4" />
                  Refresh
                </Button>
                {canWrite && (
                  <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                    <DialogTrigger asChild>
                      <Button className="rounded-[16px] bg-slate-950 hover:bg-slate-800">
                        <Plus className="mr-2 h-4 w-4" />
                        Tambah Risk Item
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-2xl rounded-[28px]">
                      <DialogHeader>
                        <DialogTitle>Tambah Risk Item</DialogTitle>
                      </DialogHeader>
                      <form onSubmit={handleCreate} className="grid gap-4 md:grid-cols-2">
                        <div className="space-y-2 md:col-span-2">
                          <Label>Judul Risiko</Label>
                          <Input value={formData.title} onChange={(e) => setFormData({ ...formData, title: e.target.value })} required className="h-12 rounded-[16px]" />
                        </div>
                        <div className="space-y-2 md:col-span-2">
                          <Label>Deskripsi</Label>
                          <Textarea value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} required rows={4} className="rounded-[16px]" />
                        </div>
                        <div className="space-y-2">
                          <Label>Area</Label>
                          <Select value={formData.area_code} onValueChange={(value) => setFormData({ ...formData, area_code: value })}>
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
                          <Label>Kategori Risiko</Label>
                          <Select value={formData.risk_category} onValueChange={(value) => setFormData({ ...formData, risk_category: value })}>
                            <SelectTrigger className="h-12 rounded-[16px]">
                              <SelectValue placeholder="Pilih kategori" />
                            </SelectTrigger>
                            <SelectContent>
                              {categories.map((category) => (
                                <SelectItem key={category} value={category}>{category}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-2">
                          <Label>Likelihood</Label>
                          <Input type="number" min="1" max="5" value={formData.likelihood} onChange={(e) => setFormData({ ...formData, likelihood: e.target.value })} className="h-12 rounded-[16px]" />
                        </div>
                        <div className="space-y-2">
                          <Label>Impact</Label>
                          <Input type="number" min="1" max="5" value={formData.impact} onChange={(e) => setFormData({ ...formData, impact: e.target.value })} className="h-12 rounded-[16px]" />
                        </div>
                        <div className="space-y-2">
                          <Label>Residual Likelihood</Label>
                          <Input type="number" min="1" max="5" value={formData.residual_likelihood} onChange={(e) => setFormData({ ...formData, residual_likelihood: e.target.value })} className="h-12 rounded-[16px]" />
                        </div>
                        <div className="space-y-2">
                          <Label>Residual Impact</Label>
                          <Input type="number" min="1" max="5" value={formData.residual_impact} onChange={(e) => setFormData({ ...formData, residual_impact: e.target.value })} className="h-12 rounded-[16px]" />
                        </div>
                        <div className="space-y-2 md:col-span-2">
                          <Label>Target Date</Label>
                          <Input type="date" value={formData.target_date} onChange={(e) => setFormData({ ...formData, target_date: e.target.value })} className="h-12 rounded-[16px]" />
                        </div>
                        <div className="md:col-span-2">
                          <Button type="submit" className="h-12 w-full rounded-[18px] bg-emerald-700 hover:bg-emerald-800">
                            Simpan Risk Item
                          </Button>
                        </div>
                      </form>
                    </DialogContent>
                  </Dialog>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                <div className="space-y-2">
                  <Label>Area</Label>
                  <Select value={filters.area_code} onValueChange={(value) => setFilters({ ...filters, area_code: value })}>
                    <SelectTrigger className="h-11 rounded-[16px] bg-slate-50">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Semua area</SelectItem>
                      {areas.map((area) => (
                        <SelectItem key={area.code} value={area.code}>{area.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Kategori</Label>
                  <Select value={filters.category} onValueChange={(value) => setFilters({ ...filters, category: value })}>
                    <SelectTrigger className="h-11 rounded-[16px] bg-slate-50">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Semua kategori</SelectItem>
                      {categories.map((category) => (
                        <SelectItem key={category} value={category}>{category}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Risk Rating</Label>
                  <Select value={filters.risk_rating} onValueChange={(value) => setFilters({ ...filters, risk_rating: value })}>
                    <SelectTrigger className="h-11 rounded-[16px] bg-slate-50">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Semua rating</SelectItem>
                      {['Critical', 'High', 'Medium', 'Low', 'Very Low'].map((rating) => (
                        <SelectItem key={rating} value={rating}>{rating}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Status</Label>
                  <Select value={filters.status} onValueChange={(value) => setFilters({ ...filters, status: value })}>
                    <SelectTrigger className="h-11 rounded-[16px] bg-slate-50">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Semua status</SelectItem>
                      {['Active', 'Monitoring', 'Mitigated', 'Closed', 'Archived'].map((status) => (
                        <SelectItem key={status} value={status}>{status}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {items.length === 0 ? (
                <div className="rounded-[22px] bg-slate-50 p-10 text-center text-slate-500">
                  Belum ada risk item pada filter ini. Workspace ERM siap untuk input berikutnya.
                </div>
              ) : (
                <div className="space-y-3">
                  {items.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => setSelectedRiskId(item.id)}
                      className={`w-full rounded-[22px] border p-4 text-left transition ${
                        selectedRisk?.id === item.id
                          ? 'border-slate-900 bg-slate-950 text-white shadow-[0_24px_60px_rgba(15,23,42,0.22)]'
                          : 'border-slate-100 bg-slate-50/70 text-slate-950 hover:border-slate-300'
                      }`}
                    >
                      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className={`rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.16em] ${
                              selectedRisk?.id === item.id ? 'bg-white text-slate-950' : 'bg-slate-950 text-white'
                            }`}>
                              {item.risk_code}
                            </span>
                            <span className={`rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.16em] ${ratingTone[item.risk_rating] || 'bg-slate-100 text-slate-700'}`}>
                              {item.risk_rating}
                            </span>
                            <span className={`rounded-full px-2.5 py-1 text-[11px] font-semibold ${selectedRisk?.id === item.id ? 'bg-white/15 text-white' : 'bg-white text-slate-500'}`}>
                              {areaMap[item.area_code] || item.area_code}
                            </span>
                          </div>
                          <h3 className="mt-3 text-lg font-bold">{item.title}</h3>
                          <p className={`mt-2 text-sm leading-6 ${selectedRisk?.id === item.id ? 'text-slate-200' : 'text-slate-600'}`}>{item.description}</p>
                          <div className={`mt-3 flex flex-wrap gap-4 text-sm ${selectedRisk?.id === item.id ? 'text-slate-200' : 'text-slate-600'}`}>
                            <span>Score {item.risk_score}</span>
                            <span>Residual {item.residual_score}</span>
                            <span>{item.risk_category}</span>
                            <span>Status {item.status}</span>
                          </div>
                          {item.ai_suggestion && (
                            <div className={`mt-3 rounded-[18px] border p-3 text-sm ${
                              selectedRisk?.id === item.id
                                ? 'border-emerald-500/30 bg-emerald-500/10 text-slate-100'
                                : 'border-emerald-200 bg-emerald-50 text-slate-700'
                            }`}>
                              <div className={`mb-1 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] ${
                                selectedRisk?.id === item.id ? 'text-emerald-200' : 'text-emerald-700'
                              }`}>
                                <Sparkles className="h-3.5 w-3.5" />
                                AI Suggestion
                              </div>
                              {item.ai_suggestion}
                            </div>
                          )}
                        </div>
                        {canWrite && (
                          <Button
                            variant={selectedRisk?.id === item.id ? 'secondary' : 'outline'}
                            onClick={(event) => {
                              event.stopPropagation();
                              handleAiAssess(item.id);
                            }}
                            disabled={aiLoadingId === item.id}
                            className="rounded-[16px]"
                          >
                            <Wand2 className="mr-2 h-4 w-4" />
                            {aiLoadingId === item.id ? 'Assessing...' : 'AI Assess'}
                          </Button>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <div className="space-y-5">
            <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-xl">
                  <ShieldAlert className="h-5 w-5 text-rose-600" />
                  Risk Detail
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {!selectedRisk ? (
                  <div className="rounded-[20px] bg-slate-50 p-6 text-sm text-slate-500">Pilih risk item untuk melihat detail.</div>
                ) : (
                  <>
                    <div className="rounded-[22px] bg-slate-950 p-5 text-white">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="rounded-full bg-white px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.16em] text-slate-950">{selectedRisk.risk_code}</span>
                        <span className={`rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.16em] ${ratingTone[selectedRisk.risk_rating] || 'bg-slate-100 text-slate-700'}`}>
                          {selectedRisk.risk_rating}
                        </span>
                      </div>
                      <h3 className="mt-3 text-2xl font-extrabold">{selectedRisk.title}</h3>
                      <p className="mt-3 text-sm leading-6 text-slate-200">{selectedRisk.description}</p>
                    </div>

                    <div className="grid gap-3 sm:grid-cols-2">
                      <div className="rounded-[20px] bg-slate-50 px-4 py-3">
                        <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Area</p>
                        <p className="mt-2 font-semibold text-slate-950">{areaMap[selectedRisk.area_code] || selectedRisk.area_code}</p>
                      </div>
                      <div className="rounded-[20px] bg-slate-50 px-4 py-3">
                        <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Kategori</p>
                        <p className="mt-2 font-semibold text-slate-950">{selectedRisk.risk_category}</p>
                      </div>
                      <div className="rounded-[20px] bg-slate-50 px-4 py-3">
                        <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Initial</p>
                        <p className="mt-2 font-semibold text-slate-950">
                          L{selectedRisk.likelihood} x I{selectedRisk.impact} = {selectedRisk.risk_score}
                        </p>
                      </div>
                      <div className="rounded-[20px] bg-slate-50 px-4 py-3">
                        <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Residual</p>
                        <p className="mt-2 font-semibold text-slate-950">
                          L{selectedRisk.residual_likelihood} x I{selectedRisk.residual_impact} = {selectedRisk.residual_score}
                        </p>
                      </div>
                    </div>

                    <div className="rounded-[22px] border border-slate-100 bg-slate-50/80 p-4">
                      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                        <CalendarClock className="h-4 w-4" />
                        Timeline & Ownership
                      </div>
                      <div className="mt-3 space-y-2 text-sm text-slate-600">
                        <p>Status: <span className="font-semibold text-slate-950">{selectedRisk.status}</span></p>
                        <p>Created by: <span className="font-semibold text-slate-950">{selectedRisk.created_by || '-'}</span></p>
                        <p>Target date: <span className="font-semibold text-slate-950">{selectedRisk.target_date || '-'}</span></p>
                        <p>Review cycle: <span className="font-semibold text-slate-950">{selectedRisk.review_frequency_days} hari</span></p>
                      </div>
                    </div>

                    <div className="rounded-[22px] border border-slate-100 bg-white p-4">
                      <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                        <Sparkles className="h-4 w-4 text-emerald-600" />
                        Activity History
                      </div>
                      {historyLoading ? (
                        <div className="rounded-[18px] bg-slate-50 p-5 text-sm text-slate-500">Memuat histori...</div>
                      ) : historyItems.length === 0 ? (
                        <div className="rounded-[18px] bg-slate-50 p-5 text-sm text-slate-500">Belum ada histori perubahan untuk risk item ini.</div>
                      ) : (
                        <div className="space-y-3">
                          {historyItems.map((entry) => (
                            <div key={entry.id} className="rounded-[18px] bg-slate-50 px-4 py-3">
                              <p className="text-sm font-semibold text-slate-950">{entry.changes?.field || 'update'}</p>
                              <p className="mt-1 text-sm text-slate-600">
                                {entry.changes?.before ?? '-'} {'->'} {entry.changes?.after ?? '-'}
                              </p>
                              <p className="mt-2 text-xs text-slate-500">{entry.changed_at}</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </>
                )}
              </CardContent>
            </Card>

            <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
              <CardHeader>
                <CardTitle className="text-xl">By Area</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {areaSummary.length === 0 ? (
                  <div className="rounded-[20px] bg-slate-50 p-6 text-sm text-slate-500">Belum ada agregat area.</div>
                ) : (
                  areaSummary.map((row) => (
                    <div key={row.area_code} className="rounded-[20px] bg-slate-50 px-4 py-3">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="font-semibold text-slate-900">{areaMap[row.area_code] || row.area_code}</p>
                          <p className="text-xs text-slate-500">{row.count} item • {row.critical_count} critical</p>
                        </div>
                        <div className="text-right">
                          <p className="text-lg font-extrabold text-slate-950">{row.highest_score}</p>
                          <p className="text-xs text-slate-500">avg {row.average_score}</p>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-xl">
                  <AlertTriangle className="h-5 w-5 text-rose-600" />
                  Risk Matrix Snapshot
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {matrix.length === 0 ? (
                  <div className="rounded-[20px] bg-slate-50 p-6 text-sm text-slate-500">Belum ada data matrix.</div>
                ) : (
                  matrix.map((cell) => (
                    <div key={`${cell.likelihood}-${cell.impact}`} className="rounded-[18px] bg-slate-50 px-4 py-3 text-sm text-slate-700">
                      Likelihood {cell.likelihood} x Impact {cell.impact}: <span className="font-semibold">{cell.count}</span> item
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>
        </section>
      </div>
    </Layout>
  );
};

export default ERMRiskPage;
