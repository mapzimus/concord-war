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
        specs = [],
        onPick = (/** @type {any} */ _p) => {} } = $props();

  /** @type {HTMLDivElement | undefined} */
  let container = $state();

  /** @type {maplibregl.Map | null} */
  let map = null;
  /** @type {MapboxOverlay | null} */
  let overlay = null;
  // Animation clock (ms); bumped by rAF only while an offensive arc is visible.
  let frame = $state(0);

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
    overlay = new MapboxOverlay({
      interleaved: false,
      layers: [],
      onClick: (info) => {
        if (info && info.object && info.layer && !info.layer.id.endsWith('__labels')) {
          onPick({ layerId: info.layer.id, properties: info.object.properties || {} });
        } else {
          onPick(null);
        }
      },
      getCursor: ({ isHovering, isDragging }) =>
        isDragging ? 'grabbing' : isHovering ? 'pointer' : 'grab'
    });
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

  // Reactive: re-render deck layers when visible set, geo cache, or animation
  // frame changes. `frame` advances ~60fps only while an arc layer is on, which
  // is what crawls the tracer dots; otherwise this runs only on data changes.
  $effect(() => {
    if (!overlay) return;
    const t = (frame % 2500) / 2500;
    overlay.setProps({ layers: buildDeckLayers(visible, geo, specs, t) });
  });

  // Reactive: drive the rAF clock only while an offensive arc layer is visible,
  // so an idle explorer pays no per-frame cost.
  $effect(() => {
    const animating = specs.some((s) => s.style?.arc && visible.has(s.id));
    if (!animating) return;
    let raf = 0;
    const loop = () => {
      frame = performance.now();
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  });

  // Reactive: enable real 3D terrain when the terrain_3d layer is on (High Ground).
  $effect(() => {
    if (!map) return;
    const want3d = visible.has('terrain_3d');
    const apply = () => {
      try {
        map?.setTerrain(want3d ? { source: 'terrarium', exaggeration: 1.4 } : null);
      } catch (e) {
        /* style not ready yet */
      }
    };
    if (map.isStyleLoaded()) apply();
    else map.once('load', apply);
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
