/**
 * DatasetCard - Individual card component for the gallery grid
 */
export default function DatasetCard({ dataset, isActive, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`
        dataset-card text-left w-full rounded-xl overflow-hidden bg-white border
        ${isActive 
          ? 'ring-2 ring-blue-500 ring-offset-2 border-blue-200' 
          : 'border-slate-200 hover:border-slate-300'
        }
        shadow-sm hover:shadow-lg
      `}
    >
      {/* Thumbnail */}
      <div className="aspect-video bg-gradient-to-br from-slate-100 to-slate-200 relative overflow-hidden">
        {dataset.thumbnail && !dataset.thumbnail.includes('placeholder') ? (
          <img
            src={dataset.thumbnail}
            alt={dataset.name}
            className="w-full h-full object-cover"
            onError={(e) => {
              e.target.style.display = 'none';
            }}
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className={`
              w-16 h-16 rounded-2xl flex items-center justify-center
              ${getSourceGradient(dataset.source)}
            `}>
              <svg className="w-8 h-8 text-white/80" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
              </svg>
            </div>
          </div>
        )}
        
        {/* Source badge overlay */}
        <div className="absolute top-3 right-3">
          <span className={`
            px-2 py-1 rounded-full text-xs font-medium backdrop-blur-sm
            ${getSourceBadgeClass(dataset.source)}
          `}>
            {dataset.source}
          </span>
        </div>

        {/* Active indicator */}
        {isActive && (
          <div className="absolute top-3 left-3">
            <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-500 text-white flex items-center gap-1">
              <span className="w-2 h-2 bg-white rounded-full animate-pulse" />
              Playing
            </span>
          </div>
        )}
      </div>

      {/* Card content */}
      <div className="p-4">
        <h4 className="font-semibold text-slate-800 mb-1">{dataset.name}</h4>
        <p className="text-sm text-slate-500 line-clamp-2">{dataset.description}</p>
        
        {/* Topic tags */}
        <div className="mt-3 flex flex-wrap gap-1">
          {dataset.topics.transforms?.slice(0, 2).map(topic => (
            <span key={topic} className="px-1.5 py-0.5 bg-slate-100 text-slate-600 rounded text-xs font-mono truncate max-w-[120px]">
              {topic.split('/').pop()}
            </span>
          ))}
          {dataset.topics.tactile && (
            <span className="px-1.5 py-0.5 bg-purple-100 text-purple-600 rounded text-xs">
              tactile
            </span>
          )}
        </div>
      </div>
    </button>
  );
}

function getSourceBadgeClass(source) {
  switch (source) {
    case 'Genrobot':
      return 'bg-emerald-500/90 text-white';
    case 'Lumos':
      return 'bg-amber-500/90 text-white';
    case 'DM Robot':
      return 'bg-violet-500/90 text-white';
    default:
      return 'bg-slate-500/90 text-white';
  }
}

function getSourceGradient(source) {
  switch (source) {
    case 'Genrobot':
      return 'bg-gradient-to-br from-emerald-400 to-emerald-600';
    case 'Lumos':
      return 'bg-gradient-to-br from-amber-400 to-amber-600';
    case 'DM Robot':
      return 'bg-gradient-to-br from-violet-400 to-violet-600';
    default:
      return 'bg-gradient-to-br from-slate-400 to-slate-600';
  }
}
