<script>
  import { onMount } from 'svelte';
  import { base } from '$app/paths';
  import ConcordMap from '$lib/map/ConcordMap.svelte';
  import LayerPanel from '$lib/explorer/LayerPanel.svelte';
  import LayerDrawer from '$lib/explorer/LayerDrawer.svelte';
  import ForcesDashboard from '$lib/dashboard/ForcesDashboard.svelte';
  import { loadManifest, loadGeoJSON } from '$lib/data/manifest.js';
  import { visibleLayers, applyChapterLayers, selectFeature, clearSelection, toggleLayer } from '$lib/data/stores.js';

  /** @type {import('$lib/data/manifest.js').LayerSpec[]} */
  let specs = $state([]);
  /** @type {Record<string, object>} */
  let geo = $state({});
  /** @type {any[]} */
  let installations = $state([]);
  let camera = $state({ center: [-71.54, 43.22], zoom: 11.2, pitch: 0, bearing: 0 });
  let showIntro = $state(true);
  let is3d = $derived($visibleLayers.has('terrain_3d'));

  // Toggle real 3D terrain, and tilt/flatten the camera to match. We read the
  // CURRENT state to decide the next pitch, because the store's value won't be
  // reflected in `is3d` until after this handler returns.
  function toggle3d() {
    const enabling = !$visibleLayers.has('terrain_3d');
    toggleLayer('terrain_3d');
    camera = { ...camera, pitch: enabling ? 55 : 0, bearing: enabling ? -18 : 0 };
  }

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

  <button class="d3" class:on={is3d} onclick={toggle3d} title="Toggle 3D terrain">
    {is3d ? '3D ✓' : '3D'}
  </button>

  <div class="panel-pane">
    <LayerPanel {specs} defaultOn={DEFAULT_ON} />
  </div>

  <LayerDrawer {specs} {installations} />
  <ForcesDashboard />

  {#if showIntro}
    <div class="intro" role="dialog" aria-label="How to use this map">
      <button class="x" onclick={() => (showIntro = false)} aria-label="Dismiss">×</button>
      <h2>The War of the Two Banks — live map</h2>
      <p>
        Concord, split by the Merrimack and I-93 into <b>West</b> (the body),
        <b>East</b> (the fist), and a striped <b>contested</b> seam. Toggle layers
        in the panel, hit <b>3D</b> for terrain, and <b>click any marker</b> for its
        real-world stats and sources.
      </p>
      <button class="go" onclick={() => (showIntro = false)}>Explore →</button>
    </div>
  {/if}
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
  .d3 {
    position: fixed;
    bottom: 16px;
    right: 16px;
    z-index: 8;
    background: var(--parchment);
    color: var(--ink);
    border: 1px solid var(--ink);
    font-family: var(--font-display);
    font-size: 0.9rem;
    padding: 8px 14px;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(58, 47, 29, 0.25);
  }
  .d3.on { background: var(--ink); color: var(--parchment); }

  .intro {
    position: fixed;
    left: 50%;
    bottom: 24px;
    transform: translateX(-50%);
    z-index: 9;
    width: min(460px, 90vw);
    background: rgba(231, 220, 192, 0.98);
    border: 2px solid var(--ink);
    box-shadow: 0 8px 30px rgba(58, 47, 29, 0.35);
    padding: 18px 22px 20px;
  }
  .intro h2 { font-family: var(--font-display); margin: 0 0 8px; font-size: 1.25rem; }
  .intro p { margin: 0 0 14px; font-size: 0.95rem; line-height: 1.5; }
  .intro b { color: var(--blitz); }
  .intro .go {
    background: var(--ink); color: var(--parchment); border: none;
    font-family: var(--font-display); font-size: 1rem; padding: 8px 18px; cursor: pointer;
  }
  .intro .go:hover { background: var(--blitz); }
  .intro .x {
    position: absolute; top: 6px; right: 10px;
    background: none; border: none; font-size: 1.4rem; line-height: 1;
    color: var(--ink); cursor: pointer;
  }

  /* On phones, free the corners: the panel sits top-left and starts collapsed-friendly,
     the 3D button shrinks, and the intro never collides with the attribution. */
  @media (max-width: 600px) {
    .panel-pane { right: 8px; top: 8px; }
    .back { font-size: 0.85rem; padding: 6px 10px; }
    .d3 { bottom: 12px; right: 12px; padding: 6px 10px; }
    .intro { bottom: 64px; }
  }
</style>
