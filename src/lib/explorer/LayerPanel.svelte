<script>
  import { visibleLayers, toggleLayer, applyChapterLayers } from '../data/stores.js';

  /** @type {{ specs: import('../data/manifest.js').LayerSpec[], defaultOn?: string[] }} */
  let { specs = [], defaultOn = [] } = $props();

  let collapsed = $state(false);
  /** @type {Set<string>} */
  let openGroups = $state(new Set());

  let groups = $derived(groupBy(specs, (s) => s.group));
  let totalOn = $derived($visibleLayers.size);

  // Open every group the first time specs arrive (preserves "nothing is hidden"
  // while still making each group individually collapsible).
  let inited = false;
  $effect(() => {
    if (specs.length && !inited) {
      inited = true;
      openGroups = new Set(Object.keys(groups));
    }
  });

  /**
   * @template T
   * @param {T[]} arr
   * @param {(t: T) => string} keyFn
   * @returns {Record<string, T[]>}
   */
  function groupBy(arr, keyFn) {
    /** @type {Record<string, T[]>} */
    const out = {};
    for (const item of arr) {
      const k = keyFn(item);
      (out[k] ??= []).push(item);
    }
    return out;
  }
  /** @param {string} g */
  function toggleGroup(g) {
    const n = new Set(openGroups);
    n.has(g) ? n.delete(g) : n.add(g);
    openGroups = n;
  }
  function hideAll() {
    visibleLayers.set(new Set());
  }
  function reset() {
    applyChapterLayers(defaultOn);
  }
  /** @param {Record<string, any>} style */
  function swatch(style) {
    return style.point || style.fill || style.line || '#3a2f1d';
  }
</script>

<aside class="panel" class:collapsed aria-label="Layer panel">
  <div class="phead">
    <strong>Layers</strong>
    <span class="count">{totalOn} on</span>
    <button class="hd" onclick={() => (collapsed = !collapsed)} aria-label="Collapse layer panel">
      {collapsed ? '▸' : '▾'}
    </button>
  </div>

  {#if !collapsed}
    <div class="acts">
      <button onclick={reset} title="Restore the default layer set">Reset</button>
      <button onclick={hideAll} title="Turn every layer off">Hide all</button>
    </div>
    <div class="groups">
      {#each Object.entries(groups) as [group, gl]}
        {@const on = gl.filter((l) => $visibleLayers.has(l.id)).length}
        <section class="group">
          <button class="glabel" onclick={() => toggleGroup(group)}>
            <span>{group}</span>
            <span class="gc">{on}/{gl.length} {openGroups.has(group) ? '▾' : '▸'}</span>
          </button>
          {#if openGroups.has(group)}
            {#each gl as l}
              <label class="row">
                <input
                  type="checkbox"
                  checked={$visibleLayers.has(l.id)}
                  onchange={() => toggleLayer(l.id)}
                />
                <span class="sw" style="background:{swatch(l.style)}"></span>
                <span class="lname">{l.label}</span>
              </label>
            {/each}
          {/if}
        </section>
      {/each}
    </div>
  {/if}
</aside>

<style>
  .panel {
    background: rgba(231, 220, 192, 0.96);
    border: 1px solid var(--ink);
    box-shadow: 0 4px 18px rgba(58, 47, 29, 0.2);
    width: 270px;
    max-width: 82vw;
    font-size: 0.9rem;
    display: flex;
    flex-direction: column;
    max-height: calc(100vh - 32px);
  }
  .phead {
    display: flex;
    align-items: center;
    gap: 8px;
    background: var(--ink);
    color: var(--parchment);
    padding: 8px 12px;
    font-family: var(--font-display);
  }
  .phead strong { flex: 1; }
  .count { font-size: 0.72rem; opacity: 0.85; }
  .hd {
    background: none; border: none; color: var(--parchment);
    cursor: pointer; font-size: 1rem; line-height: 1;
  }
  .acts { display: flex; gap: 6px; padding: 8px 12px 4px; }
  .acts button {
    flex: 1; background: var(--parchment-dark); border: 1px solid var(--ink);
    padding: 4px; cursor: pointer; font-size: 0.78rem; font-family: inherit;
  }
  .acts button:hover { background: #d7c597; }
  .groups { overflow-y: auto; padding: 4px 0 8px; }
  .glabel {
    width: 100%; display: flex; justify-content: space-between; align-items: center;
    background: rgba(216, 200, 164, 0.5); border: none;
    border-top: 1px solid var(--parchment-dark);
    padding: 6px 12px; cursor: pointer; font-weight: 700;
    font-family: var(--font-display); font-size: 0.9rem;
  }
  .glabel:hover { background: rgba(216, 200, 164, 0.85); }
  .gc { font-size: 0.72rem; color: #6b5a2a; font-weight: 400; }
  .row { display: flex; align-items: center; gap: 7px; padding: 3px 12px 3px 18px; }
  .sw { width: 11px; height: 11px; border: 1px solid var(--ink); border-radius: 2px; flex: none; }
  .lname { line-height: 1.2; }
</style>
