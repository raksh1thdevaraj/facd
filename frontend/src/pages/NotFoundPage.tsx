import React from 'react';
import { Link } from 'react-router-dom';
import { FileQuestion, ArrowLeft } from 'lucide-react';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="max-w-md mx-auto my-20 glass-card rounded-2xl p-8 border border-slate-800 text-center space-y-4">
      <div className="p-3 bg-slate-800 text-slate-400 rounded-2xl w-fit mx-auto border border-slate-700">
        <FileQuestion className="w-8 h-8" />
      </div>
      <h2 className="text-xl font-bold text-slate-100">404 - Page Not Found</h2>
      <p className="text-xs text-slate-400">
        The requested route does not exist or the verification record has moved.
      </p>
      <div className="pt-2">
        <Link
          to="/"
          className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Safety</span>
        </Link>
      </div>
    </div>
  );
};
