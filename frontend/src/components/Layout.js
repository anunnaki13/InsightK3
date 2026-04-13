import React, { useContext, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { AppContext } from '../App';
import { Button } from '@/components/ui/button';
import {
  Bell,
  ChevronRight,
  ClipboardCheck,
  FileCheck,
  FileText,
  LayoutDashboard,
  ListChecks,
  LogOut,
  Menu,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';

const Layout = ({ children }) => {
  const { user, logout } = useContext(AppContext);
  const location = useLocation();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  const navigation = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard, hint: 'Ringkasan eksekutif' },
    { name: 'Kriteria', path: '/criteria', icon: ListChecks, hint: 'Master audit SMK3' },
    { name: 'Klausul', path: '/clauses', icon: FileCheck, hint: 'Knowledge base & mapping' },
    { name: 'Audit', path: '/audit', icon: ClipboardCheck, hint: 'Evidence & assessment' },
    { name: 'Rekomendasi', path: '/recommendations', icon: FileText, hint: 'Action tracking' },
    { name: 'Laporan', path: '/reports', icon: FileText, hint: 'Output manajemen' },
    { name: 'ERM Risk', path: '/erm-risk', icon: ShieldAlert, hint: 'Risk register awal', roles: ['admin', 'auditor', 'risk_officer', 'management'] },
  ].filter((item) => !item.roles || item.roles.includes(user?.role));

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

  const NavContent = () => (
    <>
      <div className="rounded-[28px] border border-white/70 bg-white/75 p-5 shadow-[0_20px_60px_rgba(38,64,55,0.12)] backdrop-blur-xl">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[linear-gradient(135deg,#0f5f53_0%,#2b8a78_100%)] shadow-[0_12px_24px_rgba(15,95,83,0.28)]">
              <ShieldCheck className="h-6 w-6 text-white" />
            </div>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-emerald-800/70">InsightK3</p>
              <h1 className="text-xl font-extrabold text-slate-900">Operations Console</h1>
            </div>
          </div>
          <div className="rounded-full border border-emerald-100 bg-emerald-50 px-2 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-emerald-700">
            v2
          </div>
        </div>

        <div className="mt-5 rounded-3xl bg-[linear-gradient(135deg,rgba(16,75,66,0.98)_0%,rgba(34,97,85,0.95)_100%)] p-4 text-white">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.22em] text-emerald-100/80">
            <Sparkles className="h-3.5 w-3.5" />
            Active Workspace
          </div>
          <p className="mt-3 text-lg font-bold leading-tight">Audit and risk intelligence platform for plant operations.</p>
          <p className="mt-2 text-sm text-emerald-50/78">Baseline audit berjalan, fondasi modular v2 sedang dibangun secara bertahap.</p>
        </div>
      </div>

      <div className="mt-6">
        <div className="mb-3 flex items-center justify-between px-1">
          <p className="text-[11px] font-bold uppercase tracking-[0.24em] text-slate-500">Modules</p>
          <span className="rounded-full bg-white/70 px-2 py-1 text-[10px] font-semibold text-slate-500 shadow-sm">
            {navigation.length} active
          </span>
        </div>

        <nav className="space-y-2">
          {navigation.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);

            return (
              <Link key={item.path} to={item.path} onClick={() => setMobileNavOpen(false)}>
                <div
                  className={`group rounded-[22px] border px-4 py-3 transition-all ${
                    active
                      ? 'border-emerald-200 bg-[linear-gradient(135deg,rgba(255,255,255,0.98)_0%,rgba(235,245,241,0.98)_100%)] shadow-[0_18px_40px_rgba(25,75,65,0.12)]'
                      : 'border-transparent bg-white/55 hover:border-white/80 hover:bg-white/82 hover:shadow-[0_14px_32px_rgba(42,66,57,0.08)]'
                  }`}
                  data-testid={`nav-${item.name.toLowerCase()}`}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`flex h-10 w-10 items-center justify-center rounded-2xl ${
                        active ? 'bg-emerald-700 text-white' : 'bg-slate-100 text-slate-600'
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className={`font-semibold ${active ? 'text-slate-950' : 'text-slate-800'}`}>{item.name}</p>
                      <p className="truncate text-xs text-slate-500">{item.hint}</p>
                    </div>
                    <ChevronRight className={`h-4 w-4 transition-transform ${active ? 'text-emerald-700' : 'text-slate-400 group-hover:translate-x-0.5'}`} />
                  </div>
                </div>
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="mt-6 rounded-[28px] border border-white/70 bg-white/75 p-4 shadow-[0_16px_40px_rgba(47,69,60,0.08)] backdrop-blur-xl">
        <div className="flex items-start gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-900 text-sm font-bold text-white">
            {(user?.name || 'I').slice(0, 1).toUpperCase()}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate font-semibold text-slate-900">{user?.name}</p>
            <p className="truncate text-xs text-slate-500">{user?.email}</p>
            <div className="mt-2 inline-flex rounded-full bg-amber-50 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-amber-700">
              {roleLabel}
            </div>
          </div>
        </div>
        <Button
          variant="outline"
          className="mt-4 h-11 w-full justify-start rounded-2xl border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
          onClick={logout}
          data-testid="logout-button"
        >
          <LogOut className="mr-3 h-4 w-4" />
          Logout
        </Button>
      </div>
    </>
  );

  return (
    <div className="min-h-screen px-3 py-3 md:px-5 md:py-5">
      <div className="relative mx-auto flex min-h-[calc(100vh-1.5rem)] max-w-[1680px] gap-4">
        <div className="hidden w-[320px] shrink-0 lg:block">
          <aside className="sticky top-5" data-testid="sidebar">
            <NavContent />
          </aside>
        </div>

        {mobileNavOpen && (
          <div className="fixed inset-0 z-40 bg-slate-950/30 backdrop-blur-sm lg:hidden" onClick={() => setMobileNavOpen(false)}>
            <aside
              className="absolute left-3 top-3 bottom-3 w-[min(88vw,340px)] overflow-y-auto rounded-[30px] border border-white/70 bg-[#eef3ee]/95 p-4 shadow-[0_28px_80px_rgba(21,44,37,0.24)]"
              onClick={(event) => event.stopPropagation()}
            >
              <NavContent />
            </aside>
          </div>
        )}

        <main className="min-w-0 flex-1">
          <div className="rounded-[32px] border border-white/65 bg-white/58 shadow-[0_30px_90px_rgba(40,60,52,0.14)] backdrop-blur-xl">
            <header className="border-b border-white/70 px-4 py-4 md:px-8 md:py-6">
              <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div className="flex items-start gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    className="mt-0.5 h-11 w-11 rounded-2xl border-white/80 bg-white/80 p-0 lg:hidden"
                    onClick={() => setMobileNavOpen(true)}
                  >
                    <Menu className="h-4 w-4" />
                  </Button>
                  <div>
                    <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-emerald-200/80 bg-emerald-50/80 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.2em] text-emerald-700">
                      {activeItem.name}
                    </div>
                    <h2 className="text-3xl font-extrabold text-slate-950 md:text-4xl">{activeItem.name}</h2>
                    <p className="mt-1 max-w-2xl text-sm text-slate-600 md:text-base">{activeItem.hint}</p>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-3">
                  <div className="rounded-[22px] border border-white/80 bg-white/70 px-4 py-3 shadow-sm">
                    <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">Environment</p>
                    <p className="mt-1 text-sm font-semibold text-slate-900">PLTU Tenayan Operations</p>
                  </div>
                  <div className="rounded-[22px] border border-white/80 bg-white/70 px-4 py-3 shadow-sm">
                    <div className="flex items-center gap-2">
                      <Bell className="h-4 w-4 text-amber-600" />
                      <div>
                        <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">Status</p>
                        <p className="mt-1 text-sm font-semibold text-slate-900">Foundation in Progress</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </header>

            <div className="px-3 py-3 md:px-6 md:py-6">
              <div className="rounded-[28px] bg-[linear-gradient(180deg,rgba(255,255,255,0.76)_0%,rgba(248,250,249,0.96)_100%)] p-3 md:p-5">
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
