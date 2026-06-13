<script>
  import { visibleLayers, toggleLayer } from '../data/stores.js';

  /** @type {{ specs: import('../data/manifest.js').LayerSpec[] }} */
  let { specs = [] } = $props();

  let groups = $derived(groupBy(specs, (s) => s.group));

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
</script>

<aside class="panel" aria-label="Layer toggle panel">
  <h3>Layers</h3>
  {#each Object.entries(groups) as [group, layers]}
    <fieldset>
      <legend>{group}</legend>
      {#each layers as l}
        <label class="row">
          <input
            type="checkbox"
            checked={$visibleLayers.has(l.id)}
            onchange={() => toggleLayer(l.id)}
          />
          <span>{l.label}</span>
        </label>
      {/each}
    </fieldset>
  {/each}
</aside>

<style>
  .panel {
    background: rgba(231, 220, 192, 0.95);
    border: 1px solid var(--ink);
    padding: 14px 18px;
    max-width: 280px;
    font-size: 0.92rem;
  }
  h3 { font-family: var(--font-display); margin-top: 0; }
  fieldset { border: none; padding: 0; margin: 0 0 14px; }
  legend { font-weight: 700; padding: 0 0 6px; }
  .row { display: flex; align-items: center; gap: 8px; padding: 3px 0; }
</style>
