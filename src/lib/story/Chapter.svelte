<script>
  /** @type {{
   *   chapter: { id: string, title: string, subtitle: string, body: string, stats: Array<{label: string, value: string}> },
   *   active?: boolean
   * }} */
  let { chapter, active = false } = $props();
</script>

<article id={chapter.id} class="chapter" class:active>
  <h2>{chapter.title}</h2>
  {#if chapter.subtitle}<p class="subtitle">{chapter.subtitle}</p>{/if}
  {#if chapter.body}<p class="body">{chapter.body}</p>{/if}
  {#if chapter.stats?.length}
    <ul class="stats">
      {#each chapter.stats as s}
        <li><span class="label">{s.label}</span><span class="value">{s.value}</span></li>
      {/each}
    </ul>
  {/if}
</article>

<style>
  .chapter {
    background: rgba(231, 220, 192, 0.92);
    border: 1px solid var(--ink);
    padding: 24px 28px;
    margin: 60vh 0;
    max-width: 480px;
    transition: box-shadow 200ms;
  }
  .chapter.active {
    box-shadow: 0 6px 24px rgba(58, 47, 29, 0.18);
  }
  h2 { font-family: var(--font-display); font-size: 1.8rem; }
  .subtitle { font-style: italic; color: var(--blitz); margin-top: -0.4em; }
  .body { font-size: 1rem; line-height: 1.55; }
  .stats { list-style: none; padding: 0; margin: 1em 0 0; }
  .stats li { display: flex; justify-content: space-between; border-top: 1px solid var(--parchment-dark); padding: 6px 0; }
  .label { color: var(--ink); }
  .value { font-weight: 700; }
</style>
