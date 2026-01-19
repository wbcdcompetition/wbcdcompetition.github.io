import { useState, useRef } from 'react';
import { DATASETS, DATA_SOURCE } from '../data/datasets';
import RerunViewer from './RerunViewer';
import DatasetCard from './DatasetCard';

export default function UmiGallery() {
  // Start with no dataset selected - user must click to activate
  const [selectedDataset, setSelectedDataset] = useState(null);
  const viewerRef = useRef(null);

  const handleCardClick = (dataset) => {
    setSelectedDataset(dataset);
    // Smooth scroll to viewer after selection
    setTimeout(() => {
      viewerRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
  };

  return (
    <div className="bg-slate-50 min-h-screen">
      {/* Header */}
      <header className="bg-slate-900 text-white py-4 sticky top-0 z-50 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <a href="../index.html" className="text-slate-400 hover:text-white transition-colors">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
              </a>
              <div>
                <h1 className="text-xl font-bold">WBCD Data Gallery</h1>
                <p className="text-sm text-slate-400">WBCD 2026 Competition</p>
              </div>
            </div>
            <div className="hidden sm:flex items-center gap-2 text-sm text-slate-400">
              <span className="px-2 py-1 bg-emerald-900/50 text-emerald-400 rounded">Genrobot</span>
              <span className="px-2 py-1 bg-amber-900/50 text-amber-400 rounded">Lumos</span>
              <span className="px-2 py-1 bg-violet-900/50 text-violet-400 rounded">DM Robot</span>
            </div>
          </div>
        </div>
      </header>

      {/* Dataset Selection - Cards first */}
      <section className="py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <h3 className="text-xl font-semibold text-slate-800 mb-2">Select a Dataset</h3>
          <p className="text-slate-600 mb-6">Click a dataset to view it in the Rerun visualizer below.</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {DATASETS.map((dataset) => (
              <DatasetCard
                key={dataset.id}
                dataset={dataset}
                isActive={selectedDataset?.id === dataset.id}
                onClick={() => handleCardClick(dataset)}
              />
            ))}
          </div>
        </div>
      </section>

      {/* The Viewer - Only shows when dataset is selected */}
      <section ref={viewerRef} className="py-8 px-4 sm:px-6 lg:px-8 bg-white border-t border-slate-200">
        <div className="max-w-7xl mx-auto">
          {selectedDataset ? (
            <>
              {/* Current dataset info */}
              <div className="mb-6">
                <div className="flex items-center gap-3 mb-2">
                  <h2 className="text-2xl font-bold text-slate-800">{selectedDataset.name}</h2>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getSourceBadgeClass(selectedDataset.source)}`}>
                    {selectedDataset.source}
                  </span>
                </div>
                <p className="text-slate-600">{selectedDataset.description}</p>
                <p className="text-sm text-amber-600 mt-2">⏳ Data files are large. Please wait a moment for the visualization to load.</p>
              </div>

              {/* Rerun Viewer */}
              <div className="foxglove-container">
                <RerunViewer
                  rrdUrl={selectedDataset.rrdUrl}
                />
              </div>

              {/* Dataset metadata */}
              <div className="mt-4 flex flex-wrap gap-2">
                <span className="text-sm text-slate-500">Topics:</span>
                {selectedDataset.topics.transforms?.map(topic => (
                  <code key={topic} className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs font-mono">
                    {topic}
                  </code>
                ))}
                {selectedDataset.topics.cameras?.map(topic => (
                  <code key={topic} className="px-2 py-1 bg-green-50 text-green-700 rounded text-xs font-mono">
                    {topic}
                  </code>
                ))}
              </div>
            </>
          ) : (
            /* Placeholder when no dataset selected */
            <div className="foxglove-container bg-slate-100 rounded-lg flex items-center justify-center">
              <div className="text-center text-slate-500">
                <svg className="w-20 h-20 mx-auto mb-4 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
                </svg>
                <p className="text-lg font-medium">Select a dataset above</p>
                <p className="text-sm mt-1">The Rerun visualizer will load here</p>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 text-slate-400 py-8 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <p className="text-sm">
            This gallery is demo-use only.Sample data are collected by our sponsors on similar tasks. They will provide datasets for the competition tasks and supply data to participating teams.
          </p>
          <p className="text-xs mt-2 text-slate-500">
            {DATA_SOURCE.note}
          </p>
          <p className="text-xs mt-3">
            <a href="../index.html" className="hover:text-white transition-colors">← Back to WBCD 2026 Competition</a>
          </p>
        </div>
      </footer>
    </div>
  );
}

function getSourceBadgeClass(source) {
  switch (source) {
    case 'Genrobot':
      return 'bg-emerald-100 text-emerald-700';
    case 'Lumos':
      return 'bg-amber-100 text-amber-700';
    case 'DM Robot':
      return 'bg-violet-100 text-violet-700';
    default:
      return 'bg-slate-100 text-slate-700';
  }
}
