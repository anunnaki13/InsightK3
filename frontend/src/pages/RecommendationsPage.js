import React, { useState, useEffect, useContext } from 'react';
import { AppContext } from '../App';
import axios from 'axios';
import Layout from '../components/Layout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertCircle, Calendar, CheckCircle, Clock, Plus, Sparkles } from 'lucide-react';
import { toast } from 'sonner';

const RecommendationsPage = () => {
  const { API, user } = useContext(AppContext);
  const [recommendations, setRecommendations] = useState([]);
  const [clauses, setClauses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    clause_id: '',
    recommendation_text: '',
    deadline: ''
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [recsRes, clausesRes] = await Promise.all([
        axios.get(`${API}/recommendations`),
        axios.get(`${API}/clauses`)
      ]);
      setRecommendations(recsRes.data);
      setClauses(clausesRes.data);
    } catch (error) {
      toast.error('Gagal memuat data');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/recommendations`, formData);
      toast.success('Rekomendasi berhasil ditambahkan');
      setDialogOpen(false);
      setFormData({ clause_id: '', recommendation_text: '', deadline: '' });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal menambahkan rekomendasi');
    }
  };

  const handleUpdateStatus = async (recId, newStatus) => {
    try {
      const updateData = {
        status: newStatus,
        completed_at: newStatus === 'completed' ? new Date().toISOString() : null
      };
      await axios.put(`${API}/recommendations/${recId}`, updateData);
      toast.success('Status berhasil diperbarui');
      fetchData();
    } catch (error) {
      toast.error('Gagal memperbarui status');
    }
  };

  const getClauseName = (clauseId) => {
    const clause = clauses.find((item) => item.id === clauseId);
    return clause ? `${clause.clause_number}: ${clause.title}` : 'Unknown';
  };

  const getStatusBadge = (status) => {
    const config = {
      pending: { label: 'Pending', className: 'bg-amber-500', icon: Clock },
      in_progress: { label: 'Dikerjakan', className: 'bg-sky-600', icon: AlertCircle },
      completed: { label: 'Selesai', className: 'bg-emerald-600', icon: CheckCircle }
    };
    const { label, className, icon: Icon } = config[status] || config.pending;

    return (
      <Badge className={`${className} rounded-full px-2.5 py-1 text-white`}>
        <Icon className="mr-1 h-3 w-3" />
        {label}
      </Badge>
    );
  };

  const getDaysLeft = (deadline) => {
    const now = new Date();
    const due = new Date(deadline);
    return Math.ceil((due - now) / (1000 * 60 * 60 * 24));
  };

  const filterRecommendations = (status) => {
    if (status === 'all') return recommendations;
    return recommendations.filter((recommendation) => recommendation.status === status);
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
      <div className="space-y-6" data-testid="recommendations-page">
        <section className="grid gap-5 xl:grid-cols-[1.25fr_0.95fr]">
          <Card className="overflow-hidden rounded-[30px] border-0 bg-[linear-gradient(135deg,#25331d_0%,#39512d_58%,#4f6f3e_100%)] text-white shadow-[0_32px_90px_rgba(37,51,29,0.24)]">
            <CardContent className="p-7 md:p-8">
              <p className="text-[11px] font-bold uppercase tracking-[0.28em] text-lime-100/75">Action Tracking</p>
              <h1 className="mt-3 text-4xl font-extrabold leading-tight md:text-5xl">Ubah hasil audit menjadi tindak lanjut yang bisa dipantau dan ditutup dengan disiplin.</h1>
              <p className="mt-4 max-w-2xl text-sm leading-6 text-lime-50/80 md:text-base">
                Halaman ini menjadi jembatan antara temuan, rekomendasi auditor, deadline, dan bukti penyelesaian yang perlu dikelola dengan ritme operasional.
              </p>
            </CardContent>
          </Card>

          <Card className="rounded-[30px] border-white/70 bg-white/80 shadow-[0_24px_70px_rgba(45,68,58,0.10)] backdrop-blur-xl">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
                <div className="rounded-[20px] bg-slate-50 px-4 py-3">
                  <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Total</p>
                  <p className="mt-2 text-3xl font-extrabold text-slate-950">{recommendations.length}</p>
                </div>
                <div className="rounded-[20px] bg-amber-50 px-4 py-3">
                  <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-amber-700">Open Items</p>
                  <p className="mt-2 text-3xl font-extrabold text-amber-800">
                    {filterRecommendations('pending').length + filterRecommendations('in_progress').length}
                  </p>
                </div>
                <div className="rounded-[20px] bg-emerald-50 px-4 py-3">
                  <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-emerald-700">Closed</p>
                  <p className="mt-2 text-3xl font-extrabold text-emerald-800">{filterRecommendations('completed').length}</p>
                </div>
              </div>

              {user?.role === 'auditor' && (
                <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                  <DialogTrigger asChild>
                    <Button className="h-12 rounded-[18px] bg-slate-950 hover:bg-slate-800" data-testid="add-recommendation-button">
                      <Plus className="mr-2 h-4 w-4" />
                      Tambah Rekomendasi
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="rounded-[28px]" data-testid="add-recommendation-dialog">
                    <DialogHeader>
                      <DialogTitle>Tambah Rekomendasi Baru</DialogTitle>
                    </DialogHeader>
                    <form onSubmit={handleSubmit} className="space-y-4">
                      <div className="space-y-2">
                        <Label htmlFor="clause">Klausul</Label>
                        <Select
                          value={formData.clause_id}
                          onValueChange={(value) => setFormData({ ...formData, clause_id: value })}
                          required
                        >
                          <SelectTrigger className="h-12 rounded-[16px]" data-testid="recommendation-clause-select">
                            <SelectValue placeholder="Pilih klausul" />
                          </SelectTrigger>
                          <SelectContent>
                            {clauses.map((clause) => (
                              <SelectItem key={clause.id} value={clause.id}>{clause.clause_number}: {clause.title}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="recommendation_text">Rekomendasi</Label>
                        <Textarea
                          id="recommendation_text"
                          data-testid="recommendation-text-input"
                          placeholder="Tuliskan rekomendasi perbaikan..."
                          value={formData.recommendation_text}
                          onChange={(e) => setFormData({ ...formData, recommendation_text: e.target.value })}
                          required
                          rows={4}
                          className="rounded-[16px]"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="deadline">Deadline</Label>
                        <Input
                          id="deadline"
                          data-testid="recommendation-deadline-input"
                          type="date"
                          value={formData.deadline}
                          onChange={(e) => setFormData({ ...formData, deadline: e.target.value })}
                          required
                          className="h-12 rounded-[16px]"
                        />
                      </div>
                      <Button type="submit" className="h-12 w-full rounded-[18px] bg-emerald-700 hover:bg-emerald-800" data-testid="submit-recommendation-button">
                        Simpan
                      </Button>
                    </form>
                  </DialogContent>
                </Dialog>
              )}
            </CardContent>
          </Card>
        </section>

        <Tabs defaultValue="all" className="space-y-4">
          <TabsList className="h-auto flex-wrap rounded-[20px] bg-slate-100 p-1.5">
            <TabsTrigger value="all" className="rounded-[14px]" data-testid="tab-all">Semua ({recommendations.length})</TabsTrigger>
            <TabsTrigger value="pending" className="rounded-[14px]" data-testid="tab-pending">Pending ({filterRecommendations('pending').length})</TabsTrigger>
            <TabsTrigger value="in_progress" className="rounded-[14px]" data-testid="tab-in-progress">Dikerjakan ({filterRecommendations('in_progress').length})</TabsTrigger>
            <TabsTrigger value="completed" className="rounded-[14px]" data-testid="tab-completed">Selesai ({filterRecommendations('completed').length})</TabsTrigger>
          </TabsList>

          {['all', 'pending', 'in_progress', 'completed'].map((tab) => (
            <TabsContent key={tab} value={tab} className="space-y-4">
              {filterRecommendations(tab).length === 0 ? (
                <Card className="rounded-[28px] border-white/70 bg-white/80">
                  <CardContent className="py-14 text-center">
                    <Calendar className="mx-auto mb-4 h-12 w-12 text-slate-300" />
                    <p className="text-slate-600">Belum ada rekomendasi</p>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
                  {filterRecommendations(tab).map((rec) => {
                    const daysLeft = getDaysLeft(rec.deadline);
                    const isOverdue = daysLeft < 0 && rec.status !== 'completed';
                    const isUrgent = daysLeft <= 3 && daysLeft >= 0 && rec.status !== 'completed';

                    return (
                      <Card
                        key={rec.id}
                        className={`rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)] ${
                          isOverdue ? 'ring-1 ring-rose-300' : isUrgent ? 'ring-1 ring-amber-300' : ''
                        }`}
                        data-testid="recommendation-card"
                      >
                        <CardHeader className="pb-3">
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <CardTitle className="text-lg leading-7">{getClauseName(rec.clause_id)}</CardTitle>
                              <div className="mt-3">{getStatusBadge(rec.status)}</div>
                            </div>
                            <div className="flex h-11 w-11 items-center justify-center rounded-[16px] bg-slate-50 text-slate-600">
                              <Sparkles className="h-4 w-4" />
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent className="space-y-4">
                          <div className="rounded-[20px] bg-slate-50 p-4">
                            <p className="text-sm leading-6 text-slate-700">{rec.recommendation_text}</p>
                          </div>

                          <div className="flex items-center gap-2 text-sm">
                            <Calendar className="h-4 w-4 text-slate-400" />
                            <span className={`${
                              isOverdue ? 'font-medium text-rose-600' :
                              isUrgent ? 'font-medium text-amber-600' :
                              'text-slate-600'
                            }`}>
                              Deadline: {new Date(rec.deadline).toLocaleDateString('id-ID')}
                              {rec.status !== 'completed' && (
                                <span className="ml-2">
                                  ({isOverdue ? `Terlambat ${Math.abs(daysLeft)} hari` : `${daysLeft} hari lagi`})
                                </span>
                              )}
                            </span>
                          </div>

                          {rec.status !== 'completed' && (
                            <div className="flex gap-2">
                              {rec.status === 'pending' && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleUpdateStatus(rec.id, 'in_progress')}
                                  className="h-10 flex-1 rounded-[16px]"
                                  data-testid="start-button"
                                >
                                  Mulai Kerjakan
                                </Button>
                              )}
                              {rec.status === 'in_progress' && (
                                <Button
                                  size="sm"
                                  onClick={() => handleUpdateStatus(rec.id, 'completed')}
                                  className="h-10 flex-1 rounded-[16px] bg-emerald-700 hover:bg-emerald-800"
                                  data-testid="complete-button"
                                >
                                  <CheckCircle className="mr-2 h-4 w-4" />
                                  Tandai Selesai
                                </Button>
                              )}
                            </div>
                          )}

                          {rec.completed_at && (
                            <p className="text-xs font-medium text-emerald-700">
                              Diselesaikan: {new Date(rec.completed_at).toLocaleDateString('id-ID')}
                            </p>
                          )}
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              )}
            </TabsContent>
          ))}
        </Tabs>
      </div>
    </Layout>
  );
};

export default RecommendationsPage;
