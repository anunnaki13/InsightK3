import React, { useContext, useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { AppContext } from '../App';
import Layout from '../components/Layout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { AlertTriangle, BellRing, Plus, RefreshCcw, ShieldAlert, Siren, Wrench } from 'lucide-react';
import { toast } from 'sonner';

const emptyEquipmentForm = {
  equipment_type: '',
  equipment_subtype: '',
  name: '',
  brand: '',
  serial_number: '',
  area_code: '',
  sub_location: '',
  capacity: '',
  status: 'ready',
  expiry_date: '',
  certificate_expiry: '',
};

const emptyInspectionForm = {
  inspection_date: '',
  overall_condition: 'good',
  findings: '',
  action_taken: '',
  next_inspection_date: '',
  checklist_results: '',
};

const readinessTone = (readiness) => {
  if (readiness < 60) return 'bg-rose-100 text-rose-700';
  if (readiness < 85) return 'bg-amber-100 text-amber-700';
  return 'bg-emerald-100 text-emerald-700';
};

const EquipmentPage = () => {
  const { API, user } = useContext(AppContext);
  const [areas, setAreas] = useState([]);
  const [equipmentTypes, setEquipmentTypes] = useState({});
  const [items, setItems] = useState([]);
  const [areaSummary, setAreaSummary] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [overdue, setOverdue] = useState([]);
  const [expiring, setExpiring] = useState([]);
  const [selectedEquipmentId, setSelectedEquipmentId] = useState(null);
  const [selectedEquipment, setSelectedEquipment] = useState(null);
  const [inspections, setInspections] = useState([]);
  const [checklistForm, setChecklistForm] = useState([]);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [equipmentDialogOpen, setEquipmentDialogOpen] = useState(false);
  const [inspectionDialogOpen, setInspectionDialogOpen] = useState(false);
  const [equipmentForm, setEquipmentForm] = useState(emptyEquipmentForm);
  const [inspectionForm, setInspectionForm] = useState(emptyInspectionForm);

  const canWrite = ['admin', 'risk_officer', 'surveyor'].includes(user?.role);

  const areaMap = useMemo(
    () => Object.fromEntries(areas.map((area) => [area.code, area.name])),
    [areas],
  );

  const metrics = useMemo(() => ({
    total: items.length,
    critical: items.filter((item) => ['expired', 'missing'].includes(item.status)).length,
    warning: items.filter((item) => item.status === 'needs_maintenance').length,
    averageReadiness: items.length ? Math.round(items.reduce((sum, item) => sum + (item.readiness_percentage || 0), 0) / items.length) : 0,
  }), [items]);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (selectedEquipmentId) {
      fetchEquipmentDetail(selectedEquipmentId);
    }
  }, [selectedEquipmentId]);

  useEffect(() => {
    if (!selectedEquipmentId && items[0]?.id) {
      setSelectedEquipmentId(items[0].id);
      return;
    }
    if (selectedEquipmentId && !items.some((item) => item.id === selectedEquipmentId)) {
      setSelectedEquipmentId(items[0]?.id || null);
    }
  }, [items, selectedEquipmentId]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [areasRes, typesRes, itemsRes, summaryRes, alertsRes, overdueRes, expiringRes] = await Promise.all([
        axios.get(`${API}/risk/areas`),
        axios.get(`${API}/equipment/types`),
        axios.get(`${API}/equipment`),
        axios.get(`${API}/equipment/areas-summary`),
        axios.get(`${API}/equipment/alerts?is_acknowledged=false`),
        axios.get(`${API}/equipment/overdue-inspection`),
        axios.get(`${API}/equipment/expiring?days=30`),
      ]);
      setAreas(areasRes.data || []);
      setEquipmentTypes(typesRes.data || {});
      setItems(itemsRes.data.items || []);
      setAreaSummary(summaryRes.data.areas || []);
      setAlerts(alertsRes.data.items || []);
      setOverdue(overdueRes.data.items || []);
      setExpiring(expiringRes.data.items || []);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal memuat workspace equipment');
    } finally {
      setLoading(false);
    }
  };

  const fetchEquipmentDetail = async (equipmentId) => {
    setDetailLoading(true);
    try {
      const [detailRes, inspectionsRes, checklistRes] = await Promise.all([
        axios.get(`${API}/equipment/${equipmentId}`),
        axios.get(`${API}/equipment/${equipmentId}/inspections`),
        axios.get(`${API}/equipment/${equipmentId}/checklist-form`),
      ]);
      setSelectedEquipment(detailRes.data);
      setInspections(inspectionsRes.data.items || []);
      setChecklistForm(checklistRes.data.required_checks || []);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal memuat detail equipment');
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCreateEquipment = async (event) => {
    event.preventDefault();
    try {
      await axios.post(`${API}/equipment`, {
        ...equipmentForm,
        expiry_date: equipmentForm.expiry_date || null,
        certificate_expiry: equipmentForm.certificate_expiry || null,
      });
      toast.success('Equipment berhasil ditambahkan');
      setEquipmentDialogOpen(false);
      setEquipmentForm(emptyEquipmentForm);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal menambahkan equipment');
    }
  };

  const handleInspectEquipment = async (event) => {
    event.preventDefault();
    if (!selectedEquipmentId) return;
    try {
      const checks = inspectionForm.checklist_results
        .split('\n')
        .map((line) => line.trim())
        .filter(Boolean)
        .map((line) => ({ check: line, result: 'ok', note: '' }));

      await axios.post(`${API}/equipment/${selectedEquipmentId}/inspect`, {
        inspection_date: inspectionForm.inspection_date,
        overall_condition: inspectionForm.overall_condition,
        findings: inspectionForm.findings || null,
        action_taken: inspectionForm.action_taken || null,
        next_inspection_date: inspectionForm.next_inspection_date,
        checklist_results: checks,
      });
      toast.success('Inspeksi berhasil dicatat');
      setInspectionDialogOpen(false);
      setInspectionForm(emptyInspectionForm);
      fetchData();
      fetchEquipmentDetail(selectedEquipmentId);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal mencatat inspeksi');
    }
  };

  const handleRunAlertCheck = async () => {
    try {
      await axios.post(`${API}/equipment/run-alert-check`);
      toast.success('Alert check selesai dijalankan');
      fetchData();
      if (selectedEquipmentId) {
        fetchEquipmentDetail(selectedEquipmentId);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal menjalankan alert check');
    }
  };

  const handleAcknowledgeAlert = async (alertId) => {
    try {
      await axios.put(`${API}/equipment/alerts/${alertId}/acknowledge`);
      toast.success('Alert diacknowledge');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal acknowledge alert');
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex h-96 items-center justify-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-[22px] bg-slate-950 text-white shadow-[0_20px_50px_rgba(15,23,42,0.24)]">
            <div className="h-6 w-6 animate-spin rounded-full border-[3px] border-white/40 border-t-white" />
          </div>
        </div>
      </Layout>
    );
  }

  const availableSubtypes = equipmentForm.equipment_type ? (equipmentTypes[equipmentForm.equipment_type]?.subtypes || []) : [];

  return (
    <Layout>
      <div className="space-y-6" data-testid="equipment-page">
        <section className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
          <Card className="overflow-hidden rounded-[30px] border-0 bg-[linear-gradient(135deg,#3d2614_0%,#7a4b28_58%,#a36b3a_100%)] text-white shadow-[0_32px_90px_rgba(61,38,20,0.24)]">
            <CardContent className="p-7 md:p-8">
              <p className="text-[11px] font-bold uppercase tracking-[0.28em] text-amber-100/75">Module D</p>
              <h1 className="mt-3 text-4xl font-extrabold leading-tight md:text-5xl">Emergency equipment readiness sekarang punya fondasi inventory dan alert.</h1>
              <p className="mt-4 max-w-2xl text-sm leading-6 text-amber-50/80 md:text-base">
                Register alat, inspeksi periodik, readiness calculation, area summary, dan alert aktif sudah berjalan dalam satu workspace.
              </p>
            </CardContent>
          </Card>

          <Card className="rounded-[30px] border-white/70 bg-white/80 shadow-[0_24px_70px_rgba(45,68,58,0.10)] backdrop-blur-xl">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Readiness Snapshot</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-[20px] bg-slate-50 px-4 py-3">
                <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Total</p>
                <p className="mt-2 text-3xl font-extrabold text-slate-950">{metrics.total}</p>
              </div>
              <div className="rounded-[20px] bg-emerald-50 px-4 py-3">
                <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-emerald-700">Avg Readiness</p>
                <p className="mt-2 text-3xl font-extrabold text-emerald-800">{metrics.averageReadiness}%</p>
              </div>
              <div className="rounded-[20px] bg-amber-50 px-4 py-3">
                <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-amber-700">Warning</p>
                <p className="mt-2 text-3xl font-extrabold text-amber-800">{metrics.warning}</p>
              </div>
              <div className="rounded-[20px] bg-rose-50 px-4 py-3">
                <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-rose-700">Critical</p>
                <p className="mt-2 text-3xl font-extrabold text-rose-800">{metrics.critical}</p>
              </div>
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-5 xl:grid-cols-[0.92fr_1.08fr]">
          <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
            <CardHeader className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <CardTitle className="text-xl">Equipment Register</CardTitle>
                <p className="mt-1 text-sm text-slate-600">Daftar alat tanggap darurat yang aktif di dalam unit.</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button variant="outline" className="rounded-[16px]" onClick={fetchData}>
                  <RefreshCcw className="mr-2 h-4 w-4" />
                  Refresh
                </Button>
                {canWrite && (
                  <>
                    <Button variant="outline" className="rounded-[16px]" onClick={handleRunAlertCheck}>
                      <BellRing className="mr-2 h-4 w-4" />
                      Run Alert Check
                    </Button>
                    <Dialog open={equipmentDialogOpen} onOpenChange={setEquipmentDialogOpen}>
                      <DialogTrigger asChild>
                        <Button className="rounded-[16px] bg-slate-950 hover:bg-slate-800">
                          <Plus className="mr-2 h-4 w-4" />
                          Tambah Alat
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-3xl rounded-[28px]">
                        <DialogHeader>
                          <DialogTitle>Tambah Emergency Equipment</DialogTitle>
                        </DialogHeader>
                        <form onSubmit={handleCreateEquipment} className="grid gap-4 md:grid-cols-2">
                          <div className="space-y-2">
                            <Label>Equipment Type</Label>
                            <Select value={equipmentForm.equipment_type} onValueChange={(value) => setEquipmentForm({ ...equipmentForm, equipment_type: value, equipment_subtype: '' })}>
                              <SelectTrigger className="h-12 rounded-[16px]"><SelectValue placeholder="Pilih tipe" /></SelectTrigger>
                              <SelectContent>
                                {Object.entries(equipmentTypes).map(([key, meta]) => <SelectItem key={key} value={key}>{meta.name}</SelectItem>)}
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="space-y-2">
                            <Label>Subtype</Label>
                            <Select value={equipmentForm.equipment_subtype} onValueChange={(value) => setEquipmentForm({ ...equipmentForm, equipment_subtype: value })}>
                              <SelectTrigger className="h-12 rounded-[16px]"><SelectValue placeholder="Pilih subtype" /></SelectTrigger>
                              <SelectContent>
                                {availableSubtypes.map((item) => <SelectItem key={item} value={item}>{item}</SelectItem>)}
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="space-y-2">
                            <Label>Area</Label>
                            <Select value={equipmentForm.area_code} onValueChange={(value) => setEquipmentForm({ ...equipmentForm, area_code: value })}>
                              <SelectTrigger className="h-12 rounded-[16px]"><SelectValue placeholder="Pilih area" /></SelectTrigger>
                              <SelectContent>
                                {areas.map((area) => <SelectItem key={area.code} value={area.code}>{area.name}</SelectItem>)}
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="space-y-2">
                            <Label>Status</Label>
                            <Select value={equipmentForm.status} onValueChange={(value) => setEquipmentForm({ ...equipmentForm, status: value })}>
                              <SelectTrigger className="h-12 rounded-[16px]"><SelectValue /></SelectTrigger>
                              <SelectContent>
                                {['ready', 'needs_maintenance', 'expired', 'missing'].map((item) => <SelectItem key={item} value={item}>{item}</SelectItem>)}
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="space-y-2 md:col-span-2">
                            <Label>Nama / Label</Label>
                            <Input value={equipmentForm.name} onChange={(event) => setEquipmentForm({ ...equipmentForm, name: event.target.value })} className="h-12 rounded-[16px]" />
                          </div>
                          <div className="space-y-2">
                            <Label>Brand</Label>
                            <Input value={equipmentForm.brand} onChange={(event) => setEquipmentForm({ ...equipmentForm, brand: event.target.value })} className="h-12 rounded-[16px]" />
                          </div>
                          <div className="space-y-2">
                            <Label>Serial Number</Label>
                            <Input value={equipmentForm.serial_number} onChange={(event) => setEquipmentForm({ ...equipmentForm, serial_number: event.target.value })} className="h-12 rounded-[16px]" />
                          </div>
                          <div className="space-y-2 md:col-span-2">
                            <Label>Sub Location</Label>
                            <Input value={equipmentForm.sub_location} onChange={(event) => setEquipmentForm({ ...equipmentForm, sub_location: event.target.value })} required className="h-12 rounded-[16px]" />
                          </div>
                          <div className="space-y-2">
                            <Label>Capacity</Label>
                            <Input value={equipmentForm.capacity} onChange={(event) => setEquipmentForm({ ...equipmentForm, capacity: event.target.value })} className="h-12 rounded-[16px]" />
                          </div>
                          <div className="space-y-2">
                            <Label>Expiry Date</Label>
                            <Input type="date" value={equipmentForm.expiry_date} onChange={(event) => setEquipmentForm({ ...equipmentForm, expiry_date: event.target.value })} className="h-12 rounded-[16px]" />
                          </div>
                          <div className="space-y-2 md:col-span-2">
                            <Label>Certificate Expiry</Label>
                            <Input type="date" value={equipmentForm.certificate_expiry} onChange={(event) => setEquipmentForm({ ...equipmentForm, certificate_expiry: event.target.value })} className="h-12 rounded-[16px]" />
                          </div>
                          <div className="md:col-span-2">
                            <Button type="submit" className="h-12 w-full rounded-[18px] bg-amber-700 hover:bg-amber-800">Simpan Equipment</Button>
                          </div>
                        </form>
                      </DialogContent>
                    </Dialog>
                  </>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {items.length === 0 ? (
                <div className="rounded-[22px] bg-slate-50 p-10 text-center text-slate-500">Belum ada equipment terdaftar.</div>
              ) : (
                items.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setSelectedEquipmentId(item.id)}
                    className={`w-full rounded-[22px] border p-4 text-left transition ${
                      selectedEquipmentId === item.id
                        ? 'border-amber-800 bg-amber-950 text-white shadow-[0_24px_60px_rgba(120,53,15,0.22)]'
                        : 'border-slate-100 bg-slate-50/70 text-slate-950 hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <span className={`rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.16em] ${selectedEquipmentId === item.id ? 'bg-white text-amber-950' : 'bg-slate-950 text-white'}`}>{item.equipment_code}</span>
                          <span className={`rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.16em] ${readinessTone(item.readiness_percentage)}`}>{item.readiness_percentage}%</span>
                        </div>
                        <p className="mt-3 text-lg font-bold">{item.name || item.equipment_type}</p>
                        <p className={`mt-2 text-sm ${selectedEquipmentId === item.id ? 'text-amber-100' : 'text-slate-600'}`}>{areaMap[item.area_code] || item.area_code} • {item.sub_location}</p>
                      </div>
                      <p className={`text-xs font-bold uppercase tracking-[0.16em] ${selectedEquipmentId === item.id ? 'text-amber-100' : 'text-slate-500'}`}>{item.status}</p>
                    </div>
                  </button>
                ))
              )}
            </CardContent>
          </Card>

          <div className="space-y-5">
            <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
              <CardHeader>
                <CardTitle className="text-xl">Equipment Detail</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {detailLoading ? (
                  <div className="rounded-[20px] bg-slate-50 p-6 text-sm text-slate-500">Memuat detail equipment...</div>
                ) : !selectedEquipment ? (
                  <div className="rounded-[20px] bg-slate-50 p-6 text-sm text-slate-500">Pilih equipment untuk melihat detail.</div>
                ) : (
                  <>
                    <div className="rounded-[22px] bg-slate-950 p-5 text-white">
                      <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-slate-300">{selectedEquipment.equipment_code}</p>
                      <h3 className="mt-3 text-2xl font-extrabold">{selectedEquipment.name || selectedEquipment.equipment_type}</h3>
                      <p className="mt-3 text-sm leading-6 text-slate-200">{areaMap[selectedEquipment.area_code] || selectedEquipment.area_code} • {selectedEquipment.sub_location}</p>
                    </div>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <div className="rounded-[20px] bg-slate-50 px-4 py-3">
                        <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Status</p>
                        <p className="mt-2 font-semibold text-slate-950">{selectedEquipment.status}</p>
                      </div>
                      <div className="rounded-[20px] bg-slate-50 px-4 py-3">
                        <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Next Inspection</p>
                        <p className="mt-2 font-semibold text-slate-950">{selectedEquipment.next_inspection_date || '-'}</p>
                      </div>
                    </div>
                    <div className="rounded-[22px] border border-slate-100 bg-slate-50/80 p-4">
                      <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                        <Wrench className="h-4 w-4" />
                        Checklist Template
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {checklistForm.map((item) => (
                          <span key={item} className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-600">{item}</span>
                        ))}
                      </div>
                    </div>
                    {canWrite && (
                      <Dialog open={inspectionDialogOpen} onOpenChange={setInspectionDialogOpen}>
                        <DialogTrigger asChild>
                          <Button variant="outline" className="rounded-[16px]">
                            <ShieldAlert className="mr-2 h-4 w-4" />
                            Catat Inspeksi
                          </Button>
                        </DialogTrigger>
                        <DialogContent className="max-w-2xl rounded-[28px]">
                          <DialogHeader>
                            <DialogTitle>Catat Inspeksi Equipment</DialogTitle>
                          </DialogHeader>
                          <form onSubmit={handleInspectEquipment} className="grid gap-4">
                            <div className="grid gap-4 md:grid-cols-2">
                              <div className="space-y-2">
                                <Label>Inspection Date</Label>
                                <Input type="date" value={inspectionForm.inspection_date} onChange={(event) => setInspectionForm({ ...inspectionForm, inspection_date: event.target.value })} required className="h-12 rounded-[16px]" />
                              </div>
                              <div className="space-y-2">
                                <Label>Next Inspection Date</Label>
                                <Input type="date" value={inspectionForm.next_inspection_date} onChange={(event) => setInspectionForm({ ...inspectionForm, next_inspection_date: event.target.value })} required className="h-12 rounded-[16px]" />
                              </div>
                            </div>
                            <div className="space-y-2">
                              <Label>Overall Condition</Label>
                              <Select value={inspectionForm.overall_condition} onValueChange={(value) => setInspectionForm({ ...inspectionForm, overall_condition: value })}>
                                <SelectTrigger className="h-12 rounded-[16px]"><SelectValue /></SelectTrigger>
                                <SelectContent>
                                  {['good', 'fair', 'poor', 'failed'].map((item) => <SelectItem key={item} value={item}>{item}</SelectItem>)}
                                </SelectContent>
                              </Select>
                            </div>
                            <div className="space-y-2">
                              <Label>Checklist Results</Label>
                              <Textarea value={inspectionForm.checklist_results} onChange={(event) => setInspectionForm({ ...inspectionForm, checklist_results: event.target.value })} placeholder={checklistForm.join('\n')} rows={5} className="rounded-[16px]" />
                            </div>
                            <div className="space-y-2">
                              <Label>Findings</Label>
                              <Textarea value={inspectionForm.findings} onChange={(event) => setInspectionForm({ ...inspectionForm, findings: event.target.value })} rows={3} className="rounded-[16px]" />
                            </div>
                            <div className="space-y-2">
                              <Label>Action Taken</Label>
                              <Textarea value={inspectionForm.action_taken} onChange={(event) => setInspectionForm({ ...inspectionForm, action_taken: event.target.value })} rows={3} className="rounded-[16px]" />
                            </div>
                            <Button type="submit" className="h-12 rounded-[18px] bg-amber-700 hover:bg-amber-800">Simpan Inspeksi</Button>
                          </form>
                        </DialogContent>
                      </Dialog>
                    )}
                  </>
                )}
              </CardContent>
            </Card>

            <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-xl">
                  <Siren className="h-5 w-5 text-amber-600" />
                  Area Summary
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {areaSummary.length === 0 ? (
                  <div className="rounded-[20px] bg-slate-50 p-6 text-sm text-slate-500">Belum ada ringkasan area.</div>
                ) : (
                  areaSummary.map((row) => (
                    <div key={row._id} className="rounded-[20px] bg-slate-50 px-4 py-3">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="font-semibold text-slate-950">{areaMap[row._id] || row._id}</p>
                          <p className="text-xs text-slate-500">{row.total} alat • {row.warning} warning • {row.critical} critical</p>
                        </div>
                        <p className="text-lg font-extrabold text-slate-950">{Math.round(row.avg_readiness || 0)}%</p>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>
        </section>

        <section className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
          <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-xl">
                <BellRing className="h-5 w-5 text-rose-600" />
                Active Alerts
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {alerts.length === 0 ? (
                <div className="rounded-[20px] bg-slate-50 p-6 text-sm text-slate-500">Tidak ada alert aktif.</div>
              ) : (
                alerts.map((alert) => (
                  <div key={alert.id} className="rounded-[22px] border border-slate-100 bg-slate-50/80 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="rounded-full bg-slate-950 px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.16em] text-white">{alert.equipment_code}</span>
                          <span className={`rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.16em] ${alert.severity === 'critical' ? 'bg-rose-100 text-rose-700' : alert.severity === 'warning' ? 'bg-amber-100 text-amber-700' : 'bg-sky-100 text-sky-700'}`}>{alert.severity}</span>
                        </div>
                        <p className="mt-3 text-sm leading-6 text-slate-700">{alert.alert_message}</p>
                        <p className="mt-2 text-xs text-slate-500">Due {alert.due_date || '-'}</p>
                      </div>
                      {canWrite && (
                        <Button variant="outline" onClick={() => handleAcknowledgeAlert(alert.id)} className="rounded-[16px]">
                          Ack
                        </Button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          <div className="space-y-5">
            <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-xl">
                  <AlertTriangle className="h-5 w-5 text-amber-600" />
                  Overdue Inspection
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {overdue.length === 0 ? (
                  <div className="rounded-[20px] bg-slate-50 p-6 text-sm text-slate-500">Tidak ada alat overdue inspeksi.</div>
                ) : (
                  overdue.slice(0, 8).map((item) => (
                    <div key={item.id} className="rounded-[18px] bg-slate-50 px-4 py-3 text-sm text-slate-700">
                      {item.equipment_code} • {item.next_inspection_date}
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-xl">
                  <ShieldAlert className="h-5 w-5 text-rose-600" />
                  Expiring Soon
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {expiring.length === 0 ? (
                  <div className="rounded-[20px] bg-slate-50 p-6 text-sm text-slate-500">Tidak ada alat yang akan expired dalam 30 hari.</div>
                ) : (
                  expiring.slice(0, 8).map((item) => (
                    <div key={item.id} className="rounded-[18px] bg-slate-50 px-4 py-3 text-sm text-slate-700">
                      {item.equipment_code} • {item.expiry_date}
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
              <CardHeader>
                <CardTitle className="text-xl">Inspection History</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {inspections.length === 0 ? (
                  <div className="rounded-[20px] bg-slate-50 p-6 text-sm text-slate-500">Belum ada histori inspeksi untuk alat ini.</div>
                ) : (
                  inspections.map((inspection) => (
                    <div key={inspection.id} className="rounded-[18px] bg-slate-50 px-4 py-3 text-sm text-slate-700">
                      {inspection.inspection_date} • {inspection.overall_condition} • next {inspection.next_inspection_date}
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>
        </section>
      </div>
    </Layout>
  );
};

export default EquipmentPage;
