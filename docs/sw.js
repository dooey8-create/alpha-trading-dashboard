const C='ib-apps-v6';
const ASSETS=['./invoice.html','./Alpha_Sales.html',
'./assets/icon-180.png','./assets/icon-512.png','./assets/manifest.webmanifest',
'./assets/icon-sales-180.png','./assets/icon-sales-512.png','./assets/manifest_sales.webmanifest'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting()));});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==C).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',e=>{
  const isHTML=e.request.mode==='navigate'||(e.request.headers.get('accept')||'').includes('text/html');
  if(isHTML){
    // HTML: 네트워크 우선 + 브라우저 HTTP캐시 우회(no-store) → 오프라인이면 캐시
    e.respondWith(fetch(e.request,{cache:'no-store'}).then(resp=>{const cp=resp.clone();caches.open(C).then(c=>c.put(e.request,cp));return resp;})
      .catch(()=>caches.match(e.request).then(r=>r||caches.match(e.request.url.includes('Alpha_Sales')?'./Alpha_Sales.html':'./invoice.html'))));
  }else{
    // 아이콘 등 정적 파일: 캐시 우선
    e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request).then(resp=>{const cp=resp.clone();caches.open(C).then(c=>c.put(e.request,cp));return resp;})));
  }
});
