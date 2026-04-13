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
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Plus, BookOpen, Edit } from 'lucide-react';
import { toast } from 'sonner';

const ClausesPage = () => {
  const { API, user } = useContext(AppContext);
  const [criteria, setCriteria] = useState([]);
  const [clauses, setClauses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [kbDialogOpen, setKbDialogOpen] = useState(false);
  const [selectedClause, setSelectedClause] = useState(null);
  const [formData, setFormData] = useState({
    criteria_id: '',
    clause_number: '',
    title: '',
    description: ''
  });
  const [knowledgeBase, setKnowledgeBase] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [criteriaRes, clausesRes] = await Promise.all([
        axios.get(`${API}/criteria`),
        axios.get(`${API}/clauses`)
      ]);
      setCriteria(criteriaRes.data);
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
      await axios.post(`${API}/clauses`, formData);
      toast.success('Klausul berhasil ditambahkan');
      setDialogOpen(false);
      setFormData({ criteria_id: '', clause_number: '', title: '', description: '' });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal menambahkan klausul');
    }
  };

  const handleUpdateKnowledgeBase = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`${API}/clauses/${selectedClause.id}/knowledge-base`, {
        knowledge_base: knowledgeBase
      });
      toast.success('Knowledge base berhasil diperbarui');
      setKbDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal memperbarui knowledge base');
    }
  };

  const openKbDialog = (clause) => {
    setSelectedClause(clause);
    setKnowledgeBase(clause.knowledge_base || '');
    setKbDialogOpen(true);
  };

  const getClausesByCriteria = (criteriaId) => {
    return clauses.filter(c => c.criteria_id === criteriaId);
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
      <div className="space-y-6" data-testid="clauses-page">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold mb-2" style={{ fontFamily: 'Manrope, sans-serif', color: '#1a1a1a' }}>Klausul Audit</h1>
            <p className="text-slate-600">Kelola klausul dan knowledge base untuk audit SMK3</p>
          </div>
          {user?.role === 'admin' && (
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button className="bg-emerald-600 hover:bg-emerald-700" data-testid="add-clause-button">
                  <Plus className="w-4 h-4 mr-2" />
                  Tambah Klausul
                </Button>
              </DialogTrigger>
              <DialogContent data-testid="add-clause-dialog">
                <DialogHeader>
                  <DialogTitle>Tambah Klausul Baru</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="criteria">Kriteria</Label>
                    <Select
                      value={formData.criteria_id}
                      onValueChange={(value) => setFormData({ ...formData, criteria_id: value })}
                      required
                    >
                      <SelectTrigger data-testid="clause-criteria-select">
                        <SelectValue placeholder="Pilih kriteria" />
                      </SelectTrigger>
                      <SelectContent>
                        {criteria.map((c) => (
                          <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="clause_number">Nomor Klausul</Label>
                    <Input
                      id="clause_number"
                      data-testid="clause-number-input"
                      placeholder="Contoh: 1.1.1"
                      value={formData.clause_number}
                      onChange={(e) => setFormData({ ...formData, clause_number: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="title">Judul Klausul</Label>
                    <Input
                      id="title"
                      data-testid="clause-title-input"
                      value={formData.title}
                      onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="description">Deskripsi</Label>
                    <Textarea
                      id="description"
                      data-testid="clause-description-input"
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      required
                      rows={3}
                    />
                  </div>
                  <Button type="submit" className="w-full bg-emerald-600 hover:bg-emerald-700" data-testid="submit-clause-button">
                    Simpan
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
          )}
        </div>

        {/* Knowledge Base Dialog */}
        <Dialog open={kbDialogOpen} onOpenChange={setKbDialogOpen}>
          <DialogContent className="max-w-2xl" data-testid="knowledge-base-dialog">
            <DialogHeader>
              <DialogTitle>Knowledge Base - {selectedClause?.clause_number}</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleUpdateKnowledgeBase} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="knowledge_base">Knowledge Base untuk AI Audit</Label>
                <Textarea
                  id="knowledge_base"
                  data-testid="knowledge-base-input"
                  placeholder="Masukkan standar, persyaratan, dan kriteria penilaian untuk klausul ini. AI akan menggunakan informasi ini untuk menilai dokumen evidence."
                  value={knowledgeBase}
                  onChange={(e) => setKnowledgeBase(e.target.value)}
                  rows={12}
                  className="font-mono text-sm"
                />
                <p className="text-xs text-slate-500">
                  Contoh: "Klausul ini mengharuskan adanya dokumen kebijakan K3 yang ditandatangani oleh manajemen puncak, 
                  berisi komitmen terhadap keselamatan kerja, dan dipublikasikan ke seluruh karyawan. 
                  Penilaian: 100 jika semua ada, 70 jika ada tapi tidak lengkap, 0 jika tidak ada."
                </p>
              </div>
              <Button type="submit" className="w-full bg-emerald-600 hover:bg-emerald-700" data-testid="save-knowledge-base-button">
                Simpan Knowledge Base
              </Button>
            </form>
          </DialogContent>
        </Dialog>

        <Card className="shadow-md">
          <CardContent className="pt-6">
            {criteria.length === 0 ? (
              <div className="text-center py-12">
                <BookOpen className="w-12 h-12 mx-auto text-slate-300 mb-4" />
                <p className="text-slate-600">Belum ada kriteria. Silakan tambahkan kriteria terlebih dahulu.</p>
              </div>
            ) : (
              <Accordion type="single" collapsible className="space-y-4">
                {criteria.map((crit) => {
                  const critClauses = getClausesByCriteria(crit.id);
                  return (
                    <AccordionItem key={crit.id} value={crit.id} className="border rounded-lg px-4" data-testid="criteria-accordion-item">
                      <AccordionTrigger className="hover:no-underline">
                        <div className="flex items-center gap-4 text-left">
                          <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center flex-shrink-0">
                            <span className="text-lg font-bold text-emerald-700" style={{ fontFamily: 'Manrope, sans-serif' }}>{crit.order}</span>
                          </div>
                          <div>
                            <h3 className="font-semibold text-base">{crit.name}</h3>
                            <p className="text-sm text-slate-500">{critClauses.length} klausul</p>
                          </div>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent>
                        {critClauses.length === 0 ? (
                          <p className="text-sm text-slate-500 py-4">Belum ada klausul untuk kriteria ini.</p>
                        ) : (
                          <div className="space-y-3 pt-4">
                            {critClauses.map((clause) => (
                              <div key={clause.id} className="p-4 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors" data-testid="clause-item">
                                <div className="flex items-start justify-between">
                                  <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-2">
                                      <span className="px-2 py-1 bg-emerald-600 text-white text-xs font-medium rounded">
                                        {clause.clause_number}
                                      </span>
                                      <h4 className="font-medium">{clause.title}</h4>
                                    </div>
                                    <p className="text-sm text-slate-600 mb-2">{clause.description}</p>
                                    {clause.knowledge_base && (
                                      <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded">
                                        <p className="text-xs font-medium text-blue-700 mb-1">Knowledge Base:</p>
                                        <p className="text-xs text-slate-700 line-clamp-2">{clause.knowledge_base}</p>
                                      </div>
                                    )}
                                  </div>
                                  {(user?.role === 'admin' || user?.role === 'auditor') && (
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      onClick={() => openKbDialog(clause)}
                                      className="ml-4"
                                      data-testid="edit-knowledge-base-button"
                                    >
                                      <Edit className="w-4 h-4 mr-2" />
                                      {clause.knowledge_base ? 'Edit KB' : 'Tambah KB'}
                                    </Button>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </AccordionContent>
                    </AccordionItem>
                  );
                })}
              </Accordion>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
};

export default ClausesPage;