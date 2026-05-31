export default function AuditProgress({ status, onViewResults, onDownload, isCompleted }) {
  const progress = status?.progress || 0;
  const message = status?.progress_message || "Processing...";
  const auditStatus = status?.status || "running";

  const steps = [
    { label: "Crawling pages", threshold: 20 },
    { label: "Fetching robots.txt & sitemap", threshold: 45 },
    { label: "Analyzing SEO", threshold: 65 },
    { label: "Generating suggestions", threshold: 75 },
    { label: "Creating Word documents", threshold: 90 },
    { label: "Done!", threshold: 100 },
  ];

  return (
    <div className="card space-y-5">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
            {auditStatus === "completed" && <span>✅</span>}
            {auditStatus === "running" && (
              <svg className="animate-spin w-5 h-5 text-blue-500" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
              </svg>
            )}
            {auditStatus === "failed" && <span>❌</span>}
            Audit Progress
          </h3>
          <p className="text-sm text-gray-500 mt-1">{status?.url}</p>
        </div>
        <span className={`
          ${auditStatus === "completed" ? "badge-green" : ""}
          ${auditStatus === "running" ? "badge-blue" : ""}
          ${auditStatus === "failed" ? "badge-red" : ""}
          ${auditStatus === "pending" ? "badge-yellow" : ""}
          text-sm
        `}>
          {auditStatus}
        </span>
      </div>

      {/* Progress Bar */}
      <div>
        <div className="flex justify-between text-sm text-gray-600 mb-2">
          <span>{message}</span>
          <span className="font-semibold">{progress}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
          <div
            className={`h-3 rounded-full transition-all duration-500 ${
              auditStatus === "completed"
                ? "bg-green-500"
                : auditStatus === "failed"
                ? "bg-red-500"
                : "progress-bar-animated"
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Step indicators */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {steps.map((step, i) => {
          const done = progress >= step.threshold;
          const active = i > 0 && progress >= steps[i - 1].threshold && progress < step.threshold;
          return (
            <div key={i} className={`flex items-center gap-2 text-sm px-3 py-2 rounded-lg ${
              done ? "bg-green-50 text-green-700" : active ? "bg-blue-50 text-blue-700" : "bg-gray-50 text-gray-400"
            }`}>
              <span className="text-base">
                {done ? "✓" : active ? "⟳" : "○"}
              </span>
              <span className="leading-tight">{step.label}</span>
            </div>
          );
        })}
      </div>

      {/* Action buttons when complete */}
      {isCompleted && (
        <div className="flex flex-wrap gap-3 pt-2 border-t border-gray-100">
          <button onClick={onViewResults} className="btn-primary flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            View Results
          </button>
          <button onClick={onDownload} className="btn-secondary flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Download Word Files (.zip)
          </button>
        </div>
      )}

      {auditStatus === "failed" && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
          <strong>Audit failed:</strong> {message}
          <br />
          <span className="text-xs">Check that the URL is accessible and try again.</span>
        </div>
      )}
    </div>
  );
}
