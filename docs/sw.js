// JARVIS Service Worker - Offline Support
const CACHE_NAME = 'jarvis-v4.4.0';
const ASSETS = [
    './',
    './index.html',
    './styles.css',
    './components.css',
    './jarvis.js',
    './api.html'
];

self.addEventListener('install', e => {
    e.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(ASSETS))
            .then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', e => {
    e.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
        ).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', e => {
    e.respondWith(
        caches.match(e.request)
            .then(cached => cached || fetch(e.request)
                .then(res => {
                    if (res.ok && e.request.method === 'GET') {
                        const clone = res.clone();
                        caches.open(CACHE_NAME).then(cache => cache.put(e.request, clone));
                    }
                    return res;
                })
            )
            .catch(() => caches.match('./index.html'))
    );
});
