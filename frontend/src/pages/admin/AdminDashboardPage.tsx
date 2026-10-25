import React, { useState, useEffect, useMemo } from 'react';
import { useAuth } from '../../context/AuthContext';
import { authService } from '../../services/authService';
import { UserProfile, UserRole, UserStatus } from '../../types/auth';
import {
  Users,
  Clock,
  CheckCircle2,
  XCircle,
  Search,
  Filter,
  ShieldCheck,
  UserCheck,
  UserX,
  Shield,
  Loader2,
} from 'lucide-react';

export const AdminDashboardPage: React.FC = () => {
  const { currentUser, userProfile: currentAdmin } = useAuth();
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<'all' | UserStatus>('all');
  const [roleFilter, setRoleFilter] = useState<'all' | UserRole>('all');
  const [toastMessage, setToastMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Subscribe to real-time users collection via Firestore onSnapshot
  useEffect(() => {
    setLoading(true);
    const unsubscribe = authService.subscribeToUsers((fetchedUsers) => {
      setUsers(fetchedUsers);
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const showToast = (text: string, type: 'success' | 'error' = 'success') => {
    setToastMessage({ text, type });
    setTimeout(() => {
      setToastMessage(null);
    }, 3500);
  };

  // Metrics Bar Calculations
  const metrics = useMemo(() => {
    const total = users.length;
    const pending = users.filter((u) => u.status === 'pending').length;
    const approved = users.filter((u) => u.status === 'approved').length;
    const rejected = users.filter((u) => u.status === 'rejected').length;
    const admins = users.filter((u) => u.role === 'admin').length;
    return { total, pending, approved, rejected, admins };
  }, [users]);

  // Filtered Users List
  const filteredUsers = useMemo(() => {
    return users.filter((u) => {
      const q = searchQuery.toLowerCase().trim();
      const matchesSearch =
        !q ||
        (u.displayName && u.displayName.toLowerCase().includes(q)) ||
        (u.email && u.email.toLowerCase().includes(q)) ||
        (u.uid && u.uid.toLowerCase().includes(q));

      const matchesStatus = statusFilter === 'all' || u.status === statusFilter;
      const matchesRole = roleFilter === 'all' || u.role === roleFilter;

      return matchesSearch && matchesStatus && matchesRole;
    });
  }, [users, searchQuery, statusFilter, roleFilter]);

  // Actions: Approve
  const handleApprove = async (candidate: UserProfile) => {
    if (!currentUser) return;
    setActionInProgress(candidate.uid);
    try {
      await authService.approveUser(candidate.uid, currentUser.uid);
      showToast(`User ${candidate.displayName || candidate.email} approved successfully.`);
    } catch (err: any) {
      showToast(err?.message || 'Failed to approve user.', 'error');
    } finally {
      setActionInProgress(null);
    }
  };

  // Actions: Reject
  const handleReject = async (candidate: UserProfile) => {
    if (!currentUser) return;
    setActionInProgress(candidate.uid);
    try {
      await authService.rejectUser(candidate.uid, currentUser.uid);
      showToast(`User ${candidate.displayName || candidate.email} registration rejected.`, 'error');
    } catch (err: any) {
      showToast(err?.message || 'Failed to reject user.', 'error');
    } finally {
      setActionInProgress(null);
    }
  };

  // Actions: Toggle Role (Promote to Admin / Demote to User)
  const handleToggleRole = async (candidate: UserProfile) => {
    const newRole: UserRole = candidate.role === 'admin' ? 'user' : 'admin';
    setActionInProgress(candidate.uid);
    try {
      await authService.updateUserRole(candidate.uid, newRole);
      showToast(`User role updated to ${newRole.toUpperCase()}.`);
    } catch (err: any) {
      showToast(err?.message || 'Failed to update user role.', 'error');
    } finally {
      setActionInProgress(null);
    }
  };

  const formatDate = (val: any): string => {
    if (!val) return '—';
    try {
      if (val.toDate && typeof val.toDate === 'function') {
        return val.toDate().toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
        });
      }
      const d = new Date(val);
      if (!isNaN(d.getTime())) {
        return d.toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
        });
      }
    } catch {
      // Ignore formatting errors
    }
    return 'Recent';
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-6 bg-[#f8fafc] min-h-[90vh]">
      {/* Toast Notification */}
      {toastMessage && (
        <div
          className={`fixed top-4 right-4 z-50 flex items-center space-x-2 px-4 py-3 rounded-xl border shadow-lg text-xs font-semibold animate-in fade-in slide-in-from-top-2 ${
            toastMessage.type === 'success'
              ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
              : 'bg-rose-50 text-rose-800 border-rose-200'
          }`}
        >
          {toastMessage.type === 'success' ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          ) : (
            <XCircle className="w-4 h-4 text-rose-600" />
          )}
          <span>{toastMessage.text}</span>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div className="space-y-1">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-indigo-50 border border-indigo-200 text-indigo-700">
              <Shield className="w-5 h-5" />
            </div>
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
              Administrative Supervisory Console
            </h1>
          </div>
          <p className="text-xs text-slate-500">
            Real-time user authorization, role delegation, and access gating management
          </p>
        </div>

        {/* Admin identifier */}
        <div className="flex items-center space-x-2 self-start sm:self-auto bg-white px-3 py-1.5 rounded-lg border border-slate-200 shadow-sm text-xs font-mono text-slate-600">
          <span className="w-2 h-2 rounded-full bg-emerald-500" />
          <span className="font-semibold text-slate-800">{currentAdmin?.email || 'admin@facd.edu'}</span>
          <span className="px-1.5 py-0.5 rounded text-[10px] bg-indigo-50 text-indigo-700 font-bold border border-indigo-100 uppercase">
            Admin
          </span>
        </div>
      </div>

      {/* Metrics Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Total Users */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>Total Registered Users</span>
            <div className="p-2 rounded-lg bg-slate-50 text-slate-600 border border-slate-100">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-900 tracking-tight font-mono">
            {metrics.total}
          </div>
          <div className="text-[11px] text-slate-500">
            {metrics.admins} Administrator{metrics.admins === 1 ? '' : 's'} provisioned
          </div>
        </div>

        {/* Pending Approvals */}
        <div className="bg-white rounded-xl border border-amber-200/80 p-5 shadow-sm space-y-2 relative overflow-hidden">
          <div className="flex items-center justify-between text-amber-700 text-xs font-medium">
            <span>Pending Approvals</span>
            <div className="p-2 rounded-lg bg-amber-50 text-amber-600 border border-amber-100">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-amber-900 tracking-tight font-mono">
            {metrics.pending}
          </div>
          <div className="text-[11px] text-amber-700/80">
            {metrics.pending === 0 ? 'No accounts awaiting verification' : 'Requires administrative review'}
          </div>
        </div>

        {/* Active Accounts (Approved) */}
        <div className="bg-white rounded-xl border border-emerald-200/80 p-5 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-emerald-700 text-xs font-medium">
            <span>Active Accounts (Approved)</span>
            <div className="p-2 rounded-lg bg-emerald-50 text-emerald-600 border border-emerald-100">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-emerald-900 tracking-tight font-mono">
            {metrics.approved}
          </div>
          <div className="text-[11px] text-emerald-700/80">
            Verified institutional operators
          </div>
        </div>
      </div>

      {/* Control Bar: Search & Filters */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search candidates by name, email, or UID..."
            className="w-full pl-10 pr-3.5 py-2 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:bg-white focus:border-indigo-600 transition-colors"
          />
        </div>

        {/* Status Filter */}
        <div className="flex items-center space-x-2">
          <Filter className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
            className="px-3 py-2 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700 font-medium focus:outline-none focus:border-indigo-600"
          >
            <option value="all">All Statuses ({metrics.total})</option>
            <option value="pending">Pending Approval ({metrics.pending})</option>
            <option value="approved">Approved ({metrics.approved})</option>
            <option value="rejected">Rejected ({metrics.rejected})</option>
          </select>

          {/* Role Filter */}
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value as any)}
            className="px-3 py-2 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700 font-medium focus:outline-none focus:border-indigo-600"
          >
            <option value="all">All Roles</option>
            <option value="user">User</option>
            <option value="admin">Admin</option>
          </select>
        </div>
      </div>

      {/* User Management Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <h2 className="text-sm font-bold text-slate-900">User Management & Approval Queue</h2>
            <span className="px-2 py-0.5 rounded-full text-[11px] font-mono bg-slate-100 text-slate-600">
              {filteredUsers.length} records
            </span>
          </div>
          {loading && (
            <div className="flex items-center space-x-1.5 text-xs text-slate-500">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-600" />
              <span>Syncing with Firestore...</span>
            </div>
          )}
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider text-[10px]">
                <th className="py-3 px-4">Candidate Name / Email</th>
                <th className="py-3 px-4">Registered Date</th>
                <th className="py-3 px-4">Assigned Role</th>
                <th className="py-3 px-4">Status Badge</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-12 text-center text-slate-400">
                    <div className="flex flex-col items-center justify-center space-y-2">
                      <Users className="w-8 h-8 text-slate-300" />
                      <p className="text-xs font-medium">No candidate accounts match the selected filters</p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredUsers.map((candidate) => {
                  const isOperating = actionInProgress === candidate.uid;
                  const isCurrentAdmin = candidate.uid === currentUser?.uid;

                  return (
                    <tr
                      key={candidate.uid}
                      className="hover:bg-slate-50/70 transition-colors group"
                    >
                      {/* Candidate Name / Email */}
                      <td className="py-3.5 px-4">
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 rounded-full bg-slate-100 text-slate-700 font-bold flex items-center justify-center text-xs shrink-0 border border-slate-200">
                            {(candidate.displayName || candidate.email || 'U')[0].toUpperCase()}
                          </div>
                          <div>
                            <div className="font-semibold text-slate-900 flex items-center space-x-1.5">
                              <span>{candidate.displayName || 'Candidate'}</span>
                              {isCurrentAdmin && (
                                <span className="text-[10px] font-mono text-indigo-700 bg-indigo-50 px-1.5 py-0.2 rounded border border-indigo-100 font-normal">
                                  You
                                </span>
                              )}
                            </div>
                            <div className="text-slate-500 font-mono text-[11px]">
                              {candidate.email}
                            </div>
                          </div>
                        </div>
                      </td>

                      {/* Registered Date */}
                      <td className="py-3.5 px-4 font-mono text-slate-600 whitespace-nowrap">
                        {formatDate(candidate.createdAt)}
                      </td>

                      {/* Assigned Role */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded text-[11px] font-semibold border ${
                            candidate.role === 'admin'
                              ? 'bg-indigo-50 text-indigo-800 border-indigo-200 font-mono'
                              : 'bg-slate-100 text-slate-700 border-slate-200 font-mono'
                          }`}
                        >
                          {candidate.role.toUpperCase()}
                        </span>
                      </td>

                      {/* Status Badge */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        {candidate.status === 'pending' && (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200">
                            <span className="w-1.5 h-1.5 rounded-full bg-amber-500 mr-1.5 animate-pulse" />
                            Pending Approval
                          </span>
                        )}
                        {candidate.status === 'approved' && (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5" />
                            Approved
                          </span>
                        )}
                        {candidate.status === 'rejected' && (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-800 border border-rose-200">
                            <span className="w-1.5 h-1.5 rounded-full bg-rose-500 mr-1.5" />
                            Rejected
                          </span>
                        )}
                      </td>

                      {/* Actions */}
                      <td className="py-3.5 px-4 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end space-x-2">
                          {isOperating ? (
                            <div className="flex items-center space-x-1.5 text-slate-400 py-1 px-3">
                              <Loader2 className="w-3.5 h-3.5 animate-spin text-slate-600" />
                              <span className="text-[11px]">Updating...</span>
                            </div>
                          ) : (
                            <>
                              {/* Approve Button */}
                              {candidate.status !== 'approved' && (
                                <button
                                  type="button"
                                  onClick={() => handleApprove(candidate)}
                                  className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg border border-emerald-600 text-emerald-700 bg-emerald-50 hover:bg-emerald-600 hover:text-white text-xs font-semibold transition-colors cursor-pointer"
                                  title="Approve candidate account"
                                >
                                  <UserCheck className="w-3.5 h-3.5" />
                                  <span>Approve</span>
                                </button>
                              )}

                              {/* Reject Button */}
                              {candidate.status !== 'rejected' && (
                                <button
                                  type="button"
                                  onClick={() => handleReject(candidate)}
                                  className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg border border-rose-300 text-rose-700 hover:bg-rose-50 hover:border-rose-400 text-xs font-semibold transition-colors cursor-pointer"
                                  title="Reject candidate account"
                                >
                                  <UserX className="w-3.5 h-3.5" />
                                  <span>Reject</span>
                                </button>
                              )}

                              {/* Role Toggle: Promote to Admin / Demote to User */}
                              {!isCurrentAdmin && (
                                <button
                                  type="button"
                                  onClick={() => handleToggleRole(candidate)}
                                  className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg border border-slate-200 text-slate-700 bg-slate-50 hover:bg-slate-100 text-xs font-medium transition-colors cursor-pointer"
                                  title={candidate.role === 'admin' ? 'Demote to User' : 'Promote to Admin'}
                                >
                                  <ShieldCheck className="w-3 h-3 text-slate-500" />
                                  <span>
                                    {candidate.role === 'admin' ? 'Demote to User' : 'Promote to Admin'}
                                  </span>
                                </button>
                              )}
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboardPage;
