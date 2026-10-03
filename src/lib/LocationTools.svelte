<script>
  import { onDestroy, createEventDispatcher } from 'svelte';
  import RequestFeedback from './RequestFeedback.svelte';
  import { MVT_TILES } from './config.js';
  export let mapView;
  export let selected = null;
  let query = '';
  let city = '';
  let mode = 'car';
  const modes = { car: 'Mobil', bike: 'Sepeda', foot: 'Jalan kaki' };
  let states = {};
  let activeRequest = '';
  let cancelled = false;
  const categories = { hospital: 'Rumah sakit & klinik', pharmacy: 'Apotek', education: 'Sekolah & kampus', worship: 'Tempat ibadah', market: 'Pasar', shop: 'Supermarket & minimarket', food: 'Restoran & kafe', fuel: 'SPBU', bank: 'Bank & ATM', hotel: 'Hotel & penginapan', transport: 'Terminal & stasiun', parking: 'Parkir', police: 'Kantor polisi', warehouse: 'Gudang', port: 'Pelabuhan' };
  let results = [];
  let facilities = [];
  let company = [];
  let kind = 'hospital';
  let radius = 2000;
  let busy = false;
  let message = '';
  let origin = null;
  let destination = null;
  let routeResult = null;
  let controller;
  const dispatch = createEventDispatcher();
  let choosing = null;
  let selectionAtStart;
  $: if (choosing && selected && selected !== selectionAtStart && !busy) setEndpoint(choosing);
  $: sameLocation = origin && destination && origin.lng === destination.lng && origin.lat === destination.lat;
  onDestroy(() => controller?.abort());

  async function request(path, params = {}) {
    const url = new URL(path, MVT_TILES);
    url.search = new URLSearchParams(params);
    controller = new AbortController();
    const current = controller;
    const timer = setTimeout(() => current.abort(), 60000);
    try {
      const response = await fetch(url, { signal: controller.signal });
      let data;
      try { data = await response.json(); } catch { throw new Error('Respons server tidak valid. Pastikan server Python terbaru berjalan.'); }
      if (!response.ok) throw new Error(data.error || 'Permintaan gagal');
      return data;
    } finally { clearTimeout(timer); }
  }
  function cancelRequest() { cancelled = true; controller?.abort(); }
  async function run(action) {
    if (busy) return;
    const key = action.name;
    activeRequest = key; cancelled = false;
    states = { ...states, [key]: { status: 'loading' } };
    busy = true; message = '';
    try {
      await action();
      states = { ...states, [key]: { status: 'success', message } };
    } catch (error) {
      const text = cancelled ? 'Pencarian dibatalkan. Anda dapat mencoba lagi.' : error.name === 'AbortError'
        ? 'Layanan terlalu lama merespons. Coba lagi atau perkecil area pencarian.'
        : error instanceof TypeError ? 'Server tidak terhubung. Periksa koneksi dan pastikan server Python berjalan.' : error.message;
      states = { ...states, [key]: { status: cancelled ? 'idle' : 'error', message: text } };
    } finally { busy = false; activeRequest = ''; }
  }
  function choose(item) {
    selected = { lng: item.geometry.coordinates[0], lat: item.geometry.coordinates[1], name: item.properties.name };
    mapView.focusSupplier(item);
    mapView.showOverlay('selection', { type: 'FeatureCollection', features: [item] });
    mapView.showPlacePopup(item);
  }
  function setEndpoint(which) {
    if (!selected || busy) return;
    if (which === 'origin') origin = { ...selected };
    else destination = { ...selected };
    choosing = null;
    dispatch('routePick', null);
    mapView.setRouteEndpoints(origin, destination);
    message = which === 'origin' ? 'Asal ditetapkan. Selanjutnya pilih tujuan.' : 'Tujuan ditetapkan. Tekan Hitung rute.';
    clearRoute();
  }
  function beginPick(which) {
    choosing = which;
    selectionAtStart = selected;
    message = `Klik ${which === 'origin' ? 'asal (A)' : 'tujuan (B)'} di peta, atau pilih hasil pencarian.`;
    dispatch('routePick', which);
  }
  function swapEndpoints() {
    [origin, destination] = [destination, origin];
    mapView.setRouteEndpoints(origin, destination);
    clearRoute();
  }
  function resetRoute() {
    origin = null; destination = null; choosing = null;
    dispatch('routePick', null);
    mapView.setRouteEndpoints(null, null);
    clearRoute(); message = 'Rute direset. Pilih asal baru.';
  }
  function clearRoute() {
    routeResult = null;
    states = { ...states, routing: { status: 'idle' } };
    mapView.closeDetails();
    mapView.showOverlay('route', { type: 'FeatureCollection', features: [] });
  }
  async function search() {
    results = [];
    mapView.showOverlay('search', { type: 'FeatureCollection', features: [] });
    const data = await request('/api/search', { q: [query.trim(), city.trim()].filter(Boolean).join(', ') });
    results = data.features;
    mapView.showOverlay('search', data);
    message = results.length ? `${results.length} hasil ditemukan.${data.approximate ? ' Hasil pendekatan nama; periksa alamat sebelum memilih.' : ' Pilih kartu untuk melihat detail.'}` : 'Belum ada hasil. Coba nama lebih pendek (misalnya Amana), ejaan lain (Amanah), atau tambahkan kota. Tempat mungkin belum tercatat di OpenStreetMap.';
  }
  async function nearby() {
    facilities = [];
    mapView.showOverlay('places', { type: 'FeatureCollection', features: [] });
    const data = await request('/api/places', { lng: selected.lng, lat: selected.lat, radius, kind });
    facilities = data.features;
    mapView.showOverlay('places', data);
    message = facilities.length ? `${facilities.length} fasilitas ditemukan, diurutkan menurut jarak (maksimal 200).` : 'Belum ada fasilitas di radius ini. Coba radius lebih besar, kategori lain, atau pusat lokasi lain. Cakupan mengikuti OpenStreetMap.';
  }
  async function routing() {
    if (!origin || !destination || sameLocation) throw new Error('Pilih asal dan tujuan yang berbeda.');
    choosing = null;
    dispatch('routePick', null);
    clearRoute();
    states = { ...states, routing: { status: 'loading' } };
    const data = await request('/api/route', { fromLng: origin.lng, fromLat: origin.lat, toLng: destination.lng, toLat: destination.lat, mode });
    routeResult = { ...data.properties, mode };
    data.properties.modeLabel = modes[mode];
    message = 'Rute ditemukan. Garis biru mengikuti jaringan jalan.';
    mapView.showOverlay('route', { type: 'FeatureCollection', features: [data] }, true);
    mapView.showRoutePopup(data, modes[mode]);
  }
  async function loadCompany() {
    const data = await request('/api/company-locations');
    company = data.features;
    mapView.showOverlay('company', data, true);
    message = `${company.length} lokasi perusahaan dimuat.`;
  }
  const label = p => p ? (p.name || `${p.lat.toFixed(5)}, ${p.lng.toFixed(5)}`) : 'Belum dipilih';
