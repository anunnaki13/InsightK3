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
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog';
import { Layers3, ListOrdered, Plus, Trash2 } from 'lucide-react';
import { toast } from 'sonner';

const CriteriaPage = () => {
  const { API, user } = useContext(AppContext);
  const [criteria, setCriteria] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({ name: '', description: '', order: 1 });

  useEffect(() => {
    fetchCriteria();
  }, []);

  const fetchCriteria = async () => {
    try {
      const response = await axios.get(`${API}/criteria`);
      setCriteria(response.data);
    } catch (error) {
      toast.error('Gagal memuat kriteria');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/criteria`, formData);
      toast.success('Kriteria berhasil ditambahkan');
      setDialogOpen(false);
      setFormData({ name: '', description: '', order: 1 });
      fetchCriteria();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal menambahkan kriteria');
    }
  };

  const handleDelete = async (id) => {
    try {
      await axios.delete(`${API}/criteria/${id}`);
      toast.success('Kriteria berhasil dihapus');
      fetchCriteria();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal menghapus kriteria');
    }
  };

  const seedData = async () => {
    try {
      await axios.post(`${API}/seed-data`);
      toast.success('Data berhasil diinisialisasi');
      fetchCriteria();
    } catch (error) {
      toast.info(error.response?.data?.message || 'Data sudah ada');
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
      <div className="space-y-6" data-testid="criteria-page">
        <section className="grid gap-5 xl:grid-cols-[1.25fr_0.95fr]">
          <Card className="overflow-hidden rounded-[30px] border-0 bg-[linear-gradient(135deg,#44311a_0%,#6c4f28_58%,#8e6a3a_100%)] text-white shadow-[0_32px_90px_rgba(68,49,26,0.24)]">
            <CardContent className="p-7 md:p-8">
              <p className="text-[11px] font-bold uppercase tracking-[0.28em] text-amber-100/75">Criteria Structure</p>
              <h1 className="mt-3 text-4xl font-extrabold leading-tight md:text-5xl">Kelola fondasi 12 kriteria audit sebagai kerangka kerja seluruh penilaian.</h1>
              <p className="mt-4 max-w-2xl text-sm leading-6 text-amber-50/80 md:text-base">
                Kriteria menjadi tulang punggung struktur audit, organisasi klausul, dan konsistensi dashboard manajemen.
              </p>
            </CardContent>
          </Card>

          <Card className="rounded-[30px] border-white/70 bg-white/80 shadow-[0_24px_70px_rgba(45,68,58,0.10)] backdrop-blur-xl">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Control Panel</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="rounded-[20px] bg-slate-50 px-4 py-3">
                <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Total Criteria</p>
                <p className="mt-2 text-3xl font-extrabold text-slate-950">{criteria.length}</p>
              </div>
              <div className="flex flex-wrap gap-3">
                {criteria.length === 0 && user?.role === 'admin' && (
                  <Button onClick={seedData} variant="outline" className="rounded-[18px]" data-testid="seed-data-button">
                    Inisialisasi Data
                  </Button>
                )}
                {user?.role === 'admin' && (
                  <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                    <DialogTrigger asChild>
                      <Button className="rounded-[18px] bg-slate-950 hover:bg-slate-800" data-testid="add-criteria-button">
                        <Plus className="mr-2 h-4 w-4" />
                        Tambah Kriteria
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="rounded-[28px]" data-testid="add-criteria-dialog">
                      <DialogHeader>
                        <DialogTitle>Tambah Kriteria Baru</DialogTitle>
                      </DialogHeader>
                      <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="name">Nama Kriteria</Label>
                          <Input
                            id="name"
                            data-testid="criteria-name-input"
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            required
                            className="h-12 rounded-[16px]"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="description">Deskripsi</Label>
                          <Textarea
                            id="description"
                            data-testid="criteria-description-input"
                            value={formData.description}
                            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                            required
                            rows={4}
                            className="rounded-[16px]"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="order">Urutan</Label>
                          <Input
                            id="order"
                            data-testid="criteria-order-input"
                            type="number"
                            min="1"
                            value={formData.order}
                            onChange={(e) => setFormData({ ...formData, order: parseInt(e.target.value, 10) })}
                            required
                            className="h-12 rounded-[16px]"
                          />
                        </div>
                        <Button type="submit" className="h-12 w-full rounded-[18px] bg-emerald-700 hover:bg-emerald-800" data-testid="submit-criteria-button">
                          Simpan
                        </Button>
                      </form>
                    </DialogContent>
                  </Dialog>
                )}
              </div>
            </CardContent>
          </Card>
        </section>

        {criteria.length === 0 ? (
          <Card className="rounded-[28px] border-white/70 bg-white/80" data-testid="empty-criteria-message">
            <CardContent className="py-14 text-center">
              <ListOrdered className="mx-auto mb-4 h-12 w-12 text-slate-300" />
              <p className="text-slate-600">Belum ada kriteria audit. Klik "Inisialisasi Data" untuk memulai.</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
            {criteria.map((item) => (
              <Card key={item.id} className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]" data-testid="criteria-card">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className="flex h-12 w-12 items-center justify-center rounded-[18px] bg-amber-50 text-amber-700">
                        <span className="text-lg font-extrabold">{item.order}</span>
                      </div>
                      <div>
                        <CardTitle className="text-lg leading-tight">{item.name}</CardTitle>
                        <p className="mt-1 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Audit pillar</p>
                      </div>
                    </div>
                    {user?.role === 'admin' && (
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-9 w-9 rounded-full text-red-500 hover:bg-red-50 hover:text-red-700" data-testid="delete-criteria-button">
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent className="rounded-[26px]">
                          <AlertDialogHeader>
                            <AlertDialogTitle>Hapus Kriteria?</AlertDialogTitle>
                            <AlertDialogDescription>
                              Tindakan ini tidak dapat dibatalkan. Kriteria akan dihapus permanen.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Batal</AlertDialogCancel>
                            <AlertDialogAction onClick={() => handleDelete(item.id)} className="bg-red-600 hover:bg-red-700">
                              Hapus
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="rounded-[22px] bg-slate-50 p-4">
                    <p className="text-sm leading-6 text-slate-600">{item.description}</p>
                  </div>
                  <div className="mt-4 inline-flex items-center gap-2 rounded-full bg-amber-50 px-3 py-1.5 text-xs font-semibold text-amber-700">
                    <Layers3 className="h-3.5 w-3.5" />
                    Structured for clause grouping
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
};

export default CriteriaPage;
