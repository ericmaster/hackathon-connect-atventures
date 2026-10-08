// Offline shell. Based on https://svelte.dev/docs/kit/service-workers
import { self } from '$app/service-worker';
import { version } from '$app/env';
import { immutable, assets } from '$app/manifest';
import { resolve } from '$app/paths';

const CACHE = `cache-${version}`;
const SHELL = resolve('/');
const ASSETS = [...immutable.map((a) => resolve(a.path)), ...assets.map((a) => resolve(a.path))];

self.addEventListener('install', (event) => {
	event.waitUntil(caches.open(CACHE).then((c) => c.addAll([SHELL, ...ASSETS])).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (event) => {
	event.waitUntil(
		caches
			.keys()
			.then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
			.then(() => self.clients.claim())
	);
});

self.addEventListener('fetch', (event) => {
	if (event.request.method !== 'GET') return;
	const url = new URL(event.request.url);
	if (url.origin !== self.location.origin) return;

	event.respondWith(
		(async () => {
			const cache = await caches.open(CACHE);
			if (ASSETS.includes(url.pathname)) {
				const hit = await cache.match(url.pathname);
				if (hit) return hit;
			}
			try {
				return await fetch(event.request);
			} catch (err) {
				// SPA: any offline navigation gets the cached shell
				const hit = event.request.mode === 'navigate' ? await cache.match(SHELL) : await cache.match(event.request);
				if (hit) return hit;
				throw err;
			}
		})()
	);
});
