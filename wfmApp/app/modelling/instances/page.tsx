"use client"

import React, { useState, useEffect, useRef } from 'react';
import { AppShell } from '@/components/app-shell';
import { processApiService, ProcessInstance } from '@/services/processApi';
import { useToast } from '@/hooks/use-toast';

export default function InstancesPage() {
  const { toast } = useToast();
  const [instances, setInstances] = useState<ProcessInstance[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Prevent duplicate fetches under React StrictMode by tracking last loaded
  const lastLoadedRef = useRef<boolean>(false);

  // Load data when component mounts
  useEffect(() => {
    if (lastLoadedRef.current) return;
    lastLoadedRef.current = true;
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Single call to list all instances; backend supports filtering via query if needed
      const resp = await processApiService.listAllProcessInstances();
      setInstances(resp.data ?? []);
    } catch (err) {
      setInstances([]);
      console.log('No instances found or error occurred:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell title="Process Instances" subtitle="View and monitor running process instances">
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-6">Process Instances</h3>
        
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-500">Loading instances...</p>
          </div>
        ) : error ? (
          <div className="text-center py-8 space-y-2">
            <p className="text-red-500">{error}</p>
            {(process.env.NEXT_PUBLIC_BPMN_OFFLINE_MODE === 'true' || /offline|connrefused|failed to fetch/i.test(error)) && (
              <p className="text-xs text-gray-500">Backend unreachable (offline mode). Showing empty list.</p>
            )}
          </div>
        ) : instances.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500">No process instances found.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Instance ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Process Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Started At</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {instances.map((instance, idx) => (
                  <tr key={instance.id || `${instance.process_id}-${instance.started_at}-${idx}` }>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{instance.id}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{instance.process_name}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        instance.status === 'completed' ? 'bg-green-100 text-green-800' :
                        instance.status === 'running' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {instance.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(instance.started_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </AppShell>
  );
}
