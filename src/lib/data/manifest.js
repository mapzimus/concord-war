import { base } from '$app/paths';

/**
 * @typedef {Object} LayerSpec
 * @property {string} id
 * @property {string} group
 * @property {string} label
 * @property {string} geojson
 * @property {string} source_url
 * @property {Record<string, any>} style
 * @property {boolean} visible_default
 * @property {string} [note]
 */

/** @returns {Promise<{version: number, layers: LayerSpec[]}>} */
export async function loadManifest() {
  const r = await fetch(`${base}/data/manifest.json`);
  if (!r.ok) throw new Error(`manifest fetch failed: ${r.status}`);
  return r.json();
}

export async function loadChapters() {
  const r = await fetch(`${base}/data/chapters.json`);
  if (!r.ok) throw new Error(`chapters fetch failed: ${r.status}`);
  return r.json();
}

/** @param {string} fname */
export async function loadGeoJSON(fname) {
  const r = await fetch(`${base}/data/${fname}`);
  if (!r.ok) throw new Error(`geojson fetch failed: ${fname}`);
  return r.json();
}
