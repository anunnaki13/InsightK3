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
import { Plus, Calendar, CheckCircle, Clock, AlertCircle } from 'lucide-react';
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
    const clause = clauses.find(c => c.id === clauseId);
    return clause ? `${clause.clause_number}: ${clause.title}` : 'Unknown';
  };

  const getStatusBadge = (status) => {
    const config = {
      pending: { label: 'Pending', color: 'bg-yellow-500', icon: Clock },
      in_progress: { label: 'Dikerjakan', color: 'bg-blue-500', icon: AlertCircle },
      completed: { label: 'Selesai', color: 'bg-green-500', icon: CheckCircle }
    };
    const { label, color, icon: Icon } = config[status] || config.pending;
    return (
      <Badge className={`${color} text-white`}>
        <Icon className="w-3 h-3 mr-1" />
        {label}
      </Badge>
    );
  };

  const getDaysLeft = (deadline) => {
    const now = new Date();
    const due = new Date(deadline);
    const diff = Math.ceil((due - now) / (1000 * 60 * 60 * 24));
    return diff;
  };

  const filterRecommendations = (status) => {
    if (status === 'all') return recommendations;
    return recommendations.filter(r => r.status === status);
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-96">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6" data-testid="recommendations-page">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold mb-2" style={{ fontFamily: 'Manrope, sans-serif', color: '#1a1a1a' }}>Rekomendasi Audit</h1>
            <p className="text-slate-600">Kelola rekomendasi dan tindak lanjut audit</p>
          </div>
          {user?.role === 'auditor' && (
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button className="bg-emerald-600 hover:bg-emerald-700" data-testid="add-recommendation-button">
                  <Plus className="w-4 h-4 mr-2" />
                  Tambah Rekomendasi
                </Button>
              </DialogTrigger>
              <DialogContent data-testid="add-recommendation-dialog">
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
                      <SelectTrigger data-testid="recommendation-clause-select">
                        <SelectValue placeholder="Pilih klausul" />
                      </SelectTrigger>
                      <SelectContent>
                        {clauses.map((c) => (
                          <SelectItem key={c.id} value={c.id}>{c.clause_number}: {c.title}</SelectItem>
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
                    />
                  </div>
                  <Button type="submit" className="w-full bg-emerald-600 hover:bg-emerald-700" data-testid="submit-recommendation-button">
                    Simpan
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
          )}
        </div>

        <Tabs defaultValue="all" className="space-y-4">
          <TabsList>
            <TabsTrigger value="all" data-testid="tab-all">Semua ({recommendations.length})</TabsTrigger>
            <TabsTrigger value="pending" data-testid="tab-pending">Pending ({filterRecommendations('pending').length})</TabsTrigger>
            <TabsTrigger value="in_progress" data-testid="tab-in-progress">Dikerjakan ({filterRecommendations('in_progress').length})</TabsTrigger>
            <TabsTrigger value="completed" data-testid="tab-completed">Selesai ({filterRecommendations('completed').length})</TabsTrigger>
          </TabsList>

          {['all', 'pending', 'in_progress', 'completed'].map((tab) => (
            <TabsContent key={tab} value={tab} className="space-y-4">
              {filterRecommendations(tab).length === 0 ? (
                <Card>
                  <CardContent className="pt-6 text-center py-12">
                    <Calendar className="w-12 h-12 mx-auto text-slate-300 mb-4" />
                    <p className="text-slate-600">Belum ada rekomendasi</p>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {filterRecommendations(tab).map((rec) => {
                    const daysLeft = getDaysLeft(rec.deadline);
                    const isOverdue = daysLeft < 0 && rec.status !== 'completed';
                    const isUrgent = daysLeft <= 3 && daysLeft >= 0 && rec.status !== 'completed';

                    return (
                      <Card key={rec.id} className={`shadow-md ${
                        isOverdue ? 'border-l-4 border-red-500' :
                        isUrgent ? 'border-l-4 border-orange-500' : ''
                      }`} data-testid="recommendation-card">
                        <CardHeader className="pb-3">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <CardTitle className="text-base mb-2">{getClauseName(rec.clause_id)}</CardTitle>
                              {getStatusBadge(rec.status)}
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent className="space-y-4">
                          <div>
                            <p className="text-sm text-slate-700">{rec.recommendation_text}</p>
                          </div>

                          <div className="flex items-center gap-2 text-sm">
                            <Calendar className="w-4 h-4 text-slate-400" />
                            <span className={`${
                              isOverdue ? 'text-red-600 font-medium' :
                              isUrgent ? 'text-orange-600 font-medium' :
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
                                  className="flex-1"
                                  data-testid="start-button"
                                >
                                  Mulai Kerjakan
                                </Button>
                              )}
                              {rec.status === 'in_progress' && (
                                <Button
                                  size="sm"
                                  onClick={() => handleUpdateStatus(rec.id, 'completed')}
                                  className="flex-1 bg-green-600 hover:bg-green-700"
                                  data-testid="complete-button"
                                >
                                  <CheckCircle className="w-4 h-4 mr-2" />
                                  Tandai Selesai
                                </Button>
                              )}
                            </div>
                          )}

                          {rec.completed_at && (
                            <p className="text-xs text-green-600">
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