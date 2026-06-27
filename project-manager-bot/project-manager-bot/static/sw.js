const CACHE_NAME = 'pm-ai-v2';
const STATIC_ASSETS = [
  '/',
  '/login-page',
  '/chat-page',
  '/static/manifest.json',
  'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
];

// Install: cache static assets
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      return cache.addAll(STATIC_ASSETS).catch(function(err) {
        console.log('Cache error:', err);
      });
    })
  );
  self.skipWaiting();
});

// Activate: clean old caches
self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(
        keys.filter(function(k) { return k !== CACHE_NAME; })
            .map(function(k) { return caches.delete(k); })
      );
    })
  );
  self.clients.claim();
});

// Fetch: network first, fallback to cache
self.addEventListener('fetch', function(event) {
  // Skip non-GET and API calls
  if (event.request.method !== 'GET') return;
  if (event.request.url.includes('/tasks') ||
      event.request.url.includes('/me') ||
      event.request.url.includes('/ws/') ||
      event.request.url.includes('/chat') ||
      event.request.url.includes('/briefing') ||
      event.request.url.includes('/horoscope')) return;

  event.respondWith(
    fetch(event.request)
      .then(function(response) {
        // Cache successful responses
        if (response.status === 200) {
          var clone = response.clone();
          caches.open(CACHE_NAME).then(function(cache) {
            cache.put(event.request, clone);
          });
        }
        return response;
      })
      .catch(function() {
        // Offline fallback
        return caches.match(event.request).then(function(cached) {
          if (cached) return cached;
          // Offline page for navigation
          if (event.request.mode === 'navigate') {
            return new Response(
              '<html><body style="font-family:Inter,sans-serif;text-align:center;padding:60px;background:#F0F4FF">' +
              '<h1 style="color:#1D4ED8">⚡ Project Manager AI</h1>' +
              '<p style="color:#666;margin-top:20px">You are offline. Please check your connection.</p>' +
              '<button onclick="location.reload()" style="margin-top:20px;background:#1D4ED8;color:white;border:none;padding:12px 24px;border-radius:10px;cursor:pointer;font-size:15px">Retry</button>' +
              '</body></html>',
              {headers: {'Content-Type': 'text/html'}}
            );
          }
        });
      })
  );
});

// Push notifications
self.addEventListener('push', function(event) {
  var data = event.data ? event.data.json() : {};
  var title = data.title || 'Project Manager AI';
  var options = {
    body: data.body || 'You have a new notification',
    icon: '/static/icons/icon-192.png',
    badge: '/static/icons/icon-192.png',
    vibrate: [200, 100, 200],
    data: { url: data.url || '/' }
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data.url || '/')
  );
});
