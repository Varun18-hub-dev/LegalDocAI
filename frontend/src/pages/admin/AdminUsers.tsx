import React, { useEffect, useState } from 'react';
import { apiService } from '../../services/api';
import { Users, Shield, RefreshCw, UserCheck, UserX, Search } from 'lucide-react';

export const AdminUsers: React.FC = () => {
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const data = await apiService.getAdminUsers();
      setUsers(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleStatus = async (userId: string, currentStatus: string) => {
    const nextStatus = currentStatus === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE';
    try {
      await apiService.updateUserStatus(userId, nextStatus);
      fetchUsers();
    } catch (err) {
      alert('Failed to update user status.');
    }
  };

  const handleChangeRole = async (userId: string, currentRole: string) => {
    const nextRole = currentRole === 'CLIENT' ? 'LAWYER' : currentRole === 'LAWYER' ? 'ADMIN' : 'CLIENT';
    try {
      await apiService.updateUserRole(userId, nextRole);
      fetchUsers();
    } catch (err) {
      alert('Failed to update user role.');
    }
  };

  const filteredUsers = users.filter((u) => 
    u.name.toLowerCase().includes(search.toLowerCase()) || 
    u.email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-8 max-w-5xl mx-auto flex flex-col gap-8 select-none">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white font-heading">Accounts Directory</h2>
        <p className="text-xs text-gray-400 mt-1">Audit, activate/deactivate accounts, and update role clearances.</p>
      </div>

      {/* Search Header */}
      <div className="flex items-center bg-brand-secondary border border-brand-border rounded-xl px-4 py-3 gap-3 max-w-md focus-within:border-accent-purple/40 transition-all duration-300">
        <Search className="w-4 h-4 text-gray-500" />
        <input 
          type="text" 
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by name or email address..." 
          className="bg-transparent border-none outline-none text-xs text-white flex-1 font-sans"
        />
      </div>

      {/* Directory Table */}
      <div className="glass-card p-6 border border-brand-border bg-brand-secondary/40">
        {loading ? (
          <div className="py-12 flex justify-center">
            <RefreshCw className="w-6 h-6 animate-spin text-accent-purple" />
          </div>
        ) : filteredUsers.length === 0 ? (
          <div className="py-12 text-center text-gray-500 italic text-xs">
            No registered users found matching the query.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-brand-border pb-3 text-[10px] font-bold text-gray-500 uppercase tracking-wider">
                  <th className="py-3 px-2">Name</th>
                  <th className="py-3 px-2">Email</th>
                  <th className="py-3 px-2">Access Role</th>
                  <th className="py-3 px-2">Status</th>
                  <th className="py-3 px-2 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map((u) => (
                  <tr key={u.id} className="border-b border-brand-border/40 hover:bg-brand-dark/20 text-xs text-gray-300 transition-all">
                    <td className="py-4 px-2 font-semibold text-gray-200">{u.name}</td>
                    <td className="py-4 px-2">{u.email}</td>
                    <td className="py-4 px-2">
                      <span className="font-semibold text-accent-purple">{u.role}</span>
                    </td>
                    <td className="py-4 px-2">
                      <span className={`px-2 py-0.5 border rounded text-[10px] font-bold ${
                        u.status === 'ACTIVE' 
                          ? 'border-emerald-500/20 bg-emerald-500/5 text-emerald-400' 
                          : 'border-rose-500/20 bg-rose-500/5 text-rose-400'
                      }`}>
                        {u.status}
                      </span>
                    </td>
                    <td className="py-4 px-2 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button 
                          onClick={() => handleChangeRole(u.id, u.role)}
                          className="px-2.5 py-1.5 bg-brand-tertiary hover:bg-brand-secondary border border-brand-border text-[10px] font-bold tracking-wider uppercase rounded-lg text-gray-300 hover:text-white transition-all"
                        >
                          Cycle Role
                        </button>
                        <button 
                          onClick={() => handleToggleStatus(u.id, u.status)}
                          className={`p-1.5 rounded-lg border transition-all ${
                            u.status === 'ACTIVE'
                              ? 'border-rose-500/20 bg-rose-500/5 text-rose-400 hover:bg-rose-500/10'
                              : 'border-emerald-500/20 bg-emerald-500/5 text-emerald-400 hover:bg-emerald-500/10'
                          }`}
                          title={u.status === 'ACTIVE' ? 'Deactivate' : 'Activate'}
                        >
                          {u.status === 'ACTIVE' ? <UserX className="w-3.5 h-3.5" /> : <UserCheck className="w-3.5 h-3.5" />}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
