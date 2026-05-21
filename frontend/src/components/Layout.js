import React, { useContext, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { AppContext } from '../App';
import { Button } from '@/components/ui/button';
import {
  ClipboardCheck,
  ClipboardList,
  FileCheck,
  FileText,
  LayoutDashboard,
  ListChecks,
  LogOut,
  Menu,
  PanelsTopLeft,
  ScrollText,
  ShieldAlert,
  ShieldCheck,
  Siren,
  SlidersHorizontal,
} from 'lucide-react';

const Layout = ({ children }) => {
  const { user, logout } = useContext(AppContext);
  const location = useLocation();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const isSurveyor = user?.role === 'surveyor';

  const navigation = [
    { section: 'Audit SMK3', name: 'Dashboard', path: '/', icon: LayoutDashboard, hint: 'Ringkasan eksekutif' },
    { section: 'Audit SMK3', name: 'Kriteria', path: '/criteria', icon: ListChecks, hint: 'Master audit SMK3' },
    { section: 'Audit SMK3', name: 'Klausul', path: '/clauses', icon: FileCheck, hint: 'Knowledge base & mapping' },
    { section: 'Audit SMK3', name: 'Audit', path: '/audit', icon: ClipboardCheck, hint: isSurveyor ? 'Evidence & catatan' : 'Evidence & assessment' },
    { section: 'Audit SMK3', name: isSurveyor ? 'Catatan' : 'Rekomendasi', path: '/recommendations', icon: FileText, hint: isSurveyor ? 'Catatan surveyor' : 'Action tracking' },
    { section: 'Audit SMK3', name: isSurveyor ? 'Laporan Catatan' : 'Laporan', path: '/reports', icon: FileText, hint: isSurveyor ? 'Laporan surveyor' : 'Output manajemen' },
    { section: 'Risk Intelligence', name: 'ERM Risk', path: '/erm-risk', icon: ShieldAlert, hint: 'Risk register awal', roles: ['admin', 'auditor', 'risk_officer', 'management'] },
    { section: 'Risk Intelligence', name: 'Underwriting', path: '/underwriting-survey', icon: ScrollText, hint: 'Survey underwriting', roles: ['admin', 'risk_officer', 'surveyor', 'management'] },
    { section: 'Risk Intelligence', name: 'Field Survey', path: '/field-risk-survey', icon: ClipboardList, hint: 'Survey lapangan', roles: ['admin', 'risk_officer', 'surveyor', 'management'] },
    { section: 'Risk Intelligence', name: 'Equipment', path: '/emergency-equipment', icon: Siren, hint: 'Readiness tanggap darurat', roles: ['admin', 'risk_officer', 'surveyor', 'management'] },
    { section: 'Risk Intelligence', name: 'Heatmap', path: '/risk-heatmap', icon: PanelsTopLeft, hint: 'Dashboard konsolidasi', roles: ['admin', 'auditor', 'risk_officer', 'management'] },
    { section: 'System', name: 'Settings', path: '/settings', icon: SlidersHorizontal, hint: 'Konfigurasi AI & sistem', roles: ['admin'] },
  ].filter((item) => {
    if (user?.role === 'surveyor' && item.section === 'Risk Intelligence') {
      return false;
    }
    return !item.roles || item.roles.includes(user?.role);
  });

  const isActive = (path) => location.pathname === path;
  const activeItem = navigation.find((item) => isActive(item.path)) || navigation[0];
  const roleLabel = user?.role === 'admin'
    ? 'Admin'
    : user?.role === 'auditor'
      ? 'Auditor'
      : user?.role === 'risk_officer'
        ? 'Risk Officer'
        : user?.role === 'management'
          ? 'Management'
          : user?.role === 'surveyor'
            ? 'Surveyor'
            : 'Auditee';

  const navSections = navigation.reduce((sections, item) => {
    const current = sections[item.section] || [];
    return { ...sections, [item.section]: [...current, item] };
  }, {});

  const NavContent = () => (
    <>
      <div className="rounded-[26px] border border-white/75 bg-white/82 p-4 shadow-[0_18px_52px_rgba(38,64,55,0.10)] backdrop-blur-xl">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[linear-gradient(135deg,#0f5f53_0%,#2b8a78_100%)] shadow-[0_12px_24px_rgba(15,95,83,0.22)]">
              <ShieldCheck className="h-5 w-5 text-white" />
            </div>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-emerald-800/70">InsightK3</p>
              <h1 className="text-lg font-extrabold text-slate-900">Audit Workbench</h1>
            </div>
          </div>
        </div>
        <div className="mt-4 rounded-2xl border border-emerald-100 bg-emerald-50/70 px-4 py-3">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700">Unit</p>
          <p className="mt-1 truncate text-sm font-semibold text-slate-900">PLTU Tenayan Operations</p>
        </div>
      </div>

      <div className="mt-5">
        <div className="mb-3 flex items-center justify-between px-1">
          <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-slate-500">Modules</p>
        </div>

        <nav className="space-y-6">
          {Object.entries(navSections).map(([section, items]) => (
            <div key={section}>
              <p className="mb-2 px-2 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">{section}</p>
              <div className="space-y-2.5">
                {items.map((item) => {
                  const Icon = item.icon;
                  const active = isActive(item.path);

                  return (
                    <Link key={item.path} to={item.path} onClick={() => setMobileNavOpen(false)}>
                      <div
                        className={`group rounded-[18px] border px-3 py-2.5 transition-all ${
                          active
                            ? 'border-emerald-200 bg-white/95 shadow-[0_14px_34px_rgba(25,75,65,0.10)]'
                            : 'border-transparent bg-white/45 hover:border-white/80 hover:bg-white/80'
                        }`}
                        data-testid={`nav-${item.name.toLowerCase()}`}
                      >
                        <div className="flex items-center gap-3">
                          <div
                            className={`flex h-9 w-9 items-center justify-center rounded-xl ${
                              active ? 'bg-emerald-700 text-white' : 'bg-slate-100 text-slate-600'
                            }`}
                          >
                            <Icon className="h-4 w-4" />
                          </div>
                          <p className={`min-w-0 flex-1 truncate text-sm font-semibold ${active ? 'text-slate-950' : 'text-slate-700'}`}>
                            {item.name}
                          </p>
                        </div>
                      </div>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </div>

      <div className="mt-5 rounded-[24px] border border-white/70 bg-white/78 p-4 shadow-[0_14px_34px_rgba(47,69,60,0.08)] backdrop-blur-xl">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-900 text-sm font-bold text-white">
            {(user?.name || 'I').slice(0, 1).toUpperCase()}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold text-slate-900">{user?.name}</p>
            <p className="truncate text-xs text-slate-500">{roleLabel}</p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-10 w-10 rounded-xl text-slate-500 hover:bg-slate-100 hover:text-slate-800"
            onClick={logout}
            data-testid="logout-button"
            title="Logout"
          >
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </>
  );

  return (
    <div className="min-h-screen px-3 py-3 md:px-4 md:py-4">
      <div className="relative mx-auto flex min-h-[calc(100vh-1.5rem)] max-w-[1680px] gap-4">
        <div className="hidden w-[300px] shrink-0 lg:block">
          <aside className="sticky top-4 max-h-[calc(100vh-2rem)] overflow-y-auto pr-1" data-testid="sidebar">
            <NavContent />
          </aside>
        </div>

        {mobileNavOpen && (
          <div className="fixed inset-0 z-40 bg-slate-950/30 backdrop-blur-sm lg:hidden" onClick={() => setMobileNavOpen(false)}>
            <aside
              className="absolute bottom-3 left-3 top-3 w-[min(88vw,340px)] overflow-y-auto rounded-[28px] border border-white/70 bg-[#eef3ee]/95 p-4 shadow-[0_28px_80px_rgba(21,44,37,0.24)]"
              onClick={(event) => event.stopPropagation()}
            >
              <NavContent />
            </aside>
          </div>
        )}

        <main className="min-w-0 flex-1">
          <div className="rounded-[28px] border border-white/65 bg-white/60 shadow-[0_24px_70px_rgba(40,60,52,0.12)] backdrop-blur-xl">
            <header className="border-b border-white/70 px-4 py-4 md:px-7 md:py-5">
              <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div className="flex items-start gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    className="mt-0.5 h-10 w-10 rounded-xl border-white/80 bg-white/80 p-0 lg:hidden"
                    onClick={() => setMobileNavOpen(true)}
                  >
                    <Menu className="h-4 w-4" />
                  </Button>
                  <div>
                    <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-emerald-700">{activeItem.name}</p>
                    <h2 className="mt-1 text-2xl font-extrabold text-slate-950 md:text-3xl">{activeItem.name}</h2>
                    <p className="mt-1 max-w-2xl text-sm text-slate-600">{activeItem.hint}</p>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-3">
                  <div className="rounded-2xl border border-white/80 bg-white/72 px-4 py-3 shadow-sm">
                    <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Environment</p>
                    <p className="mt-1 text-sm font-semibold text-slate-900">PLTU Tenayan Operations</p>
                  </div>
                </div>
              </div>
            </header>

            <div className="px-3 py-3 md:px-5 md:py-5">
              <div className="rounded-[24px] bg-[linear-gradient(180deg,rgba(255,255,255,0.76)_0%,rgba(248,250,249,0.96)_100%)] p-3 md:p-5">
                {children}
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;
