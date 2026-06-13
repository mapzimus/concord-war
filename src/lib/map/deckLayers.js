import { GeoJsonLayer } from '@deck.gl/layers';

/**
 * Build the deck.gl layer list for a given visible-layer set.
 *
 * @param {Set<string>} visible       Layer ids that should be drawn.
 * @param {Record<string, object>} geo Map from layer id -> loaded GeoJSON FeatureCollection.
 * @param {import('../data/manifest.js').LayerSpec[]} specs Full manifest list (for styling).
 * @returns {object[]} deck.gl layer instances.
 */
export function buildDeckLayers(visible, geo, specs) {
  const out = [];
  for (const spec of specs) {
    if (!visible.has(spec.id)) continue;
    const data = geo[spec.id];
    if (!data) continue;
    out.push(
      new GeoJsonLayer({
        id: spec.id,
        data,
        stroked: true,
        filled: true,
        pickable: true,
        lineWidthMinPixels: spec.style.lineWidth ?? 1,
        getLineColor: spec.style.line ? hexToRgba(spec.style.line) : [60, 47, 29, 255],
        getFillColor: spec.style.fill ? hexToRgba(spec.style.fill, spec.style.fillOpacity ?? 0.5) : [0, 0, 0, 0],
        getPointRadius: spec.style.pointRadius ?? 6,
        pointRadiusUnits: 'pixels'
      })
    );
  }
  return out;
}

/** @param {string} hex e.g. "#bcc6a8" */
function hexToRgba(hex, alpha = 1) {
  const h = hex.replace('#', '');
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  return [r, g, b, Math.round(alpha * 255)];
}
