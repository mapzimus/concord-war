<script>
  import { onMount, onDestroy } from 'svelte';
  import scrollama from 'scrollama';
  import Chapter from './Chapter.svelte';
  import { setChapter, applyChapterLayers } from '../data/stores.js';

  /** @type {{
   *   chapters: Array<{id: string, title: string, subtitle: string, body: string, stats: any[], camera: any, layers: string[]}>,
   *   onChapter?: (chapter: any) => void
   * }} */
  let { chapters = [], onChapter = () => {} } = $props();

  /** @type {ReturnType<typeof scrollama> | undefined} */
  let scroller;

  onMount(() => {
    scroller = scrollama();
    scroller
      .setup({ step: '.chapter', offset: 0.5, debug: false })
      .onStepEnter((response) => {
        const idx = Number(response.element.dataset.idx);
        const ch = chapters[idx];
        if (!ch) return;
        setChapter(ch.id);
        applyChapterLayers(ch.layers);
        onChapter(ch);
        response.element.classList.add('active');
      })
      .onStepExit((response) => {
        response.element.classList.remove('active');
      });
    const resize = () => scroller?.resize();
    window.addEventListener('resize', resize);
  });

  onDestroy(() => {
    scroller?.destroy();
  });
</script>

<div class="scrolly">
  {#each chapters as ch, idx}
    <div data-idx={idx}>
      <Chapter chapter={ch} />
    </div>
  {/each}
</div>

<style>
  .scrolly {
    position: relative;
    pointer-events: none;
  }
  .scrolly > div {
    pointer-events: auto;
  }
</style>
