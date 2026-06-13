<script>
  import { onMount } from 'svelte';
  import ConcordMap from '$lib/map/ConcordMap.svelte';
  import Scrollytelling from '$lib/story/Scrollytelling.svelte';
  import LayerPanel from '$lib/explorer/LayerPanel.svelte';
  import { loadManifest, loadChapters, loadGeoJSON } from '$lib/data/manifest.js';
  import { visibleLayers } from '$lib/data/stores.js';

  /** @type {import('$lib/data/manifest.js').LayerSpec[]} */
  let specs = $state([]);
  let chapters = $state([]);
  /** @type {Record<string, object>} */
  let geo = $state({});
  let camera = $state({ center: [-71.538, 43.207], zoom: 11, pitch: 0, bearing: 0 });

  onMount(async () => {
    const m = await loadManifest();
    specs = m.layers;
    const c = await loadChapters();
    chapters = c.chapters;
    // Lazy-load every layer's GeoJSON (Pass A only has 6 small files; fine to load all)
    const loaded = {};
    await Promise.all(specs.map(async (s) => {
      loaded[s.id] = await loadGeoJSON(s.geojson);
    }));
    geo = loaded;
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
    <ConcordMap {camera} visible={$visibleLayers} {geo} {specs} />
  </div>

  <div class="story-pane">
    <Scrollytelling {chapters} onChapter={handleChapter} />
  </div>

  <div class="panel-pane">
    <LayerPanel {specs} />
  </div>
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
