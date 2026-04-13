import React, { useState, useContext } from 'react';
import { AppContext } from '../App';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ShieldCheck, Sparkles, Workflow } from 'lucide-react';

const AuthPage = () => {
  const { login, register } = useContext(AppContext);
  const [loginData, setLoginData] = useState({ email: '', password: '' });
  const [registerData, setRegisterData] = useState({ email: '', password: '', name: '', role: 'auditee' });
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    await login(loginData.email, loginData.password);
    setLoading(false);
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    const success = await register(
      registerData.email,
      registerData.password,
      registerData.name,
      registerData.role
    );
    if (success) {
      setRegisterData({ email: '', password: '', name: '', role: 'auditee' });
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen px-4 py-6 md:px-6 md:py-8">
      <div className="mx-auto grid min-h-[calc(100vh-3rem)] max-w-[1540px] gap-5 xl:grid-cols-[1.15fr_0.85fr]">
        <Card className="overflow-hidden rounded-[34px] border-0 bg-[linear-gradient(135deg,#103a35_0%,#1b5b52_58%,#2b786c_100%)] text-white shadow-[0_34px_100px_rgba(16,58,53,0.28)]">
          <CardContent className="flex h-full flex-col justify-between p-8 md:p-10">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1.5 text-[11px] font-bold uppercase tracking-[0.22em] text-emerald-50/80">
                <Sparkles className="h-3.5 w-3.5" />
                InsightK3
              </div>
              <h1 className="mt-6 max-w-3xl text-4xl font-extrabold leading-tight md:text-6xl">
                Platform audit dan risk intelligence untuk operasi pembangkit.
              </h1>
              <p className="mt-5 max-w-2xl text-base leading-7 text-emerald-50/80">
                Bangun keputusan audit yang lebih cepat, konsisten, dan terdokumentasi dengan workspace yang menyatukan evidence, analisis, dan tindak lanjut.
              </p>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-[24px] border border-white/14 bg-white/10 p-5 backdrop-blur-sm">
                <ShieldCheck className="h-6 w-6 text-emerald-50" />
                <p className="mt-4 text-lg font-bold">Audit Readiness</p>
                <p className="mt-2 text-sm text-emerald-50/74">Pantau evidence dan kelayakan klausul secara lebih terstruktur.</p>
              </div>
              <div className="rounded-[24px] border border-white/14 bg-white/10 p-5 backdrop-blur-sm">
                <Workflow className="h-6 w-6 text-emerald-50" />
                <p className="mt-4 text-lg font-bold">Decision Flow</p>
                <p className="mt-2 text-sm text-emerald-50/74">Dari upload dokumen sampai keputusan auditor dalam satu alur yang jelas.</p>
              </div>
              <div className="rounded-[24px] border border-white/14 bg-white/10 p-5 backdrop-blur-sm">
                <Sparkles className="h-6 w-6 text-emerald-50" />
                <p className="mt-4 text-lg font-bold">Premium Workspace</p>
                <p className="mt-2 text-sm text-emerald-50/74">Dirancang untuk penggunaan operasional dan review manajemen.</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="flex items-center">
          <Card className="w-full rounded-[34px] border-white/70 bg-white/82 shadow-[0_30px_90px_rgba(40,60,52,0.14)] backdrop-blur-xl" data-testid="auth-card">
            <CardHeader className="pb-4 text-center">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-[22px] bg-[linear-gradient(135deg,#0f5f53_0%,#2b8a78_100%)] shadow-[0_18px_40px_rgba(15,95,83,0.24)]">
                <ShieldCheck className="h-8 w-8 text-white" />
              </div>
              <CardTitle className="text-3xl font-extrabold">Masuk ke InsightK3</CardTitle>
              <CardDescription className="mx-auto max-w-md text-sm leading-6 text-slate-600">
                Workspace audit keselamatan dan manajemen risiko untuk operasional PLTU Tenayan.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="login" className="w-full">
                <TabsList className="mb-6 grid h-12 w-full grid-cols-2 rounded-[18px] bg-slate-100 p-1">
                  <TabsTrigger value="login" className="rounded-[14px]" data-testid="login-tab">Login</TabsTrigger>
                  <TabsTrigger value="register" className="rounded-[14px]" data-testid="register-tab">Daftar</TabsTrigger>
                </TabsList>

                <TabsContent value="login">
                  <form onSubmit={handleLogin} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="login-email">Email</Label>
                      <Input
                        id="login-email"
                        data-testid="login-email-input"
                        type="email"
                        placeholder="nama@email.com"
                        value={loginData.email}
                        onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
                        required
                        className="h-12 rounded-[16px] border-slate-200 bg-white"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="login-password">Password</Label>
                      <Input
                        id="login-password"
                        data-testid="login-password-input"
                        type="password"
                        placeholder="••••••••"
                        value={loginData.password}
                        onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                        required
                        className="h-12 rounded-[16px] border-slate-200 bg-white"
                      />
                    </div>
                    <Button
                      type="submit"
                      className="h-12 w-full rounded-[18px] bg-slate-950 hover:bg-slate-800"
                      disabled={loading}
                      data-testid="login-submit-button"
                    >
                      {loading ? 'Memproses...' : 'Masuk ke Workspace'}
                    </Button>
                  </form>
                </TabsContent>

                <TabsContent value="register">
                  <form onSubmit={handleRegister} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="register-name">Nama Lengkap</Label>
                      <Input
                        id="register-name"
                        data-testid="register-name-input"
                        type="text"
                        placeholder="Nama lengkap"
                        value={registerData.name}
                        onChange={(e) => setRegisterData({ ...registerData, name: e.target.value })}
                        required
                        className="h-12 rounded-[16px] border-slate-200 bg-white"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="register-email">Email</Label>
                      <Input
                        id="register-email"
                        data-testid="register-email-input"
                        type="email"
                        placeholder="nama@email.com"
                        value={registerData.email}
                        onChange={(e) => setRegisterData({ ...registerData, email: e.target.value })}
                        required
                        className="h-12 rounded-[16px] border-slate-200 bg-white"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="register-password">Password</Label>
                      <Input
                        id="register-password"
                        data-testid="register-password-input"
                        type="password"
                        placeholder="••••••••"
                        value={registerData.password}
                        onChange={(e) => setRegisterData({ ...registerData, password: e.target.value })}
                        required
                        className="h-12 rounded-[16px] border-slate-200 bg-white"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="register-role">Role</Label>
                      <Select
                        value={registerData.role}
                        onValueChange={(value) => setRegisterData({ ...registerData, role: value })}
                      >
                        <SelectTrigger className="h-12 rounded-[16px]" data-testid="register-role-select">
                          <SelectValue placeholder="Pilih role" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="admin" data-testid="role-admin">Admin</SelectItem>
                          <SelectItem value="auditor" data-testid="role-auditor">Auditor</SelectItem>
                          <SelectItem value="auditee" data-testid="role-auditee">Auditee</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <Button
                      type="submit"
                      className="h-12 w-full rounded-[18px] bg-emerald-700 hover:bg-emerald-800"
                      disabled={loading}
                      data-testid="register-submit-button"
                    >
                      {loading ? 'Memproses...' : 'Buat Akun'}
                    </Button>
                  </form>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
