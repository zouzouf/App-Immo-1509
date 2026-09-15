self.addEventListener('fetch', function(event) {
    // Permet le fonctionnement PWA basique
    event.respondWith(fetch(event.request));
});
