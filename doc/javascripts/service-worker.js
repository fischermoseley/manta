addEventListener('install', () => {
self.skipWaiting();
});
addEventListener('activate', () => {
self.clients.claim();
});

let resolver;
console.log("(Service Worker): Loaded!");

addEventListener('message', event => {
resolver(new Response(event.data,{status:200}));
console.log("(Service Worker): fufilling fetch, sending: ", event.data);
});

addEventListener('fetch', e => {
const u = new URL(e.request.url);
console.log("(Service Worker): Got fetch to: ", u);
if (u.pathname === '/read_serial/' || u.pathname === '/write_serial/') {
    e.respondWith(new Promise(r => resolver = r));
}
});

