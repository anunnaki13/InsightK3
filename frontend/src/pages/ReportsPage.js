import React, { useState, useContext } from 'react';
import { AppContext } from '../App';
import axios from 'axios';
import Layout from '../components/Layout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FileText, Download, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

const ReportsPage = () => {
  const { API } = useContext(AppContext);
  const [generating, setGenerating] = useState(false);

  const handleGenerateReport = async () => {
    setGenerating(true);
    try {
      const response = await axios.post(`${API}/reports/generate`);
      const { filename, content } = response.data;
      
      const blob = new Blob([Uint8Array.from(atob(content), c => c.charCodeAt(0))], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast.success('Laporan berhasil diunduh!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal membuat laporan');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <Layout>
      <div className="space-y-6" data-testid="reports-page">
        <div>
          <h1 className="text-4xl font-bold mb-2" style={{ fontFamily: 'Manrope, sans-serif', color: '#1a1a1a' }}>Laporan Audit</h1>
          <p className="text-slate-600">Generate laporan audit SMK3 dalam format PDF</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="shadow-md hover:shadow-lg transition-shadow" data-testid="report-card">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <FileText className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <CardTitle>Laporan Lengkap</CardTitle>
                  <p className="text-sm text-slate-600">Ringkasan dan detail audit semua kriteria</p>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 mb-6 text-sm text-slate-600">
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-emerald-600 rounded-full"></div>
                  Statistik audit keseluruhan
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-emerald-600 rounded-full"></div>
                  Pencapaian audit berbasis penilaian auditor
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-emerald-600 rounded-full"></div>
                  Breakdown Confirm/Non-Confirm per kriteria
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-emerald-600 rounded-full"></div>
                  Detail penilaian auditor per klausul
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-emerald-600 rounded-full"></div>
                  Catatan & tanggal kesepakatan auditor
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-emerald-600 rounded-full"></div>
                  Analisis AI sebagai referensi
                </li>
              </ul>
              <Button
                onClick={handleGenerateReport}
                disabled={generating}
                className="w-full bg-blue-600 hover:bg-blue-700"
                data-testid="generate-report-button"
              >
                {generating ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Membuat Laporan...
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4 mr-2" />
                    Generate & Download PDF
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          <Card className="shadow-md" data-testid="info-card">
            <CardHeader>
              <CardTitle>Informasi Laporan</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="font-medium text-sm mb-2">Format Laporan</h4>
                <p className="text-sm text-slate-600">
                  Laporan dihasilkan dalam format PDF profesional yang mencakup semua data audit terkini.
                </p>
              </div>
              <div>
                <h4 className="font-medium text-sm mb-2">Isi Laporan</h4>
                <p className="text-sm text-slate-600">
                  Laporan berisi ringkasan eksekutif, skor per kriteria, tabel detail hasil audit, 
                  serta analisis kekuatan dan area yang perlu ditingkatkan.
                </p>
              </div>
              <div>
                <h4 className="font-medium text-sm mb-2">Penggunaan</h4>
                <p className="text-sm text-slate-600">
                  Laporan dapat digunakan untuk presentasi manajemen, dokumentasi audit, 
                  dan perencanaan perbaikan berkelanjutan.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="shadow-md bg-gradient-to-br from-emerald-50 to-blue-50">
          <CardContent className="pt-6">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-white rounded-lg shadow-sm">
                <FileText className="w-6 h-6 text-emerald-600" />
              </div>
              <div>
                <h3 className="font-semibold mb-2">Tips Penggunaan Laporan</h3>
                <ul className="space-y-1 text-sm text-slate-700">
                  <li>• Generate laporan secara berkala untuk tracking progress audit</li>
                  <li>• Bagikan dengan stakeholder terkait untuk transparansi</li>
                  <li>• Gunakan sebagai basis untuk membuat action plan perbaikan</li>
                  <li>• Simpan laporan sebagai dokumentasi historis audit</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
};

export default ReportsPage;