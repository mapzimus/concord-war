import { GeoJsonLayer, TextLayer } from '@deck.gl/layers';

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

    // Point fill takes precedence over polygon fill so points always render
    // visibly even when a polygon-style isn't set.
    const pointFill = spec.style.point ? hexToRgba(spec.style.point, 1) : null;
    const polyFill = spec.style.fill ? hexToRgba(spec.style.fill, spec.style.fillOpacity ?? 0.5) : null;
    const lineColor = spec.style.line ? hexToRgba(spec.style.line) : [60, 47, 29, 255];

    out.push(
      new GeoJsonLayer({
        id: spec.id,
        data,
        stroked: true,
        filled: true,
        pickable: true,
        lineWidthMinPixels: spec.style.lineWidth ?? 1,
        getLineColor: lineColor,
        getFillColor: pointFill || polyFill || [0, 0, 0, 0],
        getPointRadius: spec.style.pointRadius ?? 6,
        pointRadiusUnits: 'pixels'
      })
    );

    // Text labels for point layers — GeoJsonLayer can't render text, so pair a
    // TextLayer that pulls each point's `name` (SDF font + parchment halo).
    if (spec.style.point && Array.isArray(data.features)) {
      const pts = data.features
        .filter((f) => f.geometry && f.geometry.type === 'Point' && f.properties && f.properties.name)
        .map((f) => ({ position: f.geometry.coordinates, text: f.properties.name }));
      if (pts.length) {
        out.push(
          new TextLayer({
            id: `${spec.id}__labels`,
            data: pts,
            getPosition: (d) => d.position,
            getText: (d) => d.text,
            getSize: 13,
            sizeUnits: 'pixels',
            getColor: hexToRgba(spec.style.point),
            getTextAnchor: 'start',
            getAlignmentBaseline: 'center',
            getPixelOffset: [(spec.style.pointRadius ?? 6) + 4, 0],
            fontFamily: 'Georgia, "Times New Roman", serif',
            fontWeight: 700,
            outlineWidth: 2,
            outlineColor: [231, 220, 192, 255],
            fontSettings: { sdf: true },
            billboard: true,
            pickable: false,
            parameters: { depthTest: false }
          })
        );
      }
    }
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
