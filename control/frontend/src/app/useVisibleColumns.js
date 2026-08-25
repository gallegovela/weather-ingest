import { useEffect, useRef, useState } from "react";

// Responsive columns with expandable row, cross-cutting since more than
// one module's listing uses it (first set by spec/control/module/stations.md,
// reused by spec/control/module/climatological_values.md): depending on
// available width, optional columns are hidden starting with the lowest
// priority (from the end of the caller's optionalFields); the ones that
// don't fit are available by expanding the row with the "+" control.
const WIDTH_PER_OPTIONAL_COLUMN = 160;
const RESERVED_WIDTH = 480; // always-visible columns + actions

export function useVisibleColumns(optionalFields) {
  const containerRef = useRef(null);
  const [width, setWidth] = useState(Number.POSITIVE_INFINITY);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return undefined;

    const observer = new ResizeObserver((entries) => {
      setWidth(entries[0].contentRect.width);
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const maxOptional = Math.max(
    0,
    Math.floor((width - RESERVED_WIDTH) / WIDTH_PER_OPTIONAL_COLUMN),
  );

  return {
    containerRef,
    visible: optionalFields.slice(0, maxOptional),
    hidden: optionalFields.slice(maxOptional),
  };
}
