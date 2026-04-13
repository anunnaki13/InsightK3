import React from 'react';
import { ArrowRight, CheckCircle2, Clock3, Layers3 } from 'lucide-react';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const ModuleLaunchPage = ({ title, badge, description, timeline, highlights = [] }) => {
  return (
    <Layout>
      <div className="space-y-6">
        <section className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
          <Card className="overflow-hidden rounded-[30px] border-0 bg-[linear-gradient(135deg,#14213d_0%,#21476a_55%,#2b6c8f_100%)] text-white shadow-[0_32px_90px_rgba(20,33,61,0.22)]">
            <CardContent className="p-7 md:p-8">
              <p className="text-[11px] font-bold uppercase tracking-[0.28em] text-sky-100/75">{badge}</p>
              <h1 className="mt-3 text-4xl font-extrabold leading-tight md:text-5xl">{title}</h1>
              <p className="mt-4 max-w-2xl text-sm leading-6 text-sky-50/80 md:text-base">
                {description}
              </p>
            </CardContent>
          </Card>

          <Card className="rounded-[30px] border-white/70 bg-white/80 shadow-[0_24px_70px_rgba(45,68,58,0.10)] backdrop-blur-xl">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Delivery Status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="rounded-[20px] bg-slate-50 px-4 py-3">
                <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Current State</p>
                <p className="mt-2 text-xl font-extrabold text-slate-950">UI shell ready</p>
              </div>
              <div className="rounded-[20px] bg-amber-50 px-4 py-3">
                <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-amber-700">Planned Start</p>
                <p className="mt-2 text-sm font-semibold leading-6 text-amber-900">{timeline}</p>
              </div>
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-5 lg:grid-cols-[0.95fr_1.05fr]">
          <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-xl">
                <Layers3 className="h-5 w-5 text-sky-700" />
                Planned Outcomes
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {highlights.map((item) => (
                <div key={item} className="flex items-start gap-3 rounded-[20px] bg-slate-50 px-4 py-3">
                  <CheckCircle2 className="mt-0.5 h-5 w-5 text-emerald-600" />
                  <p className="text-sm leading-6 text-slate-700">{item}</p>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="rounded-[28px] border-white/70 bg-white/80 shadow-[0_22px_55px_rgba(43,67,58,0.10)]">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-xl">
                <Clock3 className="h-5 w-5 text-slate-700" />
                Implementation Note
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-[22px] bg-slate-950 p-5 text-white">
                <p className="text-[11px] font-bold uppercase tracking-[0.24em] text-slate-300">Structured rollout</p>
                <p className="mt-3 text-lg font-bold leading-7">
                  Modul ini sengaja disiapkan dulu pada level product shell agar arsitektur UI dan navigasi v2 tetap rapi saat pengembangan backend menyusul.
                </p>
              </div>
              <div className="rounded-[20px] bg-slate-50 px-4 py-4 text-sm leading-6 text-slate-600">
                Setelah modul aktif, halaman ini akan diganti menjadi workspace penuh dengan form, tabel, analytics, dan integrasi lintas modul sesuai blueprint.
              </div>
              <div className="inline-flex items-center gap-2 rounded-full border border-sky-200 bg-sky-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-sky-700">
                Next build stage
                <ArrowRight className="h-3.5 w-3.5" />
              </div>
            </CardContent>
          </Card>
        </section>
      </div>
    </Layout>
  );
};

export default ModuleLaunchPage;
