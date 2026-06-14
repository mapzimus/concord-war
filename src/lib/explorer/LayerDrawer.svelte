<script>
  import { selectedFeature, clearSelection } from '../data/stores.js';

  /** @type {{ specs: import('../data/manifest.js').LayerSpec[] }} */
  let { specs = [] } = $props();

  let f = $derived($selectedFeature);
  let spec = $derived(f ? specs.find((s) => s.id === f.layerId) : null);

  const SKIP = new Set(['name', 'side', 'note', 'OBJECTID', 'id', 'geometry']);

  /** @param {Record<string, any>} props */
  function rows(props) {
    if (!props) return [];
    return Object.entries(props).filter(
      ([k, v]) => !SKIP.has(k) && v !== null && v !== '' && typeof v !== 'object'
    );
  }
</script>

{#if f}
  <aside class="drawer" aria-label="Feature details">
    <button class="close" onclick={clearSelection} aria-label="Close">×</button>
    <h3>{f.properties.name ?? spec?.label ?? 'Feature'}</h3>
    <div class="meta">
      {#if spec}<span class="layer">{spec.label}</span>{/if}
      {#if f.properties.side}<span class="badge badge-{String(f.properties.side).toLowerCase()}">{f.properties.side}</span>{/if}
    </div>
    {#if f.properties.note}<p class="note">{f.properties.note}</p>{/if}
    {#if f.properties.blurb}<p class="note">{f.properties.blurb}</p>{/if}
    {#if rows(f.properties).length}
      <dl>
        {#each rows(f.properties) as [k, v]}
          <div class="row"><dt>{k}</dt><dd>{v}</dd></div>
        {/each}
      </dl>
    {/if}
    {#if spec?.source_url}
      <p class="src">Source: {spec.source_url}</p>
    {/if}
  </aside>
{/if}

<style>
  .drawer {
    position: fixed;
    top: 24px;
    left: 24px;
    width: min(34vw, 380px);
    max-height: calc(100vh - 48px);
    overflow-y: auto;
    background: rgba(231, 220, 192, 0.97);
    border: 1px solid var(--ink);
    box-shadow: 0 8px 28px rgba(58, 47, 29, 0.25);
    padding: 18px 22px 22px;
    z-index: 6;
  }
  .close {
    position: absolute;
    top: 8px;
    right: 12px;
    background: none;
    border: none;
    font-size: 1.6rem;
    line-height: 1;
    cursor: pointer;
    color: var(--ink);
  }
  h3 {
    font-family: var(--font-display);
    font-size: 1.3rem;
    margin: 0 24px 6px 0;
  }
  .meta { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-bottom: 8px; }
  .layer { font-size: 0.82rem; color: #6b5a2a; }
  .badge {
    font-size: 0.72rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 2px;
    border: 1px solid var(--ink);
  }
  .badge-east { background: var(--east); }
  .badge-west { background: var(--west); }
  .badge-contested { background: #c4825a; color: #fff; }
  .note { font-size: 0.92rem; line-height: 1.45; margin: 8px 0; }
  dl { margin: 10px 0 0; }
  .row { display: flex; justify-content: space-between; gap: 12px; border-top: 1px solid var(--parchment-dark); padding: 5px 0; font-size: 0.86rem; }
  dt { color: #6b5a2a; text-transform: lowercase; }
  dd { margin: 0; font-weight: 600; text-align: right; }
  .src { margin-top: 12px; font-size: 0.72rem; color: #6b5a2a; word-break: break-word; }
</style>
