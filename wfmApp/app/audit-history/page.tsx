
"use client";
import React, { useEffect, useState } from 'react';

interface AuditRecord {
  timestamp: number;
  filename: string;
  action: string;
  diff?: any;
  sessionId?: string;
  hash?: string;
}

export default function AuditHistoryPage() {
  const [records, setRecords] = useState<AuditRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const [limit, setLimit] = useState(50);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/audit/conflicts?offset=${offset}&limit=${limit}`)
      .then(r => r.json())
      .then(data => {
        setRecords(data.data || []);
        setLoading(false);
      })
      .catch(e => { setError('Failed to load audit history'); setLoading(false); });
  }, [offset, limit]);

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h2 className="text-xl font-bold mb-4">Conflict Audit History</h2>
      {error && <div className="text-red-600 mb-2">{error}</div>}
      <div className="mb-3 flex items-center space-x-2">
        <button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset-limit))} className="px-2 py-1 rounded bg-gray-200">Prev</button>
        <span>Showing {offset+1} - {offset+records.length}</span>
        <button disabled={records.length < limit} onClick={() => setOffset(offset+limit)} className="px-2 py-1 rounded bg-gray-200">Next</button>
        <select value={limit} onChange={e => { setLimit(Number(e.target.value)); setOffset(0); }} className="ml-2 px-2 py-1 rounded">
          {[25,50,100].map(n => <option key={n} value={n}>{n}</option>)}
        </select>
      </div>
      <table className="w-full text-xs border">
        <thead>
          <tr className="bg-gray-100">
            <th className="border px-2 py-1">Time</th>
            <th className="border px-2 py-1">Filename</th>
            <th className="border px-2 py-1">Action</th>
            <th className="border px-2 py-1">Session</th>
            <th className="border px-2 py-1">Diff Summary</th>
            <th className="border px-2 py-1">Hash</th>
          </tr>
        </thead>
        <tbody>
          {records.map(r => (
            <tr key={r.hash || r.timestamp}>
              <td className="border px-2 py-1">{new Date(r.timestamp).toLocaleString()}</td>
              <td className="border px-2 py-1">{r.filename}</td>
              <td className="border px-2 py-1">{r.action}</td>
              <td className="border px-2 py-1">{r.sessionId}</td>
              <td className="border px-2 py-1">{r.diff ? Object.entries(r.diff).map(([k,v]) => `${k}: ${Array.isArray(v)?v.length:v}`).join(', ') : ''}</td>
              <td className="border px-2 py-1 font-mono text-[10px]">{r.hash?.slice(0,12)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="mt-4">
        <a href="/api/audit/conflicts/download" className="px-3 py-2 rounded bg-blue-600 text-white">Download Raw Audit Log</a>
      </div>
    </div>
  );
}
