<script>
  import { onMount } from 'svelte';
  import ConcordMap from '$lib/map/ConcordMap.svelte';
  import Scrollytelling from '$lib/story/Scrollytelling.svelte';
  import LayerPanel from '$lib/explorer/LayerPanel.svelte';
  import LayerDrawer from '$lib/explorer/LayerDrawer.svelte';
  import ForcesDashboard from '$lib/dashboard/ForcesDashboard.svelte';
  import { loadManifest, loadChapters, loadGeoJSON } from '$lib/data/manifest.js';
  import { visibleLayers, applyChapterLayers, setChapter, selectFeature, clearSelection } from '$lib/data/stores.js';

  /** @type {import('$lib/data/manifest.js').LayerSpec[]} */
  let specs = $state([]);
  let chapters = $state([]);
  /** @type {Record<string, object>} */
  let geo = $state({});
  /** @type {any[]} */
  let installations = $state([]);
  let camera = $state({ center: [-71.538, 43.207], zoom: 11, pitch: 0, bearing: 0 });

  /** Set of layer ids that have been fetched (or are in flight). */
  const inflight = new Set();

  /** @param {string[]} ids — fetch each layer's GeoJSON if not already loaded. */
  async function loadLayers(ids) {
    const targets = ids.filter((id) => !geo[id] && !inflight.has(id) && specs.find((s) => s.id === id));
    if (targets.length === 0) return;
    for (const id of targets) inflight.add(id);
    const results = await Promise.all(
      targets.map(async (id) => {
        const spec = specs.find((s) => s.id === id);
        try {
          const data = await loadGeoJSON(spec.geojson);
          return /** @type {const} */ ([id, data]);
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
    const c = await loadChapters();
    chapters = c.chapters;
    try {
      installations = (await loadGeoJSON('installations.json')).installations ?? [];
    } catch (e) {
      console.warn('installations.json load failed', e);
    }
    // Apply chapter 1's camera + layers on initial mount so the first paint
    // matches the intended view (scrollama only fires once cards intersect).
    if (chapters.length > 0) {
      camera = { ...chapters[0].camera };
      setChapter(chapters[0].id);
      applyChapterLayers(chapters[0].layers);
      // Preload only chapter 1's layers — the rest fetch on first toggle.
      await loadLayers(chapters[0].layers);
    }
  });

  // Lazy-load any newly-visible layer that isn't in geo yet (e.g. user toggled
  // a checkbox on or scrolled into a chapter that needs heavier layers).
  $effect(() => {
    const ids = Array.from($visibleLayers);
    if (ids.length === 0 || specs.length === 0) return;
    loadLayers(ids);
  });

  /** @param {any} ch */
  function handleChapter(ch) {
    camera = { ...ch.camera };
  }
</script>

<svelte:head>
  <title>The War of the Two Banks · Concord NH</title>
</svelte:head>

<div class="layout">
  <div class="map-pane">
    <ConcordMap
      {camera}
      visible={$visibleLayers}
      {geo}
      {specs}
      onPick={(p) => (p ? selectFeature(p) : clearSelection())}
    />
  </div>

  <div class="story-pane">
    <Scrollytelling {chapters} onChapter={handleChapter} />
  </div>

  <div class="panel-pane">
    <LayerPanel {specs} />
  </div>

  <LayerDrawer {specs} {installations} />

  <ForcesDashboard />
</div>

<style>
  .layout {
    position: relative;
    width: 100vw;
    min-height: 100vh;
  }
  .map-pane {
    position: sticky;
    top: 0;
    width: 100%;
    height: 100vh;
    z-index: 1;
  }
  .story-pane {
    position: absolute;
    top: 0;
    left: 24px;
    width: min(40vw, 520px);
    z-index: 3;
  }
  .panel-pane {
    position: fixed;
    top: 24px;
    right: 24px;
    z-index: 4;
  }
</style>
