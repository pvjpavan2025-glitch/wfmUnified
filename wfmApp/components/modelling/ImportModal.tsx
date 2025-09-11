"use client"

import React, { useState, useRef } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface ImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImport: (xml: string, filename?: string) => void;
}

export function ImportModal({ isOpen, onClose, onImport }: ImportModalProps) {
  const [activeTab, setActiveTab] = useState<'url' | 'file'>('url');
  const [urlValue, setUrlValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleUrlImport = async () => {
    if (!urlValue.trim()) return;
    
    setIsLoading(true);
    try {
      // Try direct fetch first
      let response;
      try {
        response = await fetch(urlValue, {
          mode: 'cors',
          headers: {
            'Accept': 'application/xml, text/xml, */*'
          }
        });
      } catch (corsError) {
        // If CORS fails, try using a CORS proxy
        const proxyUrl = `https://api.allorigins.win/get?url=${encodeURIComponent(urlValue)}`;
        response = await fetch(proxyUrl);
        if (response.ok) {
          const data = await response.json();
          const xml = data.contents;
          if (xml && xml.trim().startsWith('<?xml')) {
            onImport(xml, 'imported-diagram');
            onClose();
            return;
          } else {
            throw new Error('Invalid BPMN/XML content received');
          }
        }
        throw corsError;
      }
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const xml = await response.text();
      if (!xml || !xml.trim().startsWith('<?xml')) {
        throw new Error('Invalid BPMN/XML content received');
      }
      
      onImport(xml, 'imported-diagram');
      onClose();
    } catch (error) {
      console.error('Error importing from URL:', error);
      let errorMessage = 'Failed to import from URL. ';
      
      if (error instanceof TypeError && error.message.includes('fetch')) {
        errorMessage += 'This may be due to CORS restrictions. Try using a file upload instead, or ensure the URL supports CORS.';
      } else if (error instanceof Error && error.message.includes('Invalid BPMN/XML')) {
        errorMessage += 'The URL does not contain valid BPMN/XML content.';
      } else if (error instanceof Error && error.message.includes('HTTP')) {
        errorMessage += `Server error: ${error.message}`;
      } else {
        errorMessage += 'Please check the URL and try again.';
      }
      
      alert(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileSelect = () => {
    fileInputRef.current?.click();
  };

  const handleFileImport = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const xml = e.target?.result as string;
        if (xml) {
          onImport(xml, file.name.replace('.bpmn', '').replace('.xml', ''));
          onClose();
        }
      };
      reader.readAsText(file);
    }
    // Reset the input
    event.target.value = '';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Import BPMN Diagram</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>
        
        <div className="p-6">
          {/* Tab Navigation */}
          <div className="flex space-x-1 mb-6">
            <button
              onClick={() => setActiveTab('url')}
              className={`px-4 py-2 rounded-md text-sm font-medium ${
                activeTab === 'url'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              From URL
            </button>
            <button
              onClick={() => setActiveTab('file')}
              className={`px-4 py-2 rounded-md text-sm font-medium ${
                activeTab === 'file'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              From File
            </button>
          </div>

          {/* URL Tab Content */}
          {activeTab === 'url' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  BPMN File URL
                </label>
                <input
                  type="url"
                  value={urlValue}
                  onChange={(e) => setUrlValue(e.target.value)}
                  placeholder="https://example.com/diagram.bpmn"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <p className="mt-2 text-sm text-gray-600">
                  Enter the URL of a BPMN file (.bpmn or .xml). Works with localhost, cloud URLs, and CORS-enabled servers.
                </p>
                <div className="mt-2 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                  <div className="text-sm">
                    <span className="text-yellow-600">⚠️</span>
                    <span className="text-yellow-800 ml-1 font-medium">CORS Notice:</span>
                    <span className="text-yellow-700 ml-1">
                      Some URLs may be blocked by browser security. If import fails, try downloading the file and using "From File" instead.
                    </span>
                  </div>
                </div>
                <div className="mt-2 text-sm">
                  <span className="text-blue-600">💡 Sample:</span>
                  <span className="text-blue-600 ml-1">
                    https://cdn.staticaly.com/gh/bpmn-io/bpmn-js-examples/master/starter/diagram.bpmn
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* File Tab Content */}
          {activeTab === 'file' && (
            <div className="space-y-4">
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                <div className="text-gray-500 mb-4">
                  <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                </div>
                <p className="text-gray-600 mb-4">Select a BPMN file to import</p>
                <button
                  onClick={handleFileSelect}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded"
                >
                  Choose File
                </button>
              </div>
            </div>
          )}

          {/* BPMN Requirements */}
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <h4 className="text-sm font-medium text-gray-900 mb-2">Valid BPMN files must contain:</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• XML format with proper structure</li>
              <li>• BPMN definitions element</li>
              <li>• At least one process element</li>
              <li>• Valid BPMN 2.0 schema compliance</li>
            </ul>
          </div>
        </div>
        
        <div className="flex justify-end space-x-3 p-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-4 rounded"
          >
            Cancel
          </button>
          {activeTab === 'url' && (
            <button
              onClick={handleUrlImport}
              disabled={!urlValue.trim() || isLoading}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded"
            >
              {isLoading ? 'Importing...' : 'Import from URL'}
            </button>
          )}
        </div>
      </div>
      
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".bpmn,.xml"
        onChange={handleFileImport}
        style={{ display: 'none' }}
      />
    </div>
  );
}