</script>

<section aria-label="Pencarian dan perjalanan">
  <h2>Lokasi & perjalanan</h2>
  <form on:submit|preventDefault={() => run(search)}>
    <label for="place-query">Cari alamat atau tempat</label>
    <input disabled={busy} id="place-query" bind:value={query} required minlength="2" maxlength="200" placeholder="Contoh: Bandung" />
    <label for="search-city">Kota / wilayah <small>(opsional)</small></label><input disabled={busy} id="search-city" bind:value={city} maxlength="100" placeholder="Contoh: Tasikmalaya" />
    <button class="primary" disabled={busy || !mapView}>{activeRequest === 'search' ? 'Mencari tempat…' : 'Cari tempat'}</button>
  </form>
  <RequestFeedback state={states.search} title="Mencari nama dan alamat…" retry={() => run(search)} cancel={cancelRequest} />
  <div class="results">{#each results as item}<button disabled={busy} on:click={() => choose(item)}><strong>{item.properties.name}</strong>{#if item.properties.address}<small>{item.properties.address}</small>{/if}{#if item.properties.distance !== undefined}<small>{(item.properties.distance / 1000).toFixed(1)} km dari pusat pencarian</small>{/if}</button>{/each}</div>
  <p class="selected">Lokasi pilihan: <strong>{label(selected)}</strong></p>
  <p>Klik peta, supplier, atau hasil pencarian untuk memilih lokasi. GPS juga dapat digunakan.</p>
  <details>
    <summary>Fasilitas sekitar</summary>
    <label for="poi-kind">Jenis fasilitas</label>
    <select disabled={busy} id="poi-kind" bind:value={kind}>{#each Object.entries(categories) as [value, name]}<option {value}>{name}</option>{/each}</select>
    <label for="poi-radius">Radius</label>
    <select disabled={busy} id="poi-radius" bind:value={radius}><option value={1000}>1 km</option><option value={2000}>2 km</option><option value={5000}>5 km</option><option value={10000}>10 km</option></select>
    {#if !selected}<p class="tip">Pilih titik pusat di peta atau cari tempat terlebih dahulu.</p>{/if}
    <button class="primary" disabled={busy || !selected} on:click={() => run(nearby)}>{activeRequest === 'nearby' ? 'Mencari fasilitas…' : 'Cari fasilitas'}</button>
    <RequestFeedback state={states.nearby} title="Mencari fasilitas di sekitar lokasi…" retry={() => run(nearby)} cancel={cancelRequest} />
    <button disabled={busy} on:click={() => { facilities = []; mapView.showOverlay('places', { type: 'FeatureCollection', features: [] }); }}>Hapus fasilitas</button>
    <div class="results">{#each facilities as item}<button disabled={busy} on:click={() => choose(item)}><strong>{item.properties.name}</strong>{#if item.properties.address}<small>{item.properties.address}</small>{/if}{#if item.properties.distance !== undefined}<small>{(item.properties.distance / 1000).toFixed(1)} km dari pusat pencarian</small>{/if}</button>{/each}</div>
  </details>
  <details open>
    <summary>Rute perjalanan</summary>
    <label for="travel-mode">Moda perjalanan</label>
    <select disabled={busy} id="travel-mode" bind:value={mode} on:change={clearRoute}>{#each Object.entries(modes) as [value, name]}<option {value}>{name}</option>{/each}</select>
    <p>1. Pilih asal · 2. Pilih tujuan · 3. Hitung rute</p>
    <div class="endpoint"><strong>A · Asal</strong><p>{label(origin)}</p>
      <button disabled={busy || !mapView} aria-pressed={choosing === 'origin'} on:click={() => beginPick('origin')}>Pilih asal di peta</button>
      <button disabled={busy || !selected} on:click={() => setEndpoint('origin')}>Gunakan lokasi pilihan sebagai asal</button>
    </div>
    <div class="endpoint"><strong>B · Tujuan</strong><p>{label(destination)}</p>
      <button disabled={busy || !mapView} aria-pressed={choosing === 'destination'} on:click={() => beginPick('destination')}>Pilih tujuan di peta</button>
      <button disabled={busy || !selected} on:click={() => setEndpoint('destination')}>Gunakan lokasi pilihan sebagai tujuan</button>
    </div>
    {#if choosing}<p role="status">Sedang memilih {choosing === 'origin' ? 'asal A' : 'tujuan B'}. Klik peta atau pilih hasil pencarian.</p><button on:click={() => { choosing = null; dispatch('routePick', null); }}>Batal memilih</button>{/if}
    {#if sameLocation}<p role="alert">Asal dan tujuan sama. Pilih lokasi tujuan yang berbeda.</p>{/if}
    <button disabled={busy || !origin || !destination || sameLocation} on:click={() => run(routing)}>{activeRequest === 'routing' ? 'Menghitung rute…' : 'Hitung rute'}</button>
    <RequestFeedback state={states.routing} title="Menghitung jalur dan estimasi waktu…" retry={() => run(routing)} cancel={cancelRequest} />
    <button disabled={busy || !origin || !destination} on:click={swapEndpoints}>Tukar asal & tujuan</button>
    <button disabled={busy || !mapView} on:click={resetRoute}>Reset rute</button>
    {#if routeResult}<p class="route-result" role="status"><strong>{(routeResult.distance / 1000).toFixed(1)} km · {Math.ceil(routeResult.duration / 60)} menit</strong><br />Estimasi {modes[routeResult.mode].toLowerCase()}</p>{/if}
    <p>Rute dimulai dari jalur terdekat yang sesuai moda pilihan. Tidak memperhitungkan kemacetan langsung atau pembatasan khusus truk.</p>
  </details>
  <details>
    <summary>Lokasi perusahaan</summary>
    <button disabled={busy || !mapView} on:click={() => run(loadCompany)}>Muat dari API perusahaan</button>
    <button disabled={busy} on:click={() => { company = []; mapView.showOverlay('company', { type: 'FeatureCollection', features: [] }); }}>Sembunyikan lokasi</button>
    <RequestFeedback state={states.loadCompany} title="Memuat lokasi perusahaan…" retry={() => run(loadCompany)} cancel={cancelRequest} />
    <div class="results">{#each company as item}<button disabled={busy} on:click={() => choose(item)}>{item.properties.name} · {item.properties.kind}</button>{/each}</div>
  </details>
  <p role="status" aria-live="polite">{choosing ? message : ''}</p>
  <p>Alamat dan koordinat pencarian dikirim ke layanan lokasi. <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">© OpenStreetMap contributors</a> · Photon · OSRM / FOSSGIS · <a href="https://www.openstreetmap.org/fixthemap" target="_blank" rel="noreferrer">Perbaiki data peta</a></p>
</section>
<style>
  .primary { background: #166348; color: white; border-color: #166348; }
  .results strong { display: block; font-size: 12px; line-height: 1.5; }
  .results small { display: block; color: #617569; margin-top: 5px; line-height: 1.4; }
  .tip { padding: 10px; border-radius: 8px; background: #fff5e4; }
  .endpoint { border-left: 3px solid #166348; padding: 10px; margin: 12px 0; background: white; border-radius: 6px; }
  .endpoint strong { font-size: 13px; }
  button[aria-pressed="true"], .route-result { background: #e5f1e8; color: #14532d; }
  .route-result { padding: 14px; border-radius: 8px; }
  section { margin: 0 24px 24px; padding: 16px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; }
  h2 { font-size: 17px; margin: 0 0 16px; color: #164c38; }
  label, summary { font-weight: 600; font-size: 13px; }
  label { display: block; margin-top: 10px; }
  input, select, button { width: 100%; box-sizing: border-box; font: inherit; font-size: 13px; padding: 10px; border: 1px solid #cbd5e0; border-radius: 7px; margin-top: 7px; background: white; }
  button, summary { cursor: pointer; } button { color: #14532d; } button:disabled { opacity: .5; cursor: not-allowed; }
  p { font-size: 12px; line-height: 1.5; overflow-wrap: anywhere; color: #475569; }
  details { border-top: 1px solid #e2e8f0; padding: 12px 0; }
  .results { max-height: 180px; overflow-y: auto; } .results button { text-align: left; }
  .selected { border-left: 3px solid #0f6f4a; padding-left: 8px; }
  :focus-visible { outline: 2px solid #0f6f4a; outline-offset: 2px; }
</style>
