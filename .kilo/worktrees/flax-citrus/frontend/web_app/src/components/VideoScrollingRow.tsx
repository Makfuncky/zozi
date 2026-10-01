"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { PlayCircle } from "lucide-react";
import { apiFetch, parseJsonResponse } from "@/lib/api";
import { ProductVideo } from "@/lib/types";
import { Carousel } from "@/components/Carousel";

interface VideoScrollingRowProps {
  productId?: number;
  title?: string;
  limit?: number;
  videos?: ProductVideo[];
}

export default function VideoScrollingRow({ productId, title = "Product Videos", limit = 10, videos: externalVideos }: VideoScrollingRowProps) {
  const [videos, setVideos] = useState<ProductVideo[]>(externalVideos ?? []);
  const [loading, setLoading] = useState(!externalVideos);
  const [playingId, setPlayingId] = useState<number | null>(null);
  const videoRefs = useRef<Record<number, HTMLVideoElement | null>>({});

  useEffect(() => {
    if (externalVideos) {
      setVideos(externalVideos);
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);

    void apiFetch(`/product-videos/product/${productId}?limit=${limit}`)
      .then((r) => (r.ok ? parseJsonResponse(r) : null))
      .then((data: { videos?: ProductVideo[] } | null) => {
        if (cancelled) return;
        const productVideos = data?.videos ?? [];
        if (productVideos.length === 0 && productId !== undefined) {
          return apiFetch(`/product-videos/featured?limit=${limit}`)
            .then((r2) => (r2.ok ? parseJsonResponse(r2) : null))
            .then((data2: { videos?: ProductVideo[] } | null) => {
              if (!cancelled) setVideos(data2?.videos ?? []);
            });
        }
        if (!cancelled) setVideos(productVideos);
      })
      .catch(() => {
        if (!cancelled) setVideos([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [productId, limit, externalVideos]);

  const handlePlay = (videoId: number) => {
    const current = videoRefs.current[videoId];
    Object.entries(videoRefs.current).forEach(([id, el]) => {
      const numId = Number(id);
      if (numId !== videoId && el && !el.paused) {
        el.pause();
      }
    });
    if (current) {
      if (current.paused) {
        current.play();
        setPlayingId(videoId);
      } else {
        current.pause();
        setPlayingId(null);
      }
    }
  };

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return "";
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  if (loading) {
    return (
      <div className="mt-6">
        <h2 className="text-lg font-semibold text-text mb-3">{title}</h2>
        <div className="flex gap-3 overflow-hidden">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-40 w-64 shrink-0 animate-pulse rounded-2xl bg-surface-2" />
          ))}
        </div>
      </div>
    );
  }

  if (videos.length === 0) {
    return null;
  }

  return (
      <div className="mt-6">
        <h2 className="text-lg font-semibold text-text mb-3">{title}</h2>
        <Carousel ariaLabel={title} itemClassName="snap-start">
          {videos.map((video) => (
            <motion.div
              key={video.id}
              className="relative h-40 w-64 shrink-0 rounded-2xl overflow-hidden border border-border bg-black group cursor-pointer"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
            >
              <video
                ref={(el) => {
                  videoRefs.current[video.id] = el;
                }}
                src={video.video_url}
                poster={video.thumbnail_url || undefined}
                className="h-full w-full object-cover"
                muted
                playsInline
                preload="metadata"
                onClick={() => handlePlay(video.id)}
              />
              {playingId !== video.id && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/30 transition-colors group-hover:bg-black/40">
                  <PlayCircle className="h-10 w-10 text-white/90" />
                </div>
              )}
              {video.duration_seconds ? (
                <span className="absolute bottom-2 right-2 rounded bg-black/70 px-1.5 py-0.5 text-[10px] font-semibold text-white">
                  {formatDuration(video.duration_seconds)}
                </span>
              ) : null}
            </motion.div>
          ))}
        </Carousel>
      </div>
  );
}
