const CACHE_NAME = 'dawa-present-v1';
const OFFLINE_URL = '/offline.html';

// Files to cache for offline use
const STATIC_CACHE_URLS = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  '/favicon.ico',
  OFFLINE_URL
];

// API endpoints that can work offline
const OFFLINE_FALLBACK_PAGES = [
  '/',
  '/offline.html'
];

// Install event - cache static resources
self.addEventListener('install', (event) => {
  console.log('Service Worker installing...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Caching static resources');
        return cache.addAll(STATIC_CACHE_URLS);
      })
      .then(() => {
        // Force the waiting service worker to become the active service worker
        return self.skipWaiting();
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker activating...');
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      // Ensure the new service worker takes control immediately
      return self.clients.claim();
    })
  );
});

// Fetch event - serve cached content when offline
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Handle navigation requests
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .catch(() => {
          return caches.open(CACHE_NAME)
            .then((cache) => {
              return cache.match(OFFLINE_URL);
            });
        })
    );
    return;
  }

  // Handle API requests
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      handleApiRequest(request)
    );
    return;
  }

  // Handle static resources
  event.respondWith(
    caches.match(request)
      .then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }

        return fetch(request)
          .then((response) => {
            // Don't cache non-successful responses
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }

            // Clone the response
            const responseToCache = response.clone();

            caches.open(CACHE_NAME)
              .then((cache) => {
                cache.put(request, responseToCache);
              });

            return response;
          })
          .catch(() => {
            // Return offline fallback for failed requests
            if (request.destination === 'document') {
              return caches.match(OFFLINE_URL);
            }
          });
      })
  );
});

// Handle API requests with offline fallback
async function handleApiRequest(request) {
  const url = new URL(request.url);
  
  try {
    // Try to fetch from network first
    const response = await fetch(request);
    
    // Cache successful responses
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    console.log('Network request failed, trying cache:', url.pathname);
    
    // Try to get from cache
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return offline fallback for specific endpoints
    return handleOfflineApiRequest(url.pathname, request);
  }
}

// Handle specific API endpoints when offline
function handleOfflineApiRequest(pathname, request) {
  // Handle video generation offline
  if (pathname === '/api/generate-video' && request.method === 'POST') {
    return new Response(JSON.stringify({
      job_id: 'offline-' + Date.now(),
      status: 'queued',
      message: 'Video queued for generation when online',
      offline: true
    }), {
      status: 202,
      headers: { 'Content-Type': 'application/json' }
    });
  }
  
  // Handle voice upload offline
  if (pathname === '/api/upload-voice-sample' && request.method === 'POST') {
    return new Response(JSON.stringify({
      voice_id: 'offline-voice-' + Date.now(),
      status: 'queued',
      message: 'Voice sample queued for processing when online',
      offline: true
    }), {
      status: 202,
      headers: { 'Content-Type': 'application/json' }
    });
  }
  
  // Default offline response
  return new Response(JSON.stringify({
    error: 'This feature requires an internet connection',
    offline: true
  }), {
    status: 503,
    headers: { 'Content-Type': 'application/json' }
  });
}

// Background sync for queued operations
self.addEventListener('sync', (event) => {
  console.log('Background sync triggered:', event.tag);
  
  if (event.tag === 'video-generation') {
    event.waitUntil(processQueuedVideoGeneration());
  }
  
  if (event.tag === 'voice-upload') {
    event.waitUntil(processQueuedVoiceUploads());
  }
});

// Process queued video generation when back online
async function processQueuedVideoGeneration() {
  try {
    const queuedJobs = await getQueuedJobs('video-generation');
    
    for (const job of queuedJobs) {
      try {
        const response = await fetch('/api/generate-video', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(job.data)
        });
        
        if (response.ok) {
          await removeQueuedJob('video-generation', job.id);
          
          // Notify user that their video is ready
          self.registration.showNotification('Dawa Present', {
            body: 'Your video has been generated successfully!',
            icon: '/favicon.ico',
            badge: '/favicon.ico',
            tag: 'video-ready'
          });
        }
      } catch (error) {
        console.error('Failed to process queued video job:', error);
      }
    }
  } catch (error) {
    console.error('Error processing queued video generation:', error);
  }
}

// Process queued voice uploads when back online
async function processQueuedVoiceUploads() {
  try {
    const queuedUploads = await getQueuedJobs('voice-upload');
    
    for (const upload of queuedUploads) {
      try {
        const formData = new FormData();
        formData.append('voice_file', upload.data.file);
        
        const response = await fetch('/api/upload-voice-sample', {
          method: 'POST',
          body: formData
        });
        
        if (response.ok) {
          await removeQueuedJob('voice-upload', upload.id);
          
          // Notify user that their voice is ready
          self.registration.showNotification('Dawa Present', {
            body: 'Your voice sample has been processed successfully!',
            icon: '/favicon.ico',
            badge: '/favicon.ico',
            tag: 'voice-ready'
          });
        }
      } catch (error) {
        console.error('Failed to process queued voice upload:', error);
      }
    }
  } catch (error) {
    console.error('Error processing queued voice uploads:', error);
  }
}

// Helper functions for queue management
async function getQueuedJobs(type) {
  const cache = await caches.open(CACHE_NAME);
  const queueKey = `queue-${type}`;
  const response = await cache.match(queueKey);
  
  if (response) {
    return await response.json();
  }
  
  return [];
}

async function removeQueuedJob(type, jobId) {
  const jobs = await getQueuedJobs(type);
  const updatedJobs = jobs.filter(job => job.id !== jobId);
  
  const cache = await caches.open(CACHE_NAME);
  const queueKey = `queue-${type}`;
  
  await cache.put(queueKey, new Response(JSON.stringify(updatedJobs), {
    headers: { 'Content-Type': 'application/json' }
  }));
}

// Handle push notifications
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : 'New update available!',
    icon: '/favicon.ico',
    badge: '/favicon.ico',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'Open App',
        icon: '/favicon.ico'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/favicon.ico'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification('Dawa Present', options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

