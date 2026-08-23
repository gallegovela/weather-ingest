import { useEffect, useRef, useState } from "react";

// Columnas responsive con fila expandible (spec/control/module/estaciones.md):
// según el ancho disponible se ocultan las columnas opcionales de menor
// prioridad (empezando por las últimas de CAMPOS_OPCIONALES); las que no
// caben quedan disponibles al expandir la fila con el control "+".
const ANCHO_POR_COLUMNA_OPCIONAL = 160;
const ANCHO_RESERVADO = 480; // indicativo + nombre + provincia + acciones

export function useColumnasVisibles(camposOpcionales) {
  const contenedorRef = useRef(null);
  const [ancho, setAncho] = useState(Number.POSITIVE_INFINITY);

  useEffect(() => {
    const el = contenedorRef.current;
    if (!el) return undefined;

    const observer = new ResizeObserver((entries) => {
      setAncho(entries[0].contentRect.width);
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const maxOpcionales = Math.max(
    0,
    Math.floor((ancho - ANCHO_RESERVADO) / ANCHO_POR_COLUMNA_OPCIONAL),
  );

  return {
    contenedorRef,
    visibles: camposOpcionales.slice(0, maxOpcionales),
    ocultas: camposOpcionales.slice(maxOpcionales),
  };
}
