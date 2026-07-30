"use client";

export default function VideoRoom() {
  return (
    <div className="flex-1 flex items-center justify-center bg-surface-1">
      <div className="text-center">
        <div className="grid grid-cols-2 gap-2 max-w-md mx-auto mb-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="aspect-video rounded-xl bg-surface-2 flex items-center justify-center">
              <span className="text-[11px] text-text-muted">Participant {i}</span>
            </div>
          ))}
        </div>
        <p className="text-xs text-text-muted">Video room ready · Join to start</p>
        <button className="mt-3 px-4 py-2 rounded-lg bg-primary text-white text-[11px] font-semibold hover:bg-primary/90 transition-colors">
          Join Call
        </button>
      </div>
    </div>
  );
}
