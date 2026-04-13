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
import { Plus, Trash2, ListOrdered } from 'lucide-react';
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
        <div className="flex items-center justify-center h-96">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6" data-testid="criteria-page">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold mb-2" style={{ fontFamily: 'Manrope, sans-serif', color: '#1a1a1a' }}>Kriteria Audit</h1>
            <p className="text-slate-600">Kelola 12 kriteria audit SMK3</p>
          </div>
          <div className="flex gap-3">
            {criteria.length === 0 && user?.role === 'admin' && (
              <Button onClick={seedData} variant="outline" data-testid="seed-data-button">
                Inisialisasi Data
              </Button>
            )}
            {user?.role === 'admin' && (
              <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                <DialogTrigger asChild>
                  <Button className="bg-emerald-600 hover:bg-emerald-700" data-testid="add-criteria-button">
                    <Plus className="w-4 h-4 mr-2" />
                    Tambah Kriteria
                  </Button>
                </DialogTrigger>
                <DialogContent data-testid="add-criteria-dialog">
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
                        rows={3}
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
                        onChange={(e) => setFormData({ ...formData, order: parseInt(e.target.value) })}
                        required
                      />
                    </div>
                    <Button type="submit" className="w-full bg-emerald-600 hover:bg-emerald-700" data-testid="submit-criteria-button">
                      Simpan
                    </Button>
                  </form>
                </DialogContent>
              </Dialog>
            )}
          </div>
        </div>

        {criteria.length === 0 ? (
          <Card data-testid="empty-criteria-message">
            <CardContent className="pt-6 text-center">
              <ListOrdered className="w-12 h-12 mx-auto text-slate-300 mb-4" />
              <p className="text-slate-600">Belum ada kriteria audit. Klik "Inisialisasi Data" untuk memulai.</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {criteria.map((item) => (
              <Card key={item.id} className="shadow-md hover:shadow-lg transition-all" data-testid="criteria-card">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
                        <span className="text-lg font-bold text-emerald-700" style={{ fontFamily: 'Manrope, sans-serif' }}>{item.order}</span>
                      </div>
                      <CardTitle className="text-base leading-tight">{item.name}</CardTitle>
                    </div>
                    {user?.role === 'admin' && (
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-8 w-8 text-red-500 hover:text-red-700 hover:bg-red-50" data-testid="delete-criteria-button">
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
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
                  <p className="text-sm text-slate-600">{item.description}</p>
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