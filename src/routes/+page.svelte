<script>
  import { onMount } from 'svelte';
  import { base } from '$app/paths';
  import { loadChapters } from '$lib/data/manifest.js';

  /** @type {Array<{id:string,title:string,subtitle:string,body:string,stats:Array<{label:string,value:string}>}>} */
  let chapters = $state([]);

  onMount(async () => {
    try {
      chapters = (await loadChapters()).chapters ?? [];
    } catch (e) {
      console.warn('chapters load failed', e);
    }
  });
</script>

<svelte:head>
  <title>The War of the Two Banks · Concord NH</title>
  <meta name="description" content="An alternate-history military survey of Concord, New Hampshire — split by the Merrimack River and Interstate 93." />
</svelte:head>

<div class="story">
  <header class="hero">
    <h1>The War of the Two Banks</h1>
    <p class="sub">
      An alternate-history military survey of Concord, New Hampshire — one small city cut
      into three by the Merrimack River and Interstate&nbsp;93: the <em>body</em> in the West,
      the <em>fist</em> in the East, and a contested no-man's-land between them.
    </p>
    <p class="cue">Scroll to read the campaign ↓</p>
  </header>

  {#each chapters as ch, i}
    <section class="chapter">
      <figure>
        <img src={`${base}/story/${ch.id}.png`} alt={ch.title} loading="lazy" />
      </figure>
      <div class="text">
        <h2><span class="num">{String(i + 1).padStart(2, '0')}</span> {ch.title}</h2>
        {#if ch.subtitle}<p class="csub">{ch.subtitle}</p>{/if}
        {#if ch.body}<p class="body">{ch.body}</p>{/if}
        {#if ch.stats?.length}
          <ul class="stats">
            {#each ch.stats as s}
              <li><span class="lab">{s.label}</span><strong>{s.value}</strong></li>
            {/each}
          </ul>
        {/if}
      </div>
    </section>
  {/each}

  <section class="cta">
    <h2>Now explore it yourself</h2>
    <p>The same campaign as a live, interactive map — toggle every layer (military, lifelines, the viewshed, flashpoints), click any installation for its real-world stats and sources.</p>
    <a class="btn" href={`${base}/explore`}>Open the interactive viewer →</a>
  </section>

  <footer>
    Sources: City of Concord GIS · U.S. Census 2020 · USGS NHD &amp; 3DEP · NH Army National Guard.
    An alternate-history exercise — the partition is fiction; every figure traces to real public data.
  </footer>
</div>

<style>
  .story {
    max-width: 920px;
    margin: 0 auto;
    padding: 0 20px 120px;
  }
  .hero {
    min-height: 82vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    border-bottom: 2px solid var(--ink);
    margin-bottom: 60px;
  }
  .hero h1 {
    font-family: var(--font-display);
    font-size: clamp(2.4rem, 6vw, 4.4rem);
    line-height: 1.05;
    margin: 0 0 0.3em;
  }
  .hero .sub {
    font-size: clamp(1rem, 2.2vw, 1.4rem);
    max-width: 40ch;
    color: #4a3b22;
  }
  .hero em { font-style: italic; color: var(--blitz); }
  .cue { margin-top: 2.4em; letter-spacing: 0.18em; text-transform: uppercase; font-size: 0.8rem; color: #6b5a2a; }

  .chapter { margin: 0 0 96px; }
  figure {
    margin: 0 0 18px;
    border: 1px solid var(--ink);
    box-shadow: 0 6px 26px rgba(58, 47, 29, 0.18);
    background: var(--parchment);
  }
  figure img { display: block; width: 100%; height: auto; }
  .text { max-width: 64ch; }
  h2 {
    font-family: var(--font-display);
    font-size: 1.9rem;
    margin: 0 0 0.2em;
  }
  .num { color: var(--blitz); margin-right: 0.3em; }
  .csub { font-style: italic; color: var(--blitz); margin: 0 0 0.6em; font-size: 1.05rem; }
  .body { font-size: 1.08rem; line-height: 1.65; }
  .stats {
    list-style: none;
    padding: 0;
    margin: 1.2em 0 0;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 10px;
  }
  .stats li {
    border-top: 2px solid var(--ink);
    padding-top: 6px;
    display: flex;
    flex-direction: column;
  }
  .stats .lab { font-size: 0.82rem; color: #6b5a2a; }
  .stats strong { font-size: 1.25rem; font-family: var(--font-display); }

  .cta {
    text-align: center;
    border: 2px solid var(--ink);
    background: rgba(215, 197, 151, 0.4);
    padding: 48px 28px;
    margin: 40px 0 60px;
  }
  .cta h2 { font-size: 2.1rem; }
  .cta p { max-width: 52ch; margin: 0 auto 1.6em; font-size: 1.05rem; }
  .btn {
    display: inline-block;
    background: var(--ink);
    color: var(--parchment);
    text-decoration: none;
    font-family: var(--font-display);
    font-size: 1.15rem;
    padding: 14px 28px;
    border: 1px solid var(--ink);
    transition: background 150ms;
  }
  .btn:hover { background: var(--blitz); }
  footer { font-size: 0.8rem; color: #6b5a2a; text-align: center; border-top: 1px solid var(--parchment-dark); padding-top: 18px; }
</style>
