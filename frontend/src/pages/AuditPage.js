import React, { useState, useEffect, useContext } from 'react';
import { AppContext } from '../App';
import axios from 'axios';
import Layout from '../components/Layout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Calendar } from '@/components/ui/calendar';
import { format } from 'date-fns';
import { id as idLocale } from 'date-fns/locale';
import { Upload, FileText, Trash2, Play, CheckCircle, XCircle, Loader2, Eye, Download, Archive, RefreshCw, Calendar as CalendarIcon, Save } from 'lucide-react';
import { toast } from 'sonner';

const AuditPage = () => {
  const { API, user } = useContext(AppContext);
  const [criteria, setCriteria] = useState([]);
  const [clauses, setClauses] = useState([]);
  const [selectedCriteria, setSelectedCriteria] = useState('');
  const [selectedClause, setSelectedClause] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [auditResult, setAuditResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [previewDoc, setPreviewDoc] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const [showResetDialog, setShowResetDialog] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [auditorAssessment, setAuditorAssessment] = useState({
    auditor_status: '',
    auditor_notes: '',
    agreed_date: ''
  });
  const [savingAssessment, setSavingAssessment] = useState(false);

  useEffect(() => {
    fetchCriteria();
  }, []);

  useEffect(() => {
    if (selectedCriteria) {
      fetchClauses(selectedCriteria);
    }
  }, [selectedCriteria]);

  useEffect(() => {
    if (selectedClause) {
      fetchDocuments(selectedClause.id);
      fetchAuditResult(selectedClause.id);
    }
  }, [selectedClause]);

  useEffect(() => {
    if (auditResult) {
      setAuditorAssessment({
        auditor_status: auditResult.auditor_status || '',
        auditor_notes: auditResult.auditor_notes || '',
        agreed_date: auditResult.agreed_date ? new Date(auditResult.agreed_date).toISOString().split('T')[0] : ''
      });
    }
  }, [auditResult]);

  const fetchCriteria = async () => {
    try {
      const response = await axios.get(`${API}/criteria`);
      setCriteria(response.data);
    } catch (error) {
      toast.error('Gagal memuat kriteria');
    }
  };

  const fetchClauses = async (criteriaId) => {
    try {
      const response = await axios.get(`${API}/clauses?criteria_id=${criteriaId}`);
      setClauses(response.data);
      if (response.data.length > 0) {
        setSelectedClause(response.data[0]);
      }
    } catch (error) {
      toast.error('Gagal memuat klausul');
    }
  };

  const fetchDocuments = async (clauseId) => {
    try {
      const response = await axios.get(`${API}/clauses/${clauseId}/documents`);
      setDocuments(response.data);
    } catch (error) {
      console.error('Error fetching documents:', error);
    }
  };

  const fetchAuditResult = async (clauseId) => {
    try {
      const response = await axios.get(`${API}/audit/results/${clauseId}`);
      setAuditResult(response.data);
    } catch (error) {
      setAuditResult(null);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file || !selectedClause) return;

    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);
    try {
      await axios.post(`${API}/clauses/${selectedClause.id}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      toast.success('Dokumen berhasil diupload');
      fetchDocuments(selectedClause.id);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal mengupload dokumen');
    } finally {
      setLoading(false);
      e.target.value = '';
    }
  };

  const handleDeleteDocument = async (docId) => {
    if (!window.confirm('Apakah Anda yakin ingin menghapus dokumen ini? Jika tidak ada dokumen tersisa, hasil audit akan dihapus.')) {
      return;
    }
    
    try {
      const response = await axios.delete(`${API}/documents/${docId}`);
      
      if (response.data.audit_result_deleted) {
        toast.success('Dokumen dan hasil audit berhasil dihapus (tidak ada dokumen tersisa)');
        setAuditResult(null);
      } else {
        toast.success('Dokumen berhasil dihapus');
      }
      
      fetchDocuments(selectedClause.id);
    } catch (error) {
      toast.error('Gagal menghapus dokumen');
    }
  };

  const handlePreviewDocument = async (doc) => {
    try {
      const response = await axios.get(`${API}/documents/${doc.id}/preview`, {
        responseType: 'blob'
      });
      
      // Create blob with proper MIME type
      const blob = new Blob([response.data], { type: doc.mime_type || 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      setPreviewDoc({ ...doc, previewUrl: url });
      setShowPreview(true);
    } catch (error) {
      toast.error('Gagal membuka preview dokumen');
      console.error('Preview error:', error);
    }
  };

  const handleDownloadDocument = async (docId, filename) => {
    try {
      const response = await axios.get(`${API}/documents/${docId}/download`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      toast.error('Gagal mengunduh dokumen');
      console.error('Download error:', error);
    }
  };

  const handleDownloadAllDocuments = () => {
    if (!selectedClause) return;
    const downloadUrl = `${API}/clauses/${selectedClause.id}/documents/download-all`;
    window.open(downloadUrl, '_blank');
  };

  const isPdfOrImage = (filename) => {
    const ext = filename.split('.').pop().toLowerCase();
    return ['pdf', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].includes(ext);
  };

  const handleHardReset = async () => {
    setResetting(true);
    try {
      const response = await axios.post(`${API}/audit/hard-reset`);
      const deleted = response.data.deleted;
      
      toast.success(
        `Hard reset berhasil! Dihapus: ${deleted.documents} dokumen, ${deleted.audit_results} hasil audit, ${deleted.recommendations} rekomendasi`
      );
      
      setShowResetDialog(false);
      setDocuments([]);
      setAuditResult(null);
      setSelectedClause(null);
      setSelectedCriteria('');
      
      // Refresh page after a moment
      setTimeout(() => {
        window.location.reload();
      }, 2000);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal melakukan hard reset');
    } finally {
      setResetting(false);
    }
  };

  const handleSaveAuditorAssessment = async () => {
    if (!selectedClause || !auditResult) {
      toast.error('Tidak ada hasil audit AI. Lakukan analisis AI terlebih dahulu.');
      return;
    }

    if (!auditorAssessment.auditor_status) {
      toast.error('Pilih status penilaian (Confirm/Non-Confirm)');
      return;
    }

    if (!auditorAssessment.agreed_date) {
      toast.error('Tentukan tanggal kesepakatan');
      return;
    }

    setSavingAssessment(true);
    try {
      await axios.put(
        `${API}/audit/results/${selectedClause.id}/auditor-assessment`,
        auditorAssessment
      );
      toast.success('Penilaian auditor berhasil disimpan!');
      fetchAuditResult(selectedClause.id);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal menyimpan penilaian auditor');
    } finally {
      setSavingAssessment(false);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedClause) return;

    setAnalyzing(true);
    try {
      const response = await axios.post(`${API}/audit/analyze/${selectedClause.id}`);
      setAuditResult(response.data);
      toast.success('Analisis selesai!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal menganalisis dokumen');
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <Layout>
      {/* Preview Dialog */}
      <Dialog open={showPreview} onOpenChange={setShowPreview}>
        <DialogContent className="max-w-4xl h-[80vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              {previewDoc?.filename}
            </DialogTitle>
          </DialogHeader>
          <div className="flex-1 overflow-auto bg-slate-50">
            {previewDoc && (
              <div className="w-full h-full">
                {previewDoc.mime_type?.includes('pdf') || previewDoc.filename.toLowerCase().endsWith('.pdf') ? (
                  <iframe
                    src={`${previewDoc.previewUrl}#view=FitH`}
                    className="w-full h-full border-0"
                    style={{ minHeight: '600px' }}
                    title="PDF Preview"
                  />
                ) : previewDoc.mime_type?.includes('image') || /\.(jpg|jpeg|png|gif|bmp|webp)$/i.test(previewDoc.filename) ? (
                  <div className="flex items-center justify-center h-full p-4">
                    <img
                      src={previewDoc.previewUrl}
                      alt={previewDoc.filename}
                      className="max-w-full max-h-full object-contain"
                    />
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center p-8">
                      <FileText className="w-16 h-16 mx-auto text-slate-400 mb-4" />
                      <p className="text-slate-600 mb-2">Preview tidak tersedia untuk tipe file ini</p>
                      <p className="text-sm text-slate-500 mb-4">{previewDoc.filename}</p>
                      <Button
                        onClick={() => handleDownloadDocument(previewDoc.id, previewDoc.filename)}
                      >
                        <Download className="w-4 h-4 mr-2" />
                        Download File
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button
              variant="outline"
              onClick={() => handleDownloadDocument(previewDoc?.id, previewDoc?.filename)}
            >
              <Download className="w-4 h-4 mr-2" />
              Download
            </Button>
            <Button variant="outline" onClick={() => setShowPreview(false)}>
              Tutup
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Hard Reset Dialog */}
      <AlertDialog open={showResetDialog} onOpenChange={setShowResetDialog}>
        <AlertDialogContent className="max-w-md">
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2 text-red-600">
              <RefreshCw className="w-5 h-5" />
              Konfirmasi Hard Reset
            </AlertDialogTitle>
            <AlertDialogDescription className="space-y-3 pt-2">
              <p className="font-semibold text-slate-900">
                ⚠️ PERINGATAN: Tindakan ini tidak dapat dibatalkan!
              </p>
              <div className="space-y-2 text-sm">
                <p>Hard reset akan menghapus:</p>
                <ul className="list-disc list-inside space-y-1 text-slate-700 ml-2">
                  <li>Semua dokumen evidence yang telah diupload</li>
                  <li>Semua hasil penilaian AI</li>
                  <li>Semua skor dan status audit</li>
                  <li>Semua rekomendasi auditor</li>
                </ul>
              </div>
              <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-xs text-yellow-800 font-medium">
                  💾 Sangat disarankan untuk <strong>backup evidence terlebih dahulu</strong> menggunakan tombol "Download Semua Evidence" di Dashboard sebelum melanjutkan.
                </p>
              </div>
              <p className="text-sm font-medium text-slate-900 pt-2">
                Apakah Anda yakin ingin melanjutkan?
              </p>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={resetting}>Batal</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleHardReset}
              disabled={resetting}
              className="bg-red-600 hover:bg-red-700"
            >
              {resetting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Menghapus...
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Ya, Reset Semua
                </>
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <div className="space-y-6" data-testid="audit-page">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-4xl font-bold mb-2" style={{ fontFamily: 'Manrope, sans-serif', color: '#1a1a1a' }}>Audit Dokumen</h1>
            <p className="text-slate-600">Upload dokumen evidence dan lakukan audit AI</p>
          </div>
          {user?.role === 'admin' && (
            <Button
              variant="outline"
              onClick={() => setShowResetDialog(true)}
              className="border-red-300 text-red-600 hover:bg-red-50 hover:text-red-700"
              data-testid="hard-reset-button"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Hard Reset Audit
            </Button>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Selection Panel */}
          <Card className="lg:col-span-1 shadow-md" data-testid="selection-panel">
            <CardHeader>
              <CardTitle>Pilih Klausul</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Kriteria</label>
                <Select value={selectedCriteria} onValueChange={setSelectedCriteria}>
                  <SelectTrigger data-testid="criteria-select">
                    <SelectValue placeholder="Pilih kriteria" />
                  </SelectTrigger>
                  <SelectContent>
                    {criteria.map((c) => (
                      <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {clauses.length > 0 && (
                <div className="space-y-2">
                  <label className="text-sm font-medium">Klausul</label>
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {clauses.map((clause) => (
                      <button
                        key={clause.id}
                        onClick={() => setSelectedClause(clause)}
                        className={`w-full text-left p-3 rounded-lg border transition-all ${
                          selectedClause?.id === clause.id
                            ? 'bg-emerald-50 border-emerald-500'
                            : 'bg-white hover:bg-slate-50 border-slate-200'
                        }`}
                        data-testid="clause-select-button"
                      >
                        <div className="font-medium text-sm">{clause.clause_number}</div>
                        <div className="text-xs text-slate-600 mt-1">{clause.title}</div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Document Upload Panel */}
          <Card className="lg:col-span-2 shadow-md" data-testid="upload-panel">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>
                  {selectedClause ? `${selectedClause.clause_number}: ${selectedClause.title}` : 'Pilih klausul'}
                </CardTitle>
                {selectedClause && documents.length > 0 && user?.role === 'auditor' && (
                  <Button
                    onClick={handleAnalyze}
                    disabled={analyzing || !selectedClause.knowledge_base}
                    className="bg-blue-600 hover:bg-blue-700"
                    data-testid="analyze-button"
                  >
                    {analyzing ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Menganalisis...
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4 mr-2" />
                        Analisis dengan AI (Tools Bantuan Auditor)
                      </>
                    )}
                  </Button>
                )}
                {selectedClause && documents.length > 0 && user?.role !== 'auditor' && (
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded text-sm text-blue-800">
                    ℹ️ Analisis AI hanya dapat dilakukan oleh Auditor
                  </div>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {selectedClause ? (
                <>
                  <p className="text-sm text-slate-600">{selectedClause.description}</p>

                  {/* Knowledge Base Display for all users */}
                  {selectedClause.knowledge_base && (
                    <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                      <h4 className="font-semibold text-blue-900 mb-3 flex items-center gap-2">
                        <FileText className="w-4 h-4" />
                        Panduan Dokumen yang Diperlukan
                      </h4>
                      <div className="text-sm text-slate-700 space-y-2">
                        {(() => {
                          const kb = selectedClause.knowledge_base;
                          
                          // Extract deskripsi klausul
                          const deskripsiMatch = kb.match(/DESKRIPSI KLAUSUL:([\s\S]*?)(?=DOKUMEN\/EVIDENCE|$)/i);
                          const deskripsi = deskripsiMatch ? deskripsiMatch[1].trim() : '';
                          
                          // Extract dokumen yang diperlukan
                          const dokumenMatch = kb.match(/DOKUMEN\/EVIDENCE YANG DIPERLUKAN[\s\S]*?:([\s\S]*?)(?=STANDAR PENILAIAN|$)/i);
                          const dokumen = dokumenMatch ? dokumenMatch[1].trim() : '';
                          
                          return (
                            <>
                              {deskripsi && (
                                <div>
                                  <p className="font-medium text-blue-800 mb-1">Deskripsi:</p>
                                  <p className="text-slate-700 whitespace-pre-line">{deskripsi}</p>
                                </div>
                              )}
                              {dokumen && (
                                <div className="mt-3">
                                  <p className="font-medium text-blue-800 mb-1">Dokumen/Evidence yang Harus Diupload:</p>
                                  <div className="text-slate-700 whitespace-pre-line bg-white p-3 rounded border border-blue-100">
                                    {dokumen}
                                  </div>
                                </div>
                              )}
                            </>
                          );
                        })()}
                      </div>
                    </div>
                  )}

                  {!selectedClause.knowledge_base && (
                    <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <p className="text-sm text-yellow-800">
                        <strong>Perhatian:</strong> Knowledge base belum dikonfigurasi untuk klausul ini. 
                        Silakan tambahkan knowledge base di halaman Klausul sebelum melakukan audit AI.
                      </p>
                    </div>
                  )}

                  {/* Upload Area */}
                  <div className="border-2 border-dashed border-slate-300 rounded-lg p-8 text-center hover:border-emerald-500 transition-colors">
                    <Upload className="w-12 h-12 mx-auto text-slate-400 mb-4" />
                    <p className="text-sm text-slate-600 mb-4">Upload dokumen evidence (PDF, Word, Excel, gambar)</p>
                    <input
                      type="file"
                      id="file-upload"
                      className="hidden"
                      onChange={handleFileUpload}
                      accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png"
                      data-testid="file-upload-input"
                    />
                    <label htmlFor="file-upload">
                      <Button
                        type="button"
                        disabled={loading}
                        onClick={() => document.getElementById('file-upload').click()}
                        className="bg-emerald-600 hover:bg-emerald-700"
                        data-testid="upload-button"
                      >
                        {loading ? 'Mengupload...' : 'Pilih File'}
                      </Button>
                    </label>
                  </div>

                  {/* Documents List */}
                  {documents.length > 0 && (
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <h3 className="font-medium text-sm">Dokumen Terupload ({documents.length})</h3>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={handleDownloadAllDocuments}
                          className="text-xs"
                          data-testid="download-all-button"
                        >
                          <Archive className="w-3 h-3 mr-1" />
                          Download Semua (ZIP)
                        </Button>
                      </div>
                      <div className="space-y-2">
                        {documents.map((doc) => (
                          <div key={doc.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors" data-testid="document-item">
                            <div className="flex items-center gap-3 flex-1">
                              <FileText className="w-5 h-5 text-blue-500 flex-shrink-0" />
                              <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium truncate">{doc.filename}</p>
                                <p className="text-xs text-slate-500">
                                  {(doc.size / 1024).toFixed(1)} KB • {new Date(doc.uploaded_at).toLocaleDateString('id-ID')}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-1 ml-2">
                              {isPdfOrImage(doc.filename) && (
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => handlePreviewDocument(doc)}
                                  className="h-8 w-8 text-blue-500 hover:text-blue-700 hover:bg-blue-50"
                                  data-testid="preview-document-button"
                                  title="Preview"
                                >
                                  <Eye className="w-4 h-4" />
                                </Button>
                              )}
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleDownloadDocument(doc.id, doc.filename)}
                                className="h-8 w-8 text-green-500 hover:text-green-700 hover:bg-green-50"
                                data-testid="download-document-button"
                                title="Download"
                              >
                                <Download className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleDeleteDocument(doc.id)}
                                className="h-8 w-8 text-red-500 hover:text-red-700 hover:bg-red-50"
                                data-testid="delete-document-button"
                                title="Hapus"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Audit Result */}
                  {auditResult && (
                    <Card className="border-2" data-testid="audit-result-card">
                      <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                          <div>
                            <CardTitle className="text-lg">Hasil Analisis AI (Tools Bantuan Auditor)</CardTitle>
                            <p className="text-xs text-slate-500 mt-1">Analisis kesesuaian dokumen yang diupload dengan dokumen yang diminta</p>
                          </div>
                          <Badge
                            variant={auditResult.status === 'Sesuai' ? 'default' : 'destructive'}
                            className={`${auditResult.status === 'Sesuai' ? 'bg-green-600' : 'bg-red-600'}`}
                          >
                            {auditResult.status === 'Sesuai' ? (
                              <CheckCircle className="w-4 h-4 mr-1" />
                            ) : (
                              <XCircle className="w-4 h-4 mr-1" />
                            )}
                            {auditResult.status}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium">Skor</span>
                            <span className="text-2xl font-bold" style={{ fontFamily: 'Manrope, sans-serif', color: auditResult.score >= 70 ? '#10b981' : '#ef4444' }}>
                              {auditResult.score.toFixed(1)}
                            </span>
                          </div>
                          <Progress value={auditResult.score} className="h-2" />
                        </div>

                        <div>
                          <h4 className="font-medium text-sm mb-2">Analisis Kesesuaian Dokumen</h4>
                          <p className="text-sm text-slate-700 bg-slate-50 p-3 rounded">{auditResult.reasoning}</p>
                        </div>

                        <div>
                          <h4 className="font-medium text-sm mb-2 text-green-700">Dokumen yang Sudah Sesuai</h4>
                          <p className="text-sm text-slate-700 bg-green-50 p-3 rounded border border-green-200">{auditResult.feedback}</p>
                        </div>

                        <div>
                          <h4 className="font-medium text-sm mb-2 text-orange-700">Dokumen yang Perlu Dilengkapi</h4>
                          <p className="text-sm text-slate-700 bg-orange-50 p-3 rounded border border-orange-200">{auditResult.improvement_suggestions}</p>
                        </div>

                        <div className="pt-3 border-t">
                          <p className="text-xs text-slate-500 italic">
                            ℹ️ Catatan: Ini adalah analisis AI sebagai tools bantuan. Keputusan akhir audit tetap di tangan auditor.
                          </p>
                        </div>

                        <p className="text-xs text-slate-500 text-right">
                          Diaudit pada: {new Date(auditResult.audited_at).toLocaleString('id-ID')}
                        </p>
                      </CardContent>
                    </Card>
                  )}

                  {/* Auditor Assessment Form */}
                  {auditResult && user?.role === 'auditor' && (
                    <Card className="border-2 border-emerald-200" data-testid="auditor-assessment-card">
                      <CardHeader className="pb-3 bg-emerald-50">
                        <CardTitle className="text-lg text-emerald-900">Penilaian Auditor (Keputusan Akhir)</CardTitle>
                        <p className="text-xs text-emerald-700 mt-1">Form penilaian final auditor terhadap klausul ini</p>
                      </CardHeader>
                      <CardContent className="space-y-5 pt-5">
                        {/* Status Assessment */}
                        <div className="space-y-3">
                          <Label className="text-sm font-semibold text-slate-900">
                            Status Penilaian <span className="text-red-500">*</span>
                          </Label>
                          <RadioGroup 
                            value={auditorAssessment.auditor_status} 
                            onValueChange={(value) => setAuditorAssessment(prev => ({ ...prev, auditor_status: value }))}
                            className="space-y-2"
                          >
                            <div className="flex items-center space-x-3 p-3 rounded-lg border-2 border-green-200 hover:bg-green-50 transition-colors">
                              <RadioGroupItem value="confirm" id="confirm" className="text-green-600" />
                              <Label htmlFor="confirm" className="flex-1 cursor-pointer font-medium text-green-900">
                                ✅ Confirm (Sesuai/Memenuhi Persyaratan)
                              </Label>
                            </div>
                            <div className="flex items-center space-x-3 p-3 rounded-lg border-2 border-orange-200 hover:bg-orange-50 transition-colors">
                              <RadioGroupItem value="non-confirm-minor" id="non_confirm_minor" className="text-orange-600" />
                              <Label htmlFor="non_confirm_minor" className="flex-1 cursor-pointer font-medium text-orange-900">
                                ⚠️ Non-Confirm Minor (Temuan Kecil)
                              </Label>
                            </div>
                            <div className="flex items-center space-x-3 p-3 rounded-lg border-2 border-red-200 hover:bg-red-50 transition-colors">
                              <RadioGroupItem value="non-confirm-major" id="non_confirm_major" className="text-red-600" />
                              <Label htmlFor="non_confirm_major" className="flex-1 cursor-pointer font-medium text-red-900">
                                ❌ Non-Confirm Major (Temuan Besar/Serius)
                              </Label>
                            </div>
                          </RadioGroup>
                        </div>

                        {/* Notes */}
                        <div className="space-y-2">
                          <Label htmlFor="auditor_notes" className="text-sm font-semibold text-slate-900">
                            Catatan & Rekomendasi Auditor
                          </Label>
                          <Textarea
                            id="auditor_notes"
                            value={auditorAssessment.auditor_notes}
                            onChange={(e) => setAuditorAssessment(prev => ({ ...prev, auditor_notes: e.target.value }))}
                            placeholder="Masukkan catatan temuan, rekomendasi perbaikan, atau hal-hal yang perlu ditindaklanjuti..."
                            className="min-h-[100px] resize-y"
                            data-testid="auditor-notes-textarea"
                          />
                        </div>

                        {/* Due Date */}
                        <div className="space-y-2">
                          <Label className="text-sm font-semibold text-slate-900">
                            Tanggal Kesepakatan Penyelesaian <span className="text-red-500">*</span>
                          </Label>
                          <Popover>
                            <PopoverTrigger asChild>
                              <Button
                                variant="outline"
                                className="w-full justify-start text-left font-normal"
                                data-testid="date-picker-button"
                              >
                                <CalendarIcon className="mr-2 h-4 w-4" />
                                {auditorAssessment.agreed_date ? (
                                  format(new Date(auditorAssessment.agreed_date), 'PPP', { locale: idLocale })
                                ) : (
                                  <span className="text-slate-500">Pilih tanggal...</span>
                                )}
                              </Button>
                            </PopoverTrigger>
                            <PopoverContent className="w-auto p-0" align="start">
                              <Calendar
                                mode="single"
                                selected={auditorAssessment.agreed_date ? new Date(auditorAssessment.agreed_date) : undefined}
                                onSelect={(date) => {
                                  if (date) {
                                    setAuditorAssessment(prev => ({ 
                                      ...prev, 
                                      agreed_date: date.toISOString().split('T')[0] 
                                    }));
                                  }
                                }}
                                initialFocus
                                locale={idLocale}
                              />
                            </PopoverContent>
                          </Popover>
                          <p className="text-xs text-slate-500">
                            Tanggal kesepakatan kapan temuan/rekomendasi akan diselesaikan oleh auditee
                          </p>
                        </div>

                        {/* Save Button */}
                        <div className="pt-3 border-t flex justify-end">
                          <Button
                            onClick={handleSaveAuditorAssessment}
                            disabled={savingAssessment}
                            className="bg-emerald-600 hover:bg-emerald-700"
                            data-testid="save-assessment-button"
                          >
                            {savingAssessment ? (
                              <>
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                Menyimpan...
                              </>
                            ) : (
                              <>
                                <Save className="w-4 h-4 mr-2" />
                                Simpan Penilaian Auditor
                              </>
                            )}
                          </Button>
                        </div>

                        {/* Status Display if already assessed */}
                        {auditResult.auditor_status && (
                          <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg">
                            <p className="text-xs font-semibold text-slate-700 mb-2">Status Penilaian Tersimpan:</p>
                            <Badge 
                              variant="outline" 
                              className={`${
                                auditResult.auditor_status === 'confirm' ? 'border-green-500 text-green-700 bg-green-50' :
                                auditResult.auditor_status === 'non-confirm-minor' ? 'border-orange-500 text-orange-700 bg-orange-50' :
                                'border-red-500 text-red-700 bg-red-50'
                              }`}
                            >
                              {auditResult.auditor_status === 'confirm' ? '✅ Confirm' :
                               auditResult.auditor_status === 'non-confirm-minor' ? '⚠️ Non-Confirm Minor' :
                               '❌ Non-Confirm Major'}
                            </Badge>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  )}
                </>
              ) : (
                <div className="text-center py-12">
                  <FileText className="w-12 h-12 mx-auto text-slate-300 mb-4" />
                  <p className="text-slate-600">Pilih klausul untuk mulai mengupload dokumen</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </Layout>
  );
};

export default AuditPage;