"use client";

import {
  forwardRef,
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { ChevronLeft, ChevronRight } from "@/lib/icons";
import { cn } from "@/lib/utils";

interface CarouselProps {
  children: ReactNode;
  className?: string;
  itemClassName?: string;
  ariaLabel?: string;
  /** Scroll distance per arrow click, in px. Defaults to ~80% of viewport. */
  scrollAmount?: number;
}

/**
 * Consistent, responsive, accessible horizontal scroller used across the app
 * (product rows, video rows, category strips, etc.).
 *
 * - Snap scrolling with momentum (mobile-friendly)
 * - Prev/Next buttons that auto-hide when no more content in that direction
 * - Pointer drag (grab) support
 * - Keyboard arrow navigation when focused
 * - RTL aware (buttons + scroll direction flip)
 */
export const Carousel = forwardRef<HTMLDivElement, CarouselProps>(
  ({ children, className, itemClassName, ariaLabel = "Carousel", scrollAmount }, ref) => {
    const innerRef = useRef<HTMLDivElement>(null);
    const drag = useRef<{ active: boolean; startX: number; startScroll: number; moved: boolean }>({
      active: false,
      startX: 0,
      startScroll: 0,
      moved: false,
    });
    const [canPrev, setCanPrev] = useState(false);
    const [canNext, setCanNext] = useState(false);
    const [isRtl, setIsRtl] = useState(false);

    const measure = useCallback(() => {
      const el = innerRef.current;
      if (!el) return;
      const { scrollLeft, scrollWidth, clientWidth } = el;
      const maxScroll = scrollWidth - clientWidth;
      setCanPrev(scrollLeft > 2);
      setCanNext(scrollLeft < maxScroll - 2);
    }, []);

    useEffect(() => {
      const el = innerRef.current;
      if (!el) return;
      measure();
      const onScroll = () => measure();
      el.addEventListener("scroll", onScroll, { passive: true });
      const ro = new ResizeObserver(() => measure());
      ro.observe(el);
      return () => {
        el.removeEventListener("scroll", onScroll);
        ro.disconnect();
      };
    }, [measure]);

    useEffect(() => {
      const el = innerRef.current;
      if (!el) return;
      const updateRtl = () => setIsRtl(getComputedStyle(el).direction === "rtl");
      updateRtl();
      const ro = new ResizeObserver(updateRtl);
      ro.observe(el);
      return () => ro.disconnect();
    }, []);

    const scrollBy = useCallback(
      (dir: 1 | -1) => {
        const el = innerRef.current;
        if (!el) return;
        const amount = scrollAmount ?? Math.max(240, el.clientWidth * 0.8);
        el.scrollBy({ left: dir * amount * (isRtl ? -1 : 1), behavior: "smooth" });
      },
      [scrollAmount, isRtl]
    );

    const onPointerDown = (e: React.PointerEvent) => {
      const el = innerRef.current;
      if (!el) return;
      drag.current = { active: true, startX: e.clientX, startScroll: el.scrollLeft, moved: false };
    };
    const onPointerMove = (e: React.PointerEvent) => {
      const el = innerRef.current;
      if (!el || !drag.current.active) return;
      const delta = e.clientX - drag.current.startX;
      if (Math.abs(delta) > 4) drag.current.moved = true;
      el.scrollLeft = drag.current.startScroll - delta;
    };
    const endDrag = () => {
      drag.current.active = false;
    };

    // Prevent click navigation right after a drag.
    const onClickCapture = (e: React.MouseEvent) => {
      if (drag.current.moved) {
        e.preventDefault();
        e.stopPropagation();
        drag.current.moved = false;
      }
    };

    const onKeyDown = (e: React.KeyboardEvent) => {
      if (e.key === "ArrowRight") {
        e.preventDefault();
        scrollBy(isRtl ? -1 : 1);
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        scrollBy(isRtl ? 1 : -1);
      }
    };

    const setRefs = (node: HTMLDivElement | null) => {
      innerRef.current = node;
      if (typeof ref === "function") ref(node);
      else if (ref) (ref as React.MutableRefObject<HTMLDivElement | null>).current = node;
    };

    return (
      <div className={cn("relative", className)}>
        {canPrev && (
          <button
            type="button"
            onClick={() => scrollBy(-1)}
            aria-label="Previous"
            className="absolute left-0 top-1/2 z-10 -translate-y-1/2 rounded-full border border-glass-border bg-glass-panel p-2 text-text shadow-lg backdrop-blur transition-colors hover:bg-glass-panel-hover hover:text-primary"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
        )}
        {canNext && (
          <button
            type="button"
            onClick={() => scrollBy(1)}
            aria-label="Next"
            className="absolute right-0 top-1/2 z-10 -translate-y-1/2 rounded-full border border-glass-border bg-glass-panel p-2 text-text shadow-lg backdrop-blur transition-colors hover:bg-glass-panel-hover hover:text-primary"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        )}
        <div
          ref={setRefs}
          role="group"
          aria-label={ariaLabel}
          tabIndex={0}
          onKeyDown={onKeyDown}
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={endDrag}
          onPointerLeave={endDrag}
          onClickCapture={onClickCapture}
          className="flex snap-x snap-mandatory gap-3 overflow-x-auto scroll-smooth pb-2 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
          style={{ cursor: "grab", touchAction: "pan-y" }}
        >
          {itemClassName
            ? Array.isArray(children)
              ? (children as ReactNode[]).map((child, i) => (
                  <div key={i} className={cn("snap-start shrink-0", itemClassName)}>
                    {child}
                  </div>
                ))
              : children
            : children}
        </div>
      </div>
    );
  }
);

Carousel.displayName = "Carousel";
