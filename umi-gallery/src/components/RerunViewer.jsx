import WebViewer from '@rerun-io/web-viewer-react';

/**
 * RerunViewer - Embeds Rerun web viewer to visualize RRD data
 * 
 * NOTE: The Rerun WebViewer component has issues when switching between datasets.
 * For now, the viewer loads the first dataset. Page reload is required to change datasets.
 */
export default function RerunViewer({ rrdUrl }) {
  // Construct full URL for RRD file
  const fullUrl = rrdUrl?.startsWith('http') 
    ? rrdUrl 
    : rrdUrl ? new URL(rrdUrl, window.location.href).href : null;

  // Show placeholder if no valid URL
  if (!fullUrl) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-slate-800 text-slate-400">
        <div className="text-center">
          <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <p>No dataset selected</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full relative">
      <WebViewer 
        width="100%" 
        height="100%" 
        rrd={fullUrl}
      />
      {/* Overlay with file info */}
      <div className="absolute bottom-4 left-4 px-3 py-2 bg-slate-900/80 backdrop-blur-sm rounded-lg text-xs text-slate-300 font-mono max-w-md truncate pointer-events-none">
        {rrdUrl}
      </div>
    </div>
  );
}
