import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import demoData from '../../../demo_users.json';

const gradeColors = {
  A: { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200' },
  B: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' },
  C: { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200' },
  D: { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200' },
  E: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' },
};

const typeBadge = {
  NTC: { bg: 'bg-violet-50', text: 'text-violet-700', border: 'border-violet-200', label: 'NTC' },
  MSME: { bg: 'bg-sky-50', text: 'text-sky-700', border: 'border-sky-200', label: 'MSME' },
  MSME_MIDDLEMAN: { bg: 'bg-sky-50', text: 'text-sky-700', border: 'border-sky-200', label: 'MSME' },
};

function DemoProfiles() {
  const navigate = useNavigate();
  const users = demoData.demo_users;

  const handleSelect = (user) => {
    localStorage.setItem('pdr_demo_user', JSON.stringify({
      user_id: user.user_id,
      name: user.user_profile?.name || user.form_fields?.full_name || user.form_fields?.applicant_name,
      model: user.model.startsWith('MSME') ? 'MSME' : 'NTC',
      form_fields: user.form_fields,
    }));
    navigate('/solutions');
  };

  return (
    <div className="bg-surface text-on-surface min-h-screen font-body antialiased">
      {/* Nav */}
      <nav className="bg-[#f7f9fb]/80 backdrop-blur-xl top-0 sticky z-50 shadow-sm shadow-slate-200/50 font-['Manrope'] antialiased tracking-tight">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <Link to="/" className="text-xl font-bold tracking-tighter text-slate-900">Paise Do Re (PDR)</Link>
          <div className="hidden md:flex items-center gap-x-8">
            <Link to="/" className="text-slate-500 font-medium hover:text-slate-900 transition-all duration-300">Home</Link>
            <Link to="/solutions" className="text-slate-500 font-medium hover:text-slate-900 transition-all duration-300">Solutions</Link>
            <span className="text-slate-900 font-semibold border-b-2 border-slate-900 pb-1">Demo Profiles</span>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/solutions" className="gradient-cta text-white px-6 py-2.5 rounded-lg font-semibold active:scale-95 transition-transform duration-200">Score a Business</Link>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 pt-16 pb-24">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-block px-4 py-1.5 mb-6 rounded-full bg-tertiary-container text-on-tertiary-container text-xs font-bold tracking-widest uppercase font-label">
            Demo Archetypes
          </div>
          <h1 className="text-4xl md:text-5xl font-headline font-extrabold text-slate-900 tracking-tighter mb-4">
            Explore Demo Profiles
          </h1>
          <p className="text-lg text-on-surface-variant max-w-2xl mx-auto leading-relaxed">
            See how PDR scores different borrower archetypes — from salaried professionals to seasonal farmers to fraud cases.
          </p>
        </div>

        {/* Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {users.map((user) => {
            const grade = gradeColors[user.expected_grade] || gradeColors.C;
            const type = typeBadge[user.model] || typeBadge.NTC;
            const displayName = user.user_profile?.name || 'Unknown';

            return (
              <div
                key={user.user_id}
                className="group bg-surface-container-lowest rounded-2xl border border-outline-variant/15 hover:border-tertiary/40 transition-all duration-500 flex flex-col overflow-hidden"
              >
                <div className="p-8 flex flex-col flex-1">
                  {/* Badges row */}
                  <div className="flex items-center gap-2 mb-5">
                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest border ${type.bg} ${type.text} ${type.border}`}>
                      {type.label}
                    </span>
                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest border ${grade.bg} ${grade.text} ${grade.border}`}>
                      Grade {user.expected_grade}
                    </span>
                  </div>

                  {/* Name */}
                  <h3 className="text-xl font-headline font-bold text-slate-900 mb-1">{displayName}</h3>
                  <p className="text-xs font-bold uppercase tracking-widest text-on-surface-variant/60 mb-4">{user.persona}</p>

                  {/* Story */}
                  <p className="text-sm text-on-surface-variant leading-relaxed flex-1">{user.story}</p>

                  {/* Select button */}
                  <button
                    onClick={() => handleSelect(user)}
                    className="mt-6 w-full py-3 rounded-lg text-sm font-bold tracking-wide bg-slate-900 text-white hover:bg-slate-800 active:scale-[0.98] transition-all duration-200 flex items-center justify-center gap-2"
                  >
                    Select Profile
                    <span className="material-symbols-outlined text-base">arrow_forward</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Back link */}
        <div className="text-center mt-12">
          <Link to="/" className="text-sm text-slate-400 hover:text-slate-600 transition-colors">
            &larr; Back to Home
          </Link>
        </div>
      </main>
    </div>
  );
}

export default DemoProfiles;
