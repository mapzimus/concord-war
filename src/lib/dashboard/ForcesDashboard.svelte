<script>
  import { base } from '$app/paths';
  import { onMount } from 'svelte';

  /** @type {Array<{key:string,label:string,west:string,east:string,unit:string,advantage:string,source_url:string}>} */
  let metrics = $state([]);
  let open = $state(true);

  onMount(async () => {
    try {
      const r = await fetch(`${base}/data/forces.json`);
      if (r.ok) metrics = (await r.json()).metrics ?? [];
    } catch (e) {
      console.warn('forces.json load failed', e);
    }
  });
</script>

{#if metrics.length}
  <aside class="dash" aria-label="Forces dashboard">
    <button class="hdr" onclick={() => (open = !open)}>
      <span>⚔ FORCES · West vs East</span>
      <span class="chev">{open ? '▾' : '▸'}</span>
    </button>
    {#if open}
      <div class="body">
        {#each metrics as m}
          <div class="metric">
            <div class="mlabel">{m.label}</div>
            <div class="vals">
              <div class="v west" class:adv={m.advantage === 'West' || m.advantage === 'Contested'}>{m.west}</div>
              <div class="v east" class:adv={m.advantage === 'East' || m.advantage === 'Contested'}>{m.east}</div>
            </div>
          </div>
        {/each}
        <p class="foot">Every figure traces to public data. Partition into warring zones is alternate-history fiction.</p>
      </div>
    {/if}
  </aside>
{/if}

<style>
  .dash {
    position: fixed;
    left: 24px;
    bottom: 24px;
    width: min(33vw, 340px);
    background: rgba(231, 220, 192, 0.96);
    border: 1px solid var(--ink);
    box-shadow: 0 6px 22px rgba(58, 47, 29, 0.22);
    z-index: 5;
    font-size: 0.82rem;
  }
  .hdr {
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: var(--ink);
    color: var(--parchment);
    border: none;
    padding: 8px 12px;
    font-family: var(--font-display);
    font-weight: 700;
    font-size: 0.92rem;
    cursor: pointer;
    letter-spacing: 0.04em;
  }
  .body { max-height: 46vh; overflow-y: auto; padding: 8px 12px 4px; }
  .metric { border-bottom: 1px solid var(--parchment-dark); padding: 6px 0; }
  .mlabel { font-weight: 600; color: #4a3b22; margin-bottom: 3px; }
  .vals { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  .v { padding: 3px 6px; border-radius: 2px; line-height: 1.25; }
  .v.west { background: rgba(215, 197, 151, 0.45); }
  .v.east { background: rgba(188, 198, 168, 0.45); }
  .v.adv { font-weight: 700; outline: 1.5px solid var(--blitz); }
  .foot { font-size: 0.66rem; color: #6b5a2a; margin: 8px 0 4px; line-height: 1.3; }
</style>
