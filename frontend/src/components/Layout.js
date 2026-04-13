import React, { useContext } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { AppContext } from '../App';
import { Button } from '@/components/ui/button';
import { LayoutDashboard, ListChecks, FileCheck, ClipboardCheck, FileText, LogOut, ShieldCheck } from 'lucide-react';

const Layout = ({ children }) => {
  const { user, logout } = useContext(AppContext);
  const location = useLocation();

  const navigation = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Kriteria', path: '/criteria', icon: ListChecks },
    { name: 'Klausul', path: '/clauses', icon: FileCheck },
    { name: 'Audit', path: '/audit', icon: ClipboardCheck },
    { name: 'Rekomendasi', path: '/recommendations', icon: FileText },
    { name: 'Laporan', path: '/reports', icon: FileText }
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <div className="min-h-screen flex" style={{ background: 'linear-gradient(135deg, #f5f7fa 0%, #e8eef3 100%)' }}>
      {/* Sidebar */}
      <aside className="w-64 bg-white shadow-lg" data-testid="sidebar">
        <div className="p-6 border-b">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-600 rounded-lg">
              <ShieldCheck className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-lg" style={{ fontFamily: 'Manrope, sans-serif' }}>SMK3 Audit</h1>
              <p className="text-xs text-slate-500">Sistem Audit K3</p>
            </div>
          </div>
        </div>

        <nav className="p-4 space-y-2">
          {navigation.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);
            return (
              <Link key={item.path} to={item.path}>
                <Button
                  variant={active ? 'default' : 'ghost'}
                  className={`w-full justify-start ${
                    active ? 'bg-emerald-600 hover:bg-emerald-700 text-white' : 'hover:bg-slate-100'
                  }`}
                  data-testid={`nav-${item.name.toLowerCase()}`}
                >
                  <Icon className="w-4 h-4 mr-3" />
                  {item.name}
                </Button>
              </Link>
            );
          })}
        </nav>

        <div className="absolute bottom-0 w-64 p-4 border-t bg-white">
          <div className="mb-3 p-3 bg-slate-50 rounded-lg">
            <p className="text-sm font-medium">{user?.name}</p>
            <p className="text-xs text-slate-500">{user?.email}</p>
            <p className="text-xs mt-1 px-2 py-1 bg-emerald-100 text-emerald-700 rounded inline-block">
              {user?.role === 'admin' ? 'Admin' : user?.role === 'auditor' ? 'Auditor' : 'Auditee'}
            </p>
          </div>
          <Button
            variant="outline"
            className="w-full justify-start text-red-600 hover:bg-red-50 hover:text-red-700"
            onClick={logout}
            data-testid="logout-button"
          >
            <LogOut className="w-4 h-4 mr-3" />
            Logout
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="p-8">
          {children}
        </div>
      </main>
    </div>
  );
};

export default Layout;