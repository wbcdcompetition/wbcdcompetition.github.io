import { useMemo } from 'react';

/**
 * FoxgloveViewer - Embeds Foxglove Studio to visualize MCAP data
 * 
 * Uses the official embed endpoint at embed.foxglove.dev
 */
export default function FoxgloveViewer({ mcapUrl, layoutType }) {
  // Build the Foxglove embed URL with the full MCAP URL
  const foxgloveUrl = useMemo(() => {
    if (!mcapUrl) return null;
    
    // Official Foxglove EMBED endpoint (allows iframe embedding)
    const baseUrl = 'https://embed.foxglove.dev';
    
    // Construct the full URL for the MCAP file
    let fullMcapUrl;
    if (mcapUrl.startsWith('http')) {
      // Already a full URL
      fullMcapUrl = mcapUrl;
    } else {
      // Local path - construct full URL from current location
      fullMcapUrl = new URL(mcapUrl, window.location.href).href;
    }
    
    // Build Foxglove URL with data source parameters
    const params = new URLSearchParams();
    params.set('ds', 'remote-file');
    params.set('ds.url', fullMcapUrl);
    
    return `${baseUrl}?${params.toString()}`;
  }, [mcapUrl]);

  // Show placeholder if no valid URL
  if (!mcapUrl) {
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
      <iframe
        src={foxgloveUrl}
        title="Foxglove Viewer"
        className="w-full h-full border-0"
        allow="fullscreen"
      />
      {/* Overlay with file info */}
      <div className="absolute bottom-4 left-4 px-3 py-2 bg-slate-900/80 backdrop-blur-sm rounded-lg text-xs text-slate-300 font-mono max-w-md truncate">
        {mcapUrl}
      </div>
    </div>
  );
}
