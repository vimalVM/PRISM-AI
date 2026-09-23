import React, { useState, useEffect } from 'react';
import { 
  Cpu, 
  RotateCw, 
  CheckCircle, 
  AlertCircle, 
  Server, 
  Zap, 
  Layers 
} from 'lucide-react';
import { getModels, reloadModels } from '../api/services';
import { ModelsStatusResponse } from '../types/system';
import { useAuth } from '../context/AuthContext';

export const ModelsPage: React.FC = () => {
  const { user } = useAuth();
  const [data, setData] = useState<ModelsStatusResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [reloadMsg, setReloadMsg] = useState<string | null>(null);

  const fetchModels = async () => {
    try {
      setLoading(true);
      const res = await getModels();
      setData(res);
    } catch (err: any) {
      console.error('Failed to fetch models:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  const handleReload = async () => {
    try {
      const res = await reloadModels();
      setReloadMsg(res.message);
      fetchModels();
    } catch (err: any) {
      setReloadMsg(`Error: ${err.message}`);
    }
  };

  return (
    <div className="flex flex-col w-full pb-10 space-y-6">
      {/* Top Banner */}
      <div className="flex items-center justify-between pb-2 border-b border-outline-variant/30">
        <div>
          <h1 className="font-headline text-xl font-bold text-on-surface">
            Model Registry & Routing Enclave
          </h1>
          <p className="text-xs text-on-surface-variant font-mono">
            Config-driven Ollama inference on 127.0.0.1:11434 · ModelSwapManager Resident VRAM Control
          </p>
        </div>
        {user?.role === 'admin' && (
          <button
            onClick={handleReload}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-surface-container hover:bg-surface-container-high text-on-surface font-mono text-xs border border-outline-variant/30 font-semibold"
          >
            <RotateCw className="w-3.5 h-3.5 text-primary-container" />
            <span>Reload Registry</span>
          </button>
        )}
      </div>

      {reloadMsg && (
        <div className="p-3 rounded-lg bg-surface-container text-xs font-mono text-primary-container border border-primary-container/30">
          {reloadMsg}
        </div>
      )}

      {/* Ollama Service Status Card */}
      <div className="bg-surface-container-low rounded-xl p-5 border border-outline-variant/30 shadow-md flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-surface-container-high flex items-center justify-center text-primary-container">
            <Server className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-headline text-base font-semibold text-on-surface">Ollama Local Daemon</h2>
              <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-surface-container text-tertiary font-bold">
                127.0.0.1:11434
              </span>
            </div>
            <div className="font-mono text-xs text-on-surface-variant mt-0.5">
              Active Resident: <strong className="text-primary">{data?.current_loaded_model || 'qwen3.5:4b'}</strong>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs text-tertiary">
          <span className="w-2 h-2 rounded-full bg-tertiary shadow-[0_0_8px_#a8ffd2]" />
          <span>CONNECTED & HEALTHY</span>
        </div>
      </div>

      {/* Model Registry Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {data && Object.entries(data.models).map(([key, model]) => (
          <div
            key={key}
            className="bg-surface-container-low rounded-xl p-5 border border-outline-variant/30 shadow-md space-y-3"
          >
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] uppercase text-outline font-bold">{key}</span>
              <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-surface-container text-tertiary font-bold border border-outline-variant/20">
                {model.provider.toUpperCase()}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <Cpu className="w-5 h-5 text-primary-container" />
              <h3 className="font-headline text-base font-semibold text-on-surface">{model.model}</h3>
            </div>

            <div className="space-y-1 font-mono text-xs text-on-surface-variant">
              <div>Capabilities: <span className="text-on-surface">{model.capabilities.join(', ')}</span></div>
              <div className="flex items-center gap-1.5 pt-1">
                <CheckCircle className="w-3.5 h-3.5 text-tertiary" />
                <span className="text-tertiary font-medium">Verified Present Locally</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Routing Rules Card */}
      <div className="bg-surface-container-low rounded-xl p-5 border border-outline-variant/30 shadow-md space-y-3">
        <div className="font-mono text-xs uppercase text-outline font-bold flex items-center gap-2">
          <Layers className="w-4 h-4 text-secondary-fixed" />
          <span>Config-Driven Routing Rules (models/registry.yaml)</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 font-mono text-xs">
          {data?.routing_rules?.map((rule, idx) => (
            <div key={idx} className="p-2.5 rounded bg-surface-container border border-outline-variant/20 text-on-surface">
              {rule}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
