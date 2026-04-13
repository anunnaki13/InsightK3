import React, { useState, useEffect, useContext } from 'react';
import { AppContext } from '../App';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { BarChart3, CheckCircle2, XCircle, FileCheck, TrendingUp, AlertTriangle, Download, Archive } from 'lucide-react';
import { toast } from 'sonner';

const DashboardPage = () => {
  const { API } = useContext(AppContext);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    fetchDashboard();
    fetchNotifications();
  }, []);

  const fetchDashboard = async () => {
    try {
      const response = await axios.get(`${API}/audit/dashboard`);
      setStats(response.data);
    } catch (error) {
      toast.error('Gagal memuat data dashboard');
    } finally {
      setLoading(false);
    }
  };

  const fetchNotifications = async () => {
    try {
      const response = await axios.get(`${API}/recommendations/notifications`);
      setNotifications(response.data.notifications || []);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  const handleDownloadAllEvidence = () => {
    const downloadUrl = `${API}/audit/download-all-evidence`;
    window.open(downloadUrl, '_blank');
    toast.success('Mengunduh semua evidence...');
  };

  const handleDownloadCriteriaEvidence = (criteriaId, criteriaName) => {
    const downloadUrl = `${API}/audit/download-criteria-evidence/${criteriaId}`;
    window.open(downloadUrl, '_blank');
    toast.success(`Mengunduh evidence ${criteriaName}...`);
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

  const completionPercentage = stats ? (stats.audited_clauses / stats.total_clauses) * 100 : 0;

  return (
    <Layout>
      <div className="space-y-6" data-testid="dashboard-page">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-4xl font-bold mb-2" style={{ fontFamily: 'Manrope, sans-serif', color: '#1a1a1a' }}>Dashboard Audit SMK3</h1>
            <p className="text-slate-600">Ringkasan status audit keselamatan dan kesehatan kerja</p>
            <div className="mt-2 flex items-center gap-4 text-xs text-slate-500">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-green-500"></span>
                85-100%: Memuaskan
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-yellow-500"></span>
                60-84%: Baik
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-red-500"></span>
                0-59%: Kurang
              </span>
              <span className="ml-2 text-slate-400">| Standar: PP 50/2012 & Permenaker 26/2014</span>
            </div>
          </div>
          <Button
            onClick={handleDownloadAllEvidence}
            className="bg-blue-600 hover:bg-blue-700"
            data-testid="download-all-evidence-button"
          >
            <Archive className="w-4 h-4 mr-2" />
            Download Semua Evidence
          </Button>
        </div>

        {/* Notifikasi */}
        {notifications.length > 0 && (
          <Card className="border-l-4 border-orange-500 bg-orange-50" data-testid="notifications-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-orange-700">
                <AlertTriangle className="w-5 h-5" />
                Notifikasi Deadline
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {notifications.slice(0, 3).map((notif) => (
                  <div key={notif.id} className="flex items-start gap-3 p-3 bg-white rounded-lg" data-testid="notification-item">
                    <div className={`p-2 rounded-full ${notif.urgency === 'critical' ? 'bg-red-100' : 'bg-orange-100'}`}>
                      <AlertTriangle className={`w-4 h-4 ${notif.urgency === 'critical' ? 'text-red-600' : 'text-orange-600'}`} />
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-sm">{notif.clause_number}: {notif.clause_title}</p>
                      <p className="text-xs text-slate-600 mt-1">{notif.recommendation.substring(0, 100)}...</p>
                      <p className={`text-xs mt-1 font-medium ${notif.urgency === 'critical' ? 'text-red-600' : 'text-orange-600'}`}>
                        {notif.days_left <= 0 ? 'Sudah melewati deadline!' : `${notif.days_left} hari lagi`}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="shadow-md hover:shadow-lg transition-shadow" data-testid="total-clauses-card">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">Total Klausul</CardTitle>
              <FileCheck className="w-5 h-5 text-slate-400" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold" style={{ fontFamily: 'Manrope, sans-serif' }}>{stats?.total_clauses || 0}</div>
              <p className="text-xs text-slate-500 mt-1">Klausul audit yang harus dipenuhi</p>
            </CardContent>
          </Card>

          <Card className="shadow-md hover:shadow-lg transition-shadow" data-testid="audited-clauses-card">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">Teraudit</CardTitle>
              <BarChart3 className="w-5 h-5 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-600" style={{ fontFamily: 'Manrope, sans-serif' }}>{stats?.audited_clauses || 0}</div>
              <Progress value={completionPercentage} className="mt-2" />
              <p className="text-xs text-slate-500 mt-1">{completionPercentage.toFixed(1)}% selesai</p>
            </CardContent>
          </Card>

          <Card className="shadow-md hover:shadow-lg transition-shadow" data-testid="average-score-card">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">Skor AI (Referensi)</CardTitle>
              <TrendingUp className="w-5 h-5 text-blue-400" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-500" style={{ fontFamily: 'Manrope, sans-serif' }}>{stats?.average_score?.toFixed(1) || 0}</div>
              <p className="text-xs text-slate-500 mt-1">Avg AI score (tools bantuan)</p>
            </CardContent>
          </Card>

          <Card className="shadow-md hover:shadow-lg transition-shadow border-2 border-emerald-200" data-testid="achievement-card">
            <CardHeader className="flex flex-row items-center justify-between pb-2 bg-emerald-50">
              <CardTitle className="text-sm font-medium text-emerald-700">Pencapaian Audit</CardTitle>
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-emerald-600" style={{ fontFamily: 'Manrope, sans-serif' }}>
                {stats?.achievement_percentage?.toFixed(1) || 0}%
              </div>
              <p className="text-xs text-slate-600 mt-1 font-medium">
                Berbasis penilaian auditor
              </p>
              <p className="text-xs text-slate-500 mt-1">
                {stats?.confirm_count || 0} dari {stats?.total_clauses || 0} klausul Confirm
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Auditor Assessment Breakdown */}
        {stats?.auditor_assessed_clauses > 0 && (
          <Card className="shadow-md border-l-4 border-emerald-500" data-testid="auditor-assessment-breakdown">
            <CardHeader className="bg-emerald-50">
              <CardTitle className="text-lg text-emerald-900">Breakdown Penilaian Auditor</CardTitle>
              <p className="text-xs text-emerald-700 mt-1">
                {stats?.auditor_assessed_clauses} dari {stats?.total_clauses} klausul telah dinilai oleh auditor
              </p>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-green-50 border-2 border-green-200 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="p-3 bg-green-100 rounded-full">
                      <CheckCircle2 className="w-6 h-6 text-green-600" />
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-green-700" style={{ fontFamily: 'Manrope, sans-serif' }}>
                        {stats?.confirm_count || 0}
                      </div>
                      <p className="text-xs text-green-600 font-medium">Confirm</p>
                      <p className="text-xs text-slate-500">Sesuai persyaratan</p>
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-orange-50 border-2 border-orange-200 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="p-3 bg-orange-100 rounded-full">
                      <AlertTriangle className="w-6 h-6 text-orange-600" />
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-orange-700" style={{ fontFamily: 'Manrope, sans-serif' }}>
                        {stats?.non_confirm_minor_count || 0}
                      </div>
                      <p className="text-xs text-orange-600 font-medium">Non-Confirm Minor</p>
                      <p className="text-xs text-slate-500">Temuan kecil</p>
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-red-50 border-2 border-red-200 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="p-3 bg-red-100 rounded-full">
                      <XCircle className="w-6 h-6 text-red-600" />
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-red-700" style={{ fontFamily: 'Manrope, sans-serif' }}>
                        {stats?.non_confirm_major_count || 0}
                      </div>
                      <p className="text-xs text-red-600 font-medium">Non-Confirm Major</p>
                      <p className="text-xs text-slate-500">Temuan serius</p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Criteria Scores */}
        <Card className="shadow-md" data-testid="criteria-scores-card">
          <CardHeader>
            <CardTitle className="text-xl" style={{ fontFamily: 'Manrope, sans-serif' }}>Skor Per Kriteria Audit</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {stats?.criteria_scores?.map((criteria) => (
                <div key={criteria.id} className="space-y-2" data-testid="criteria-score-item">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <h3 className="font-medium">{criteria.name}</h3>
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          criteria.strength === 'strong' ? 'bg-green-100 text-green-700' :
                          criteria.strength === 'moderate' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-red-100 text-red-700'
                        }`}>
                          {criteria.strength_label || (criteria.strength === 'strong' ? 'Memuaskan' : criteria.strength === 'moderate' ? 'Baik' : 'Kurang')}
                        </span>
                        {criteria.audited_clauses > 0 && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDownloadCriteriaEvidence(criteria.id, criteria.name)}
                            className="h-6 px-2 text-xs text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                            data-testid="download-criteria-evidence-button"
                          >
                            <Download className="w-3 h-3 mr-1" />
                            Download
                          </Button>
                        )}
                      </div>
                      <div className="flex items-center gap-4 mt-1">
                        <p className="text-xs text-slate-500">
                          {criteria.audited_clauses}/{criteria.total_clauses} klausul teraudit
                        </p>
                        {criteria.auditor_assessed_clauses > 0 && (
                          <p className="text-xs text-emerald-600 font-medium">
                            ✓ {criteria.confirm_count} Confirm • 
                            {criteria.non_confirm_minor_count > 0 && ` ⚠ ${criteria.non_confirm_minor_count} NC Minor`}
                            {criteria.non_confirm_major_count > 0 && ` ✗ ${criteria.non_confirm_major_count} NC Major`}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold" style={{ fontFamily: 'Manrope, sans-serif', color: criteria.strength === 'strong' ? '#10b981' : criteria.strength === 'moderate' ? '#f59e0b' : '#ef4444' }}>
                        {criteria.achievement_percentage?.toFixed(1) || '0.0'}%
                      </div>
                      <p className="text-xs text-slate-500">Avg: {criteria.average_score?.toFixed(1) || '0.0'}</p>
                    </div>
                  </div>
                  <Progress
                    value={criteria.achievement_percentage || 0}
                    className={`h-2 ${
                      criteria.strength === 'strong' ? 'bg-green-100' :
                      criteria.strength === 'moderate' ? 'bg-yellow-100' :
                      'bg-red-100'
                    }`}
                  />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
};

export default DashboardPage;