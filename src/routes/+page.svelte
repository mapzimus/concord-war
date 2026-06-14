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
  <meta name="description" content="An alternate-history military survey of Concord, New Hampshire — split by the Merrimack River and Interstate 93, rendered in 3D relief from real elevation data." />
</svelte:head>

<div class="story">
  <header class="hero">
    <h1>The War of the Two Banks</h1>
    <p class="sub">
      An alternate-history military survey of Concord, New Hampshire — one small city cut
      into three by the Merrimack River and Interstate&nbsp;93: the <em>body</em> in the West,
      the <em>fist</em> in the East, and a contested no-man's-land between.
    </p>
  </header>

  <figure class="hero-map">
    <img src={`${base}/maps/hero_3d_poster.png`} alt="3D relief campaign map of Concord, NH split into West and East banks" />
    <figcaption>
      The campaign in 3D — terrain path-traced from the USGS 10&nbsp;m elevation model,
      with both banks' key military and civic assets called out.
    </figcaption>
  </figure>

  <section class="feature">
    <figure>
      <img src={`${base}/maps/hero_3d_spin.gif`} alt="Rotating 3D view of the Concord terrain" loading="lazy" />
    </figure>
    <div class="ftext">
      <h2>Terrain decides everything</h2>
      <p>
        Concord's war is a river war. The Merrimack and the I-93 corridor carve the city in
        two, and the East holds the high ground at Oak Hill. Spin the model: every bridge,
        ridge, and floodplain that a campaign would turn on is real elevation, not artistic
        licence.
      </p>
    </div>
  </section>

  <section class="feature reverse">
    <figure>
      <img src={`${base}/maps/hero_relief.png`} alt="2D shaded-relief map of the Concord territories" loading="lazy" />
    </figure>
    <div class="ftext">
      <h2>The same ground, read flat</h2>
      <p>
        A shaded-relief survey of the partition: West and East territories draped over the
        hillshade, the front line, the river crossings that become chokepoints, and every
        sourced asset. Everything outside the city fades to parchment so the contested
        ground reads first.
      </p>
    </div>
  </section>

  <section class="campaign">
    <h2 class="ch-head">The campaign, bank by bank</h2>
    {#each chapters as ch, i}
      <article class="chapter">
        <figure class="chmap">
          <img src={`${base}/story/${ch.id}.png`} alt={`Relief map — ${ch.title}`} loading="lazy" />
        </figure>
        <div class="chtext">
          <h3><span class="num">{String(i + 1).padStart(2, '0')}</span> {ch.title}</h3>
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
      </article>
    {/each}
  </section>

  <section class="cta">
    <h2>Now explore it yourself</h2>
    <p>The same campaign as a live, interactive map — toggle every layer (military, lifelines, the viewshed, flashpoints), flip on 3D terrain, and click any installation for its real-world stats and sources.</p>
    <a class="btn" href={`${base}/explore`}>Open the interactive viewer →</a>
  </section>

  <footer>
    Relief from USGS 3DEP 10&nbsp;m DEM (×2 vertical exaggeration) · City of Concord GIS · U.S. Census 2020 · USGS NHD · NH Army National Guard.
    Built in R (rayshader / terra / sf). An alternate-history exercise — the partition is fiction; every figure traces to real public data.
  </footer>
</div>

<style>
  .story {
    max-width: 1040px;
    margin: 0 auto;
    padding: 0 20px 120px;
  }
  .hero {
    min-height: 56vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    margin-bottom: 24px;
  }
  .hero h1 {
    font-family: var(--font-display);
    font-size: clamp(2.4rem, 6vw, 4.6rem);
    line-height: 1.04;
    margin: 0 0 0.3em;
  }
  .hero .sub {
    font-size: clamp(1rem, 2.2vw, 1.4rem);
    max-width: 44ch;
    color: #4a3b22;
  }
  .hero em { font-style: italic; color: var(--blitz); }

  .hero-map {
    margin: 0 0 80px;
    border: 1px solid var(--ink);
    box-shadow: 0 10px 40px rgba(58, 47, 29, 0.28);
    background: var(--parchment);
  }
  .hero-map img { display: block; width: 100%; height: auto; }
  figcaption {
    font-size: 0.9rem;
    color: #6b5a2a;
    padding: 10px 16px;
    border-top: 1px solid var(--parchment-dark);
    font-style: italic;
  }

  .feature {
    display: grid;
    grid-template-columns: 1.1fr 0.9fr;
    gap: 36px;
    align-items: center;
    margin: 0 0 80px;
  }
  .feature.reverse { grid-template-columns: 0.9fr 1.1fr; }
  .feature.reverse figure { order: 2; }
  .feature figure {
    margin: 0;
    border: 1px solid var(--ink);
    box-shadow: 0 6px 26px rgba(58, 47, 29, 0.2);
    background: var(--parchment);
  }
  .feature img { display: block; width: 100%; height: auto; }
  .ftext h2 { font-family: var(--font-display); font-size: 1.9rem; margin: 0 0 0.3em; }
  .ftext p { font-size: 1.08rem; line-height: 1.65; color: #3a2f1d; }

  .campaign { margin: 0 0 40px; }
  .ch-head {
    font-family: var(--font-display);
    font-size: 1.6rem;
    border-bottom: 2px solid var(--ink);
    padding-bottom: 8px;
    margin: 0 0 28px;
  }
  .chapter { margin: 0 0 64px; }
  .chmap {
    margin: 0 0 16px;
    border: 1px solid var(--ink);
    box-shadow: 0 6px 24px rgba(58, 47, 29, 0.2);
    background: var(--parchment);
  }
  .chmap img { display: block; width: 100%; height: auto; }
  .chtext { max-width: 70ch; }
  .chapter h3 { font-family: var(--font-display); font-size: 1.45rem; margin: 0 0 0.2em; }
  .num { color: var(--blitz); margin-right: 0.3em; }
  .csub { font-style: italic; color: var(--blitz); margin: 0 0 0.5em; }
  .body { font-size: 1.05rem; line-height: 1.6; }
  .stats {
    list-style: none; padding: 0; margin: 1em 0 0;
    display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 10px;
  }
  .stats li { border-top: 2px solid var(--ink); padding-top: 6px; display: flex; flex-direction: column; }
  .stats .lab { font-size: 0.8rem; color: #6b5a2a; }
  .stats strong { font-size: 1.2rem; font-family: var(--font-display); }

  .cta {
    text-align: center; border: 2px solid var(--ink);
    background: rgba(215, 197, 151, 0.4); padding: 48px 28px; margin: 50px 0 60px;
  }
  .cta h2 { font-size: 2.1rem; font-family: var(--font-display); }
  .cta p { max-width: 54ch; margin: 0 auto 1.6em; font-size: 1.05rem; }
  .btn {
    display: inline-block; background: var(--ink); color: var(--parchment);
    text-decoration: none; font-family: var(--font-display); font-size: 1.15rem;
    padding: 14px 28px; border: 1px solid var(--ink); transition: background 150ms;
  }
  .btn:hover { background: var(--blitz); }
  footer { font-size: 0.8rem; color: #6b5a2a; text-align: center; border-top: 1px solid var(--parchment-dark); padding-top: 18px; }

  @media (max-width: 720px) {
    .feature, .feature.reverse { grid-template-columns: 1fr; gap: 18px; }
    .feature.reverse figure { order: 0; }
  }
</style>
