import { writable } from 'svelte/store';

/** @type {import('svelte/store').Writable<string>} */
export const currentChapterId = writable('intro');

/** @type {import('svelte/store').Writable<Set<string>>} */
export const visibleLayers = writable(new Set());

/** @param {string} id */
export function setChapter(id) {
  currentChapterId.set(id);
}

/** @param {string} layerId */
export function toggleLayer(layerId) {
  visibleLayers.update((s) => {
    const next = new Set(s);
    if (next.has(layerId)) next.delete(layerId);
    else next.add(layerId);
    return next;
  });
}

/** @param {string[]} ids */
export function applyChapterLayers(ids) {
  visibleLayers.set(new Set(ids));
}
