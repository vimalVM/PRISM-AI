import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  RotateCw, 
  CheckCircle, 
  AlertTriangle, 
  Download, 
  Hash, 
  Lock 
} from 'lucide-react';
import { getAuditLogs, verifyAuditChain } from '../api/services';
import { AuditEvent } from '../types/system';

export const AuditPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [chainStatus, setChainStatus] = useState<{ valid: boolean; message: string } | null>(null);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const data = await getAuditLogs({ limit: 50 });
      setLogs(data);
    } catch (err) {
      console.error('Failed to fetch audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const handleVerify = async () => {
    try {
      const res = await verifyAuditChain();
      setChainStatus({ valid: res.valid, message: `${res.message} (${res.records_checked} events)` });
    } catch (err: any) {
      setChainStatus({ valid: false, message: `Verification failed: ${err.message}` });
    }
  };

  return (
    <div className="flex flex-col w-full pb-10 space-y-6">
      {/* Top Banner */}
      <div className="flex items-center justify-between pb-2 border-b border-outline-variant/30">
        <div>
          <h1 className="font-headline text-xl font-bold text-on-surface">
            Tamper-Evident Audit Trail
          </h1>
          <p className="text-xs text-on-surface-variant font-mono">
            Cryptographic SHA-256 Hash Chain · SEC-14 Complete Event Traceability
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleVerify}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-surface-container hover:bg-surface-container-high text-primary font-mono text-xs border border-primary/30 font-semibold"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-primary" />
            <span>Verify Hash Chain</span>
          </button>
          <button
            onClick={fetchLogs}
            className="p-1.5 rounded bg-surface-container hover:bg-surface-container-high text-on-surface border border-outline-variant/30"
          >
            <RotateCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {chainStatus && (
        <div
          className={`p-3 rounded-lg border font-mono text-xs flex items-center gap-2 ${
            chainStatus.valid
              ? 'bg-emerald-500/10 border-emerald-500/30 text-tertiary-fixed'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
          }`}
        >
          {chainStatus.valid ? <CheckCircle className="w-4 h-4 text-tertiary" /> : <AlertTriangle className="w-4 h-4 text-rose-400" />}
          <span>{chainStatus.message}</span>
        </div>
      )}

      {/* Audit Log Table */}
      <div className="bg-surface-container-low rounded-xl overflow-hidden shadow-lg border border-outline-variant/30">
        <table className="w-full text-left font-mono text-xs">
          <thead className="bg-surface-container-lowest text-outline text-[10px] uppercase border-b border-outline-variant/20">
            <tr>
              <th className="py-2.5 px-4">Event Timestamp</th>
              <th className="py-2.5 px-4">Event Type</th>
              <th className="py-2.5 px-4">Operator / Role</th>
              <th className="py-2.5 px-4">Tool / Model</th>
              <th className="py-2.5 px-4">Status</th>
              <th className="py-2.5 px-4">SHA-256 Hash</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-container">
            {logs.length > 0 ? (
              logs.map((log) => (
                <tr key={log.id} className="hover:bg-surface-container-high/40 transition-colors">
                  <td className="py-3 px-4 text-on-surface-variant">
                    {new Date(log.ts).toLocaleTimeString()}
                  </td>
                  <td className="py-3 px-4 font-semibold text-on-surface">{log.event_type}</td>
                  <td className="py-3 px-4 text-on-surface-variant">
                    {log.user_id ? `${log.user_id.substring(0, 8)} (${log.role})` : 'SYSTEM'}
                  </td>
                  <td className="py-3 px-4 text-primary">
                    {log.model || log.tool || 'N/A'}
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        log.status === 'ok' || log.status === 'success'
                          ? 'bg-emerald-500/10 text-tertiary-fixed'
                          : 'bg-rose-500/10 text-rose-300'
                      }`}
                    >
                      {log.status.toUpperCase()}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-outline font-mono text-[10px]">
                    {log.hash?.substring(0, 16)}...
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6} className="py-6 text-center text-outline">
                  No audit events recorded yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
