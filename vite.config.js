import adapter from '@sveltejs/adapter-static';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vitest/config';

// The sveltekit() plugin targets Vite 8's environments API; vitest 2.x bundles
// Vite 5.4 which doesn't have it, so we skip the plugin under VITEST.
const isVitest = !!process.env.VITEST;

export default defineConfig({
	plugins: isVitest
		? []
		: [
				sveltekit({
					compilerOptions: {
						// Force runes mode for the project, except for libraries. Can be removed in svelte 6.
						runes: ({ filename }) =>
							filename.split(/[/\\]/).includes('node_modules') ? undefined : true
					},
					adapter: adapter({
						pages: 'build',
						assets: 'build',
						fallback: 'index.html',
						precompress: false,
						strict: true
					}),
					paths: {
						base: process.env.BASE_PATH ?? ''
					},
					prerender: {
						handleHttpError: 'warn'
					}
				})
			],
	test: {
		include: ['tests/**/*.{test,spec}.{js,ts}'],
		environment: 'jsdom'
	}
});
