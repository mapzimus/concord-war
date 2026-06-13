import { describe, it, expect, beforeEach } from 'vitest';
import { get } from 'svelte/store';
import {
  currentChapterId,
  visibleLayers,
  setChapter,
  toggleLayer,
  applyChapterLayers
} from '../src/lib/data/stores.js';

describe('stores', () => {
  beforeEach(() => {
    setChapter('intro');
    visibleLayers.set(new Set());
  });

  it('setChapter updates currentChapterId', () => {
    setChapter('explorer');
    expect(get(currentChapterId)).toBe('explorer');
  });

  it('toggleLayer adds and removes a layer id', () => {
    toggleLayer('river');
    expect(get(visibleLayers).has('river')).toBe(true);
    toggleLayer('river');
    expect(get(visibleLayers).has('river')).toBe(false);
  });

  it('applyChapterLayers replaces visible layers with the chapter set', () => {
    visibleLayers.set(new Set(['was-there-before']));
    applyChapterLayers(['city', 'river', 'front_line']);
    const v = get(visibleLayers);
    expect(v.has('was-there-before')).toBe(false);
    expect(v.has('city')).toBe(true);
    expect(v.has('river')).toBe(true);
    expect(v.has('front_line')).toBe(true);
  });
});
