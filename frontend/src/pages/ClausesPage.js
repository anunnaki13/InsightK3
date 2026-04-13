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
import { BookOpen, Edit, FileText, Plus, Sparkles } from 'lucide-react';
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

  const getClausesByCriteria = (criteriaId) => clauses.filter((clause) => clause.criteria_id === criteriaId);
  const knowledgeBaseCount = clauses.filter((clause) => clause.knowledge_base).length;

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
      <div className="space-y-6" data-testid="clauses-page">
        <section className="grid gap-5 xl:grid-cols-[1.25fr_0.95fr]">
          <Card className="overflow-hidden rounded-[30px] border-0 bg-[linear-gradient(135deg,#1a314e_0%,#294d77_58%,#3f6b99_100%)] text-white shadow-[0_32px_90px_rgba(26,49,78,0.26)]">
            <CardContent className="p-7 md:p-8">
              <p className="text-[11px] font-bold uppercase tracking-[0.28em] text-sky-100/75">Clause Library</p>
              <h1 className="mt-3 text-4xl font-extrabold leading-tight md:text-5xl">Kelola klausul dan knowledge base sebagai mesin konteks untuk audit evidence.</h1>
              <p className="mt-4 max-w-2xl text-sm leading-6 text-sky-50/80 md:text-base">
                Di sini struktur audit bertemu dengan konteks penilaian. Kualitas knowledge base akan menentukan kualitas review AI dan konsistensi audit.
              </p>
            </CardContent>
          </Card>

          <Card className="rounded-[30px] border-white/70 bg-white/80 shadow-[0_24px_70px_rgba(45,68,58,0.10)] backdrop-blur-xl">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Library Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-[20px] bg-slate-50 px-4 py-3">
                  <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Total Klausul</p>
                  <p className="mt-2 text-3xl font-extrabold text-slate-950">{clauses.length}</p>
                </div>
                <div className="rounded-[20px] bg-slate-50 px-4 py-3">
                  <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">KB Ready</p>
                  <p className="mt-2 text-3xl font-extrabold text-emerald-700">{knowledgeBaseCount}</p>
                </div>
              </div>
              {user?.role === 'admin' && (
                <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                  <DialogTrigger asChild>
                    <Button className="h-12 rounded-[18px] bg-slate-950 hover:bg-slate-800" data-testid="add-clause-button">
                      <Plus className="mr-2 h-4 w-4" />
                      Tambah Klausul
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="rounded-[28px]" data-testid="add-clause-dialog">
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
                          <SelectTrigger className="h-12 rounded-[16px]" data-testid="clause-criteria-select">
                            <SelectValue placeholder="Pilih kriteria" />
                          </SelectTrigger>
                          <SelectContent>
                            {criteria.map((criterion) => (
                              <SelectItem key={criterion.id} value={criterion.id}>{criterion.name}</SelectItem>
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
                          className="h-12 rounded-[16px]"
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
                          className="h-12 rounded-[16px]"
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
                          rows={4}
                          className="rounded-[16px]"
                        />
                      </div>
                      <Button type="submit" className="h-12 w-full rounded-[18px] bg-emerald-700 hover:bg-emerald-800" data-testid="submit-clause-button">
                        Simpan
                      </Button>
                    </form>
                  </DialogContent>
                </Dialog>
              )}
            </CardContent>
          </Card>
        </section>

        <Dialog open={kbDialogOpen} onOpenChange={setKbDialogOpen}>
          <DialogContent className="max-w-2xl rounded-[28px]" data-testid="knowledge-base-dialog">
            <DialogHeader>
              <DialogTitle>Knowledge Base - {selectedClause?.clause_number}</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleUpdateKnowledgeBase} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="knowledge_base">Knowledge Base untuk AI Audit</Label>
                <Textarea
                  id="knowledge_base"
                  data-testid="knowledge-base-input"
                  placeholder="Masukkan standar, persyaratan, dan kriteria penilaian untuk klausul ini."
                  value={knowledgeBase}
                  onChange={(e) => setKnowledgeBase(e.target.value)}
                  rows={12}
                  className="rounded-[16px] font-mono text-sm"
                />
                <p className="text-xs leading-6 text-slate-500">
                  Tulis konteks yang cukup tegas: dokumen yang wajib ada, standar minimum, indikator kelengkapan, dan ekspektasi evaluasi.
                </p>
              </div>
              <Button type="submit" className="h-12 w-full rounded-[18px] bg-slate-950 hover:bg-slate-800" data-testid="save-knowledge-base-button">
                Simpan Knowledge Base
              </Button>
            </form>
          </DialogContent>
        </Dialog>

        <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
          <CardContent className="pt-6">
            {criteria.length === 0 ? (
              <div className="py-14 text-center">
                <BookOpen className="mx-auto mb-4 h-12 w-12 text-slate-300" />
                <p className="text-slate-600">Belum ada kriteria. Silakan tambahkan kriteria terlebih dahulu.</p>
              </div>
            ) : (
              <Accordion type="single" collapsible className="space-y-4">
                {criteria.map((criterion) => {
                  const criterionClauses = getClausesByCriteria(criterion.id);
                  return (
                    <AccordionItem key={criterion.id} value={criterion.id} className="rounded-[24px] border border-slate-100 bg-slate-50/70 px-5" data-testid="criteria-accordion-item">
                      <AccordionTrigger className="hover:no-underline">
                        <div className="flex items-center gap-4 text-left">
                          <div className="flex h-12 w-12 items-center justify-center rounded-[18px] bg-sky-50 text-sky-700">
                            <span className="text-lg font-extrabold">{criterion.order}</span>
                          </div>
                          <div>
                            <h3 className="font-bold text-base text-slate-950">{criterion.name}</h3>
                            <p className="text-sm text-slate-500">{criterionClauses.length} klausul</p>
                          </div>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent>
                        {criterionClauses.length === 0 ? (
                          <p className="py-4 text-sm text-slate-500">Belum ada klausul untuk kriteria ini.</p>
                        ) : (
                          <div className="space-y-3 pt-4">
                            {criterionClauses.map((clause) => (
                              <div key={clause.id} className="rounded-[22px] bg-white p-4 shadow-sm" data-testid="clause-item">
                                <div className="flex items-start justify-between gap-4">
                                  <div className="min-w-0 flex-1">
                                    <div className="mb-2 flex flex-wrap items-center gap-2">
                                      <span className="rounded-full bg-slate-950 px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.16em] text-white">
                                        {clause.clause_number}
                                      </span>
                                      <h4 className="font-semibold text-slate-950">{clause.title}</h4>
                                    </div>
                                    <p className="text-sm leading-6 text-slate-600">{clause.description}</p>
                                    <div className="mt-3">
                                      {clause.knowledge_base ? (
                                        <div className="rounded-[18px] border border-emerald-200 bg-emerald-50 p-3">
                                          <div className="mb-1 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700">
                                            <Sparkles className="h-3.5 w-3.5" />
                                            Knowledge Base Ready
                                          </div>
                                          <p className="line-clamp-2 text-xs leading-5 text-slate-700">{clause.knowledge_base}</p>
                                        </div>
                                      ) : (
                                        <div className="rounded-[18px] border border-dashed border-slate-200 bg-slate-50 p-3 text-xs text-slate-500">
                                          Knowledge base belum disusun untuk klausul ini.
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                  {(user?.role === 'admin' || user?.role === 'auditor') && (
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      onClick={() => openKbDialog(clause)}
                                      className="rounded-[16px]"
                                      data-testid="edit-knowledge-base-button"
                                    >
                                      <Edit className="mr-2 h-4 w-4" />
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
