<script>
  import { onMount } from 'svelte';
  import { base } from '$app/paths';
  import ConcordMap from '$lib/map/ConcordMap.svelte';
  import LayerPanel from '$lib/explorer/LayerPanel.svelte';
  import LayerDrawer from '$lib/explorer/LayerDrawer.svelte';
  import ForcesDashboard from '$lib/dashboard/ForcesDashboard.svelte';
  import { loadManifest, loadGeoJSON } from '$lib/data/manifest.js';
  import { visibleLayers, applyChapterLayers, selectFeature, clearSelection } from '$lib/data/stores.js';

  /** @type {import('$lib/data/manifest.js').LayerSpec[]} */
  let specs = $state([]);
  /** @type {Record<string, object>} */
  let geo = $state({});
  /** @type {any[]} */
  let installations = $state([]);
  let camera = $state({ center: [-71.54, 43.22], zoom: 11.2, pitch: 0, bearing: 0 });

  const DEFAULT_ON = [
    'city', 'river', 'front_line',
    'territory_west', 'territory_east', 'territory_contested', 'territory_contested_stripes',
    'crossings', 'flashpoints'
  ];

  const inflight = new Set();
  /** @param {string[]} ids */
  async function loadLayers(ids) {
    const targets = ids.filter(
      (id) => !geo[id] && !inflight.has(id) && specs.find((s) => s.id === id && s.geojson)
    );
    if (targets.length === 0) return;
    for (const id of targets) inflight.add(id);
    const results = await Promise.all(
      targets.map(async (id) => {
        const spec = specs.find((s) => s.id === id);
        try {
          return /** @type {const} */ ([id, await loadGeoJSON(spec.geojson)]);
        } catch (err) {
          console.warn(`failed to load ${spec.geojson}:`, err);
          return null;
        }
      })
    );
    const next = { ...geo };
    for (const r of results) if (r) next[r[0]] = r[1];
    geo = next;
    for (const id of targets) inflight.delete(id);
  }

  onMount(async () => {
    const m = await loadManifest();
    specs = m.layers;
    try {
      installations = (await loadGeoJSON('installations.json')).installations ?? [];
    } catch (e) {
      console.warn('installations load failed', e);
    }
    applyChapterLayers(DEFAULT_ON);
    await loadLayers(DEFAULT_ON);
  });

  // Lazy-load any newly-toggled layer.
  $effect(() => {
    const ids = Array.from($visibleLayers);
    if (ids.length === 0 || specs.length === 0) return;
    loadLayers(ids);
  });
</script>

<svelte:head>
  <title>Explore · The War of the Two Banks</title>
</svelte:head>

<div class="explore">
  <div class="map-pane">
    <ConcordMap
      {camera}
      visible={$visibleLayers}
      {geo}
      {specs}
      onPick={(p) => (p ? selectFeature(p) : clearSelection())}
    />
  </div>

  <a class="back" href={`${base}/`}>← The story</a>

  <div class="panel-pane">
    <LayerPanel {specs} />
  </div>

  <LayerDrawer {specs} {installations} />
  <ForcesDashboard />
</div>

<style>
  .explore {
    position: fixed;
    inset: 0;
    overflow: hidden;
  }
  .map-pane {
    position: absolute;
    inset: 0;
    z-index: 1;
  }
  .back {
    position: fixed;
    top: 16px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 8;
    background: var(--ink);
    color: var(--parchment);
    text-decoration: none;
    font-family: var(--font-display);
    font-size: 0.95rem;
    padding: 8px 14px;
    border: 1px solid var(--ink);
  }
  .back:hover { background: var(--blitz); }
  .panel-pane {
    position: fixed;
    top: 16px;
    right: 16px;
    z-index: 4;
    max-height: calc(100vh - 32px);
    overflow-y: auto;
  }
</style>
