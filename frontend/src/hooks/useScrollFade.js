import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * Tracks whether a horizontally scrollable element has more content to the
 * left/right, so the UI can show a fade edge hinting that it scrolls sideways.
 *
 *   const { ref, fadeLeft, fadeRight } = useScrollFade();
 *   <div ref={ref} style={{ overflowX: 'auto' }}>…</div>
 */
export function useScrollFade(threshold = 4) {
  const ref = useRef(null);
  const [fade, setFade] = useState({ fadeLeft: false, fadeRight: false });

  const update = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    const max = el.scrollWidth - el.clientWidth;
    const next = {
      fadeLeft: max > threshold && el.scrollLeft > threshold,
      fadeRight: max > threshold && el.scrollLeft < max - threshold,
    };
    setFade((prev) => (prev.fadeLeft === next.fadeLeft && prev.fadeRight === next.fadeRight ? prev : next));
  }, [threshold]);

  useEffect(() => {
    const el = ref.current;
    if (!el) return undefined;
    update();
    el.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
    let ro;
    if (typeof ResizeObserver !== 'undefined') {
      ro = new ResizeObserver(update);
      ro.observe(el);
    }
    return () => {
      el.removeEventListener('scroll', update);
      window.removeEventListener('resize', update);
      if (ro) ro.disconnect();
    };
  }, [update]);

  return { ref, update, ...fade };
}

export default useScrollFade;
