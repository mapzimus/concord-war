import { GeoJsonLayer, TextLayer, ArcLayer, ScatterplotLayer } from '@deck.gl/layers';

const ARC_COLORS = {
  bombardment: [158, 59, 46],
  air_assault: [26, 82, 118],
  armor: [110, 44, 0]
};

/**
 * Build the deck.gl layer list for a given visible-layer set.
 *
 * @param {Set<string>} visible       Layer ids that should be drawn.
 * @param {Record<string, object>} geo Map from layer id -> loaded GeoJSON FeatureCollection.
 * @param {import('../data/manifest.js').LayerSpec[]} specs Full manifest list (for styling).
 * @param {number} t Animation phase in [0, 1) used to crawl arc tracer dots.
 * @returns {object[]} deck.gl layer instances.
 */
export function buildDeckLayers(visible, geo, specs, t = 0) {
  const out = [];
  for (const spec of specs) {
    if (!visible.has(spec.id)) continue;
    const data = geo[spec.id];
    if (!data) continue;

    // Arc layers (offensive trajectories) render as curved ArcLayer, not flat lines.
    if (spec.style.arc && Array.isArray(data.features)) {
      const arcs = data.features
        .filter((f) => f.geometry && f.geometry.type === 'LineString' && f.geometry.coordinates.length >= 2)
        .map((f) => {
          const c = f.geometry.coordinates;
          return { s: c[0], t: c[c.length - 1], kind: f.properties?.kind, properties: f.properties || {} };
        });
      out.push(
        new ArcLayer({
          id: spec.id,
          data: arcs,
          pickable: true,
          getSourcePosition: (d) => d.s,
          getTargetPosition: (d) => d.t,
          getSourceColor: (d) => ARC_COLORS[d.kind] || [158, 59, 46],
          getTargetColor: (d) => {
            const c = ARC_COLORS[d.kind] || [158, 59, 46];
            return [c[0], c[1], c[2], 110];
          },
          getWidth: (d) => (d.kind === 'armor' ? 6 : d.kind === 'air_assault' ? 4 : 5),
          widthUnits: 'pixels',
          getHeight: 0.45
        })
      );

      // Animated tracer dots crawling each arc's ground track (source -> target),
      // three per arc at staggered phases so the corridor reads as "in motion".
      const tracers = [];
      for (const a of arcs) {
        const col = ARC_COLORS[a.kind] || [158, 59, 46];
        for (let k = 0; k < 3; k++) {
          const u = (t + k / 3) % 1;
          tracers.push({
            position: [a.s[0] + (a.t[0] - a.s[0]) * u, a.s[1] + (a.t[1] - a.s[1]) * u],
            color: col
          });
        }
      }
      out.push(
        new ScatterplotLayer({
          id: `${spec.id}__tracer`,
          data: tracers,
          getPosition: (d) => d.position,
          getFillColor: (d) => d.color,
          getRadius: 4.5,
          radiusUnits: 'pixels',
          stroked: true,
          getLineColor: [231, 220, 192, 255],
          lineWidthMinPixels: 1,
          pickable: false,
          parameters: { depthTest: false },
          updateTriggers: { getPosition: t }
        })
      );
      continue;
    }

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
