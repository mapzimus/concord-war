<script>
  import { onMount, onDestroy } from 'svelte';
  import maplibregl from 'maplibre-gl';
  import 'maplibre-gl/dist/maplibre-gl.css';
  import { MapboxOverlay } from '@deck.gl/mapbox';
  import style from './mapStyle.json';
  import { buildDeckLayers } from './deckLayers.js';

  /** @type {{
   *   camera: {center: [number, number], zoom: number, pitch?: number, bearing?: number},
   *   visible: Set<string>,
   *   geo: Record<string, object>,
   *   specs: import('../data/manifest.js').LayerSpec[]
   * }} */
  let { camera = { center: [-71.538, 43.207], zoom: 11, pitch: 0, bearing: 0 },
        visible = new Set(),
        geo = {},
        specs = [] } = $props();

  /** @type {HTMLDivElement | undefined} */
  let container = $state();

  /** @type {maplibregl.Map | null} */
  let map = null;
  /** @type {MapboxOverlay | null} */
  let overlay = null;

  onMount(() => {
    map = new maplibregl.Map({
      container,
      style,
      center: camera.center,
      zoom: camera.zoom,
      pitch: camera.pitch ?? 0,
      bearing: camera.bearing ?? 0,
      attributionControl: false
    });
    map.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right');
    overlay = new MapboxOverlay({ interleaved: false, layers: [] });
    map.on('load', () => {
      map?.addControl(overlay);
      overlay?.setProps({ layers: buildDeckLayers(visible, geo, specs) });
    });
  });

  onDestroy(() => {
    map?.remove();
    map = null;
  });

  // Reactive: re-fly when camera changes
  $effect(() => {
    if (!map || !camera) return;
    map.flyTo({
      center: camera.center,
      zoom: camera.zoom,
      pitch: camera.pitch ?? 0,
      bearing: camera.bearing ?? 0,
      duration: 1800,
      essential: true
    });
  });

  // Reactive: re-render deck layers when visible set or geo cache changes
  $effect(() => {
    if (!overlay) return;
    overlay.setProps({ layers: buildDeckLayers(visible, geo, specs) });
  });
</script>

<div class="map" bind:this={container}></div>

<style>
  .map {
    width: 100%;
    height: 100%;
    min-height: 480px;
  }
</style>
