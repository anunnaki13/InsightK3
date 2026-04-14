import React, { useContext, useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import { AppContext } from '../App';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Database, KeyRound, RefreshCw, Save, ShieldCheck, Sparkles } from 'lucide-react';
import { toast } from 'sonner';

const SettingsPage = () => {
  const { API, user } = useContext(AppContext);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [refreshingModels, setRefreshingModels] = useState(false);
  const [settings, setSettings] = useState(null);
  const [models, setModels] = useState([]);
  const [verification, setVerification] = useState(null);
  const [formData, setFormData] = useState({
    api_key: '',
    model: '',
  });

  useEffect(() => {
    fetchSettings();
  }, []);

  const availableModelIds = useMemo(() => models.map((item) => item.id), [models]);

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/settings/ai/openrouter`);
      setSettings(response.data);
      setFormData({
        api_key: '',
        model: response.data.model || '',
      });
      if (response.data.has_api_key) {
        await fetchModels();
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal memuat AI settings');
    } finally {
      setLoading(false);
    }
  };

  const fetchModels = async () => {
    setRefreshingModels(true);
    try {
      const response = await axios.get(`${API}/settings/ai/openrouter/models`);
      setModels(response.data.items || []);
    } catch (error) {
      setModels([]);
      toast.error(error.response?.data?.detail || 'Gagal memuat model OpenRouter');
    } finally {
      setRefreshingModels(false);
    }
  };

  const handleVerify = async () => {
    setVerifying(true);
    try {
      const response = await axios.post(`${API}/settings/ai/openrouter/verify`, {
        api_key: formData.api_key,
        model: formData.model,
      });
      setVerification(response.data);
      setModels(response.data.available_models || []);
      toast.success('OpenRouter credential berhasil diverifikasi');
    } catch (error) {
      setVerification(null);
      toast.error(error.response?.data?.detail || 'Verifikasi OpenRouter gagal');
    } finally {
      setVerifying(false);
    }
  };

  const handleSave = async (event) => {
    event.preventDefault();
    setSaving(true);
    try {
      const response = await axios.put(`${API}/settings/ai/openrouter`, formData);
      setSettings(response.data);
      setModels(response.data.available_models || models);
      setVerification(null);
      setFormData((current) => ({
        ...current,
        api_key: '',
        model: response.data.model || current.model,
      }));
      toast.success('AI settings berhasil disimpan');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal menyimpan AI settings');
    } finally {
      setSaving(false);
    }
  };

  if (user?.role !== 'admin') {
    return (
      <Layout>
        <div className="rounded-[28px] border border-rose-100 bg-rose-50/70 p-6 text-sm text-rose-700">
          Halaman ini hanya tersedia untuk admin.
        </div>
      </Layout>
    );
  }

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
      <div className="space-y-6" data-testid="settings-page">
        <section className="grid gap-5 xl:grid-cols-[1.2fr_0.9fr]">
          <Card className="overflow-hidden rounded-[30px] border-0 bg-[linear-gradient(135deg,#17344a_0%,#22556d_55%,#3b7f8c_100%)] text-white shadow-[0_32px_90px_rgba(23,52,74,0.24)]">
            <CardContent className="p-7 md:p-8">
              <p className="text-[11px] font-bold uppercase tracking-[0.28em] text-cyan-100/75">Admin Settings</p>
              <h1 className="mt-3 text-4xl font-extrabold leading-tight md:text-5xl">Kelola OpenRouter credential dan model AI aktif untuk InsightK3.</h1>
              <p className="mt-4 max-w-2xl text-sm leading-6 text-cyan-50/82 md:text-base">
                Konfigurasi ini dipakai oleh audit AI dan AI risk assessment. Credential diverifikasi ke OpenRouter sebelum disimpan.
              </p>
            </CardContent>
          </Card>

          <Card className="rounded-[30px] border-white/70 bg-white/80 shadow-[0_24px_70px_rgba(45,68,58,0.10)] backdrop-blur-xl">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Runtime Status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <div className="rounded-[24px] border border-slate-200 bg-slate-50/85 p-4">
                <div className="flex items-center gap-2 text-slate-900">
                  <ShieldCheck className="h-4 w-4 text-emerald-600" />
                  <span className="font-semibold">Provider: OpenRouter</span>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  <Badge variant="secondary" className="bg-emerald-50 text-emerald-700">
                    Source: {settings?.settings_source || 'unset'}
                  </Badge>
                  <Badge variant="secondary" className="bg-sky-50 text-sky-700">
                    {settings?.has_api_key ? 'API key tersedia' : 'API key belum diisi'}
                  </Badge>
                </div>
                <div className="mt-4 space-y-2 text-slate-600">
                  <p><span className="font-medium text-slate-900">Current key:</span> {settings?.masked_api_key || '-'}</p>
                  <p><span className="font-medium text-slate-900">Current model:</span> {settings?.model || '-'}</p>
                  <p><span className="font-medium text-slate-900">Key label:</span> {settings?.key_label || '-'}</p>
                  <p><span className="font-medium text-slate-900">Limit remaining:</span> {settings?.key_limit_remaining ?? '-'}</p>
                  <p><span className="font-medium text-slate-900">Usage:</span> {settings?.key_usage ?? '-'}</p>
                </div>
              </div>

              {verification && (
                <div className="rounded-[24px] border border-emerald-200 bg-emerald-50/80 p-4 text-slate-700">
                  <div className="flex items-center gap-2 font-semibold text-emerald-800">
                    <Sparkles className="h-4 w-4" />
                    Verifikasi berhasil
                  </div>
                  <p className="mt-2">Key: {verification.masked_api_key}</p>
                  <p>Label: {verification.key_info?.label || '-'}</p>
                  <p>Model ditemukan: {verification.model_exists === null ? 'tidak dicek' : verification.model_exists ? 'ya' : 'tidak'}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
          <Card className="rounded-[30px] border-white/70 bg-white/85 shadow-[0_24px_70px_rgba(45,68,58,0.10)] backdrop-blur-xl">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">OpenRouter Configuration</CardTitle>
            </CardHeader>
            <CardContent>
              <form className="space-y-5" onSubmit={handleSave}>
                <div className="space-y-2">
                  <Label htmlFor="api-key">API Key</Label>
                  <div className="relative">
                    <KeyRound className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                    <Input
                      id="api-key"
                      type="password"
                      className="pl-10"
                      placeholder={settings?.has_api_key ? 'Kosongkan untuk memakai key yang tersimpan saat ini' : 'sk-or-v1-...'}
                      value={formData.api_key}
                      onChange={(event) => setFormData((current) => ({ ...current, api_key: event.target.value }))}
                    />
                  </div>
                  <p className="text-xs text-slate-500">
                    Key baru akan diverifikasi ke OpenRouter sebelum disimpan. Jika field ini dikosongkan, aplikasi akan mempertahankan key yang sudah tersimpan.
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="model-name">Model</Label>
                  <div className="relative">
                    <Database className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                    <Input
                      id="model-name"
                      list="openrouter-models"
                      className="pl-10"
                      placeholder="google/gemini-2.0-flash-001"
                      value={formData.model}
                      onChange={(event) => setFormData((current) => ({ ...current, model: event.target.value }))}
                    />
                    <datalist id="openrouter-models">
                      {availableModelIds.map((modelId) => (
                        <option key={modelId} value={modelId} />
                      ))}
                    </datalist>
                  </div>
                  <p className="text-xs text-slate-500">
                    Model ini akan dipakai untuk seluruh fitur AI OpenRouter di InsightK3.
                  </p>
                </div>

                <div className="flex flex-wrap gap-3">
                  <Button type="button" className="rounded-2xl" variant="outline" onClick={handleVerify} disabled={verifying}>
                    <ShieldCheck className={`mr-2 h-4 w-4 ${verifying ? 'animate-pulse' : ''}`} />
                    {verifying ? 'Verifying...' : 'Verify Key'}
                  </Button>
                  <Button type="submit" className="rounded-2xl bg-emerald-700 hover:bg-emerald-800" disabled={saving}>
                    <Save className="mr-2 h-4 w-4" />
                    {saving ? 'Menyimpan...' : 'Simpan Setting'}
                  </Button>
                  <Button type="button" className="rounded-2xl" variant="outline" onClick={fetchModels} disabled={refreshingModels || !settings?.has_api_key}>
                    <RefreshCw className={`mr-2 h-4 w-4 ${refreshingModels ? 'animate-spin' : ''}`} />
                    Refresh Models
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          <Card className="rounded-[30px] border-white/70 bg-white/85 shadow-[0_24px_70px_rgba(45,68,58,0.10)] backdrop-blur-xl">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Available Models</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="rounded-[24px] border border-slate-200 bg-slate-50/75 p-4 text-xs text-slate-500">
                Daftar ini diambil dari endpoint resmi OpenRouter `/api/v1/models` menggunakan key yang sedang aktif.
              </div>
              <div className="mt-4 space-y-3">
                {models.length === 0 ? (
                  <div className="rounded-[24px] border border-dashed border-slate-200 bg-white/70 p-6 text-sm text-slate-500">
                    Belum ada model yang dimuat. Simpan atau verifikasi key dulu, lalu klik `Refresh Models`.
                  </div>
                ) : (
                  models.slice(0, 25).map((item) => (
                    <div key={item.id} className="rounded-[24px] border border-slate-200 bg-white/80 p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="font-semibold text-slate-900">{item.name || item.id}</p>
                          <p className="mt-1 text-xs text-slate-500">{item.id}</p>
                        </div>
                        <Button
                          type="button"
                          variant="outline"
                          className="h-8 rounded-xl px-3 text-xs"
                          onClick={() => setFormData((current) => ({ ...current, model: item.id }))}
                        >
                          Pakai
                        </Button>
                      </div>
                      <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-500">
                        <Badge variant="secondary" className="bg-slate-100 text-slate-700">
                          Context: {item.context_length || '-'}
                        </Badge>
                        <Badge variant="secondary" className="bg-slate-100 text-slate-700">
                          Prompt: {item.pricing?.prompt ?? '-'}
                        </Badge>
                        <Badge variant="secondary" className="bg-slate-100 text-slate-700">
                          Completion: {item.pricing?.completion ?? '-'}
                        </Badge>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </section>
      </div>
    </Layout>
  );
};

export default SettingsPage;
