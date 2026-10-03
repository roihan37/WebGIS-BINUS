<script>
  import { onMount, onDestroy } from 'svelte';
  import { MVT_TILES } from './lib/config.js';
  import LocationTools from './lib/LocationTools.svelte';
  let selectedLocation = null;
  let activeTab = 'map';
  let panelOpen = true;
  let routePick = null;
  import MapView from './lib/MapView.svelte';

  const supplierApi = new URL('/api/suppliers', MVT_TILES).href;
  let adding = false;
  let saving = false;
  let location = null;
  let supplierName = '';
  let region = '';
  let area = '';
  let formError = '';
  let suppliers = { type: 'FeatureCollection', features: [] };

  let geocoding = false;
  let addressNote = '';
  let lookupVersion = 0;
  let regionRevision = 0;
  let lookupController;

  function stopLookup() {
    lookupVersion += 1;
    lookupController?.abort();
    geocoding = false;
    addressNote = '';
  }
  onDestroy(stopLookup);

  async function selectLocation(point, gps = false) {
    if (saving) return;
    if (gps && !adding) startAdding();
    stopLookup();
    location = point;
    mapView.markLocation(point);
    const version = lookupVersion;
    const revision = regionRevision;
    geocoding = true;
    lookupController = new AbortController();
    const controller = lookupController;
    const timer = setTimeout(() => controller.abort(), 15000);
    try {
      const url = new URL('/api/reverse-geocode', supplierApi);
      url.search = new URLSearchParams({ lat: point.lat, lng: point.lng });
      const response = await fetch(url, { signal: lookupController.signal });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Alamat tidak ditemukan');
      if (version !== lookupVersion || !adding) return;
      if (revision === regionRevision) region = data.region;
      addressNote = data.address || data.region;
    } catch (error) {
      if (version === lookupVersion) addressNote = 'Alamat belum tersedia. Isi wilayah secara manual atau coba lagi.';
    } finally {
      clearTimeout(timer);
      if (version === lookupVersion) geocoding = false;
    }
  }

  onMount(() => {
    fetch(supplierApi).then(async response => {
      if (!response.ok) throw new Error();
      const data = await response.json();
      // Merge with any supplier saved while this request was pending.
      const features = new Map([...data.features, ...suppliers.features].map(f => [f.id, f]));
      suppliers = { type: 'FeatureCollection', features: [...features.values()] };
      mapView.updateSuppliers(suppliers);
    }).catch(() => formError = 'Supplier tersimpan belum dapat dimuat. Pastikan server Python versi terbaru berjalan, lalu muat ulang halaman.');
  });

  function startAdding() {
    if (isBufferActive) handleBufferAction();
    stopLookup();
    activeTab = 'supplier';
    panelOpen = true;
    adding = true;
    location = null;
    formError = '';
    status = 'Klik peta untuk memilih lokasi supplier';
  }

  function cancelAdding() {
    stopLookup();
    adding = false;
    location = null;
    supplierName = ''; region = ''; area = '';
    mapView.finishPicking();
  }

  async function saveSupplier() {
    if (saving || geocoding) return;
    if (!location || !supplierName.trim() || !region.trim() || area === '' || !Number.isFinite(Number(area)) || Number(area) < 0) {
      formError = 'Pilih lokasi dan isi nama, wilayah, serta luas lahan yang valid.';
      return;
    }
    saving = true;
    formError = '';
    try {
      const response = await fetch(supplierApi, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...location, entityname: supplierName.trim(), regionlabel: region.trim(), plotareaha: Number(area) })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Gagal menyimpan');
      suppliers = { type: 'FeatureCollection', features: [...suppliers.features, data] };
      mapView.updateSuppliers(suppliers);
      minArea = 0;
      mapView.applyFilter(0);
      layerVisible = true;
      mapView.toggleLayer(true);
      setMode('mvt');
      mapView.focusSupplier(data);
      cancelAdding();
      status = 'Supplier berhasil disimpan. Filter luas direset agar titik terlihat.';
    } catch (error) {
      formError = 'Gagal menyimpan. Pastikan server Python berjalan. ' + error.message;
    } finally { saving = false; }
  }

  let basemap = import.meta.env.VITE_MAPID_KEY ? 'street' : 'demo';
  let mapView;
  let status = 'Siap menjelajah';
  let layerVisible = true;
  let isMvtLoaded = false;
  let currentMode = 'mvt';
  let minArea = 0;
  
  // Buffer State
  let bufferRadius = 10;
  let isBufferActive = false;
  let bufferCenter;

  function useMvt() {
    mapView.setLayerMode(currentMode);
    status = 'Layer supplier diaktifkan';
    isMvtLoaded = true;
  }

  function togglePoints(event) {
    layerVisible = event.currentTarget.checked;
    mapView.toggleLayer(layerVisible);
  }

  function setMode(mode) {
    currentMode = mode;
    mapView.setLayerMode(mode);
    isMvtLoaded = true;
  }

  function handleFilterChange(event) {
    minArea = Number(event.currentTarget.value);
    mapView.applyFilter(minArea);
  }

  function handleBufferAction() {
    if (isBufferActive) {
      mapView.clearBuffer();
      bufferCenter = null;
      isBufferActive = false;
      status = 'Buffer dihapus';
    } else {
      setMode('mvt');
      layerVisible = true;
      mapView.toggleLayer(true);
      isBufferActive = true;
      status = 'Klik supplier untuk menentukan pusat buffer';
    }
  }

  // INI ADALAH FUNGSI KRUSIAL YANG MENANGKAP EVENT DARI MAPVIEW
  function onSupplierSelected(event) {
    const lngLat = event.detail; // Data koordinat dikirim lewat event.detail
    if (isBufferActive) {
      bufferCenter = lngLat;
      mapView.createBuffer(bufferCenter, bufferRadius);
    }
  }

  function updateRadius(event) {
    bufferRadius = Number(event.currentTarget.value);
    if (isBufferActive && bufferCenter) mapView.createBuffer(bufferCenter, bufferRadius);
  }

  const options = [
    { id: 'street', label: 'Street 2D', icon: '🏙️' },
    { id: 'light', label: 'Light Mode', icon: '☀️' },
    { id: 'satellite', label: 'Satellite', icon: '🛰️' },
    { id: 'demo', label: 'Demo Fallback', icon: '🌐' }
  ];
</script>

<div class="app-container">
  <header class="workspace-header">
    <div class="identity"><span class="brand-icon" aria-hidden="true">S</span><div><strong>Supplier Atlas</strong><small>Workspace pemetaan & distribusi</small></div></div>
    <div class="header-actions"><span class="workspace-label">MAPID × BINUS</span><button class="secondary-btn panel-toggle" aria-expanded={panelOpen} aria-controls="workspace-sidebar" on:click={() => panelOpen = !panelOpen}>{panelOpen ? 'Tutup panel' : 'Buka panel'}</button><button class="primary-btn" disabled={saving} on:click={startAdding}>+ Tambah supplier</button></div>
  </header>
  <aside id="workspace-sidebar" class="sidebar" class:panel-hidden={!panelOpen}>
    <div class="panel-heading"><span class="eyebrow">RUANG KERJA</span><h1>Jelajahi jaringan Anda</h1><p>Temukan lokasi. Pahami jangkauan.</p></div>
    <nav class="panel-tabs" aria-label="Menu workspace">
      {#each [{ id: 'map', label: 'Peta' }, { id: 'tools', label: 'Analisis' }, { id: 'supplier', label: 'Supplier' }] as tab}
        <button aria-pressed={activeTab === tab.id} class:chosen={activeTab === tab.id} on:click={() => activeTab = tab.id}>{tab.label}</button>
      {/each}
    </nav>
    <div class="sidebar-content">
      <div class="tab-panel" hidden={activeTab !== 'map'}>
      <div class="main-action">
        <button class="primary-btn" on:click={useMvt} class:active={isMvtLoaded}>
          
          {isMvtLoaded ? 'Layer supplier diaktifkan' : 'Tampilkan data supplier'}
        </button>
      </div>

      </div>
      <div class="tab-panel" hidden={activeTab !== 'tools'}><LocationTools on:routePick={event => { routePick = event.detail; if (routePick) { if (adding) cancelAdding(); if (window.innerWidth <= 760) panelOpen = false; } else if (activeTab === 'tools') panelOpen = true; }} {mapView} bind:selected={selectedLocation} /></div>
      <div class="tab-panel" hidden={activeTab !== 'supplier'}>
      <div class="section-intro"><h2>Data supplier</h2><p>{suppliers.features.length} lokasi tersimpan melalui aplikasi ini. Data MVT tidak termasuk hitungan ini.</p></div>
      <section class="supplier-form menu-section" aria-label="Tambah supplier">
        {#if !adding}
          <button class="secondary-btn" on:click={startAdding}>+ Tambah Supplier</button>
        {:else}
          <h2>Tambah Supplier</h2>
          <button class="secondary-btn" disabled={saving} on:click={() => mapView.locateMe()}>Lokasi Saya</button>
          <p>Lokasi dikirim ke OpenStreetMap untuk mencari alamat. Periksa wilayah sebelum menyimpan.</p>
          <p role="status">{geocoding ? 'Mencari alamat…' : addressNote}</p>
          {#if location && !geocoding}<button class="secondary-btn" disabled={saving} on:click={() => selectLocation(location)}>Cari alamat lagi</button>{/if}
          <p><a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">© OpenStreetMap contributors</a></p>
          <p>Klik peta untuk memilih lokasi. Klik lagi untuk memindahkannya.</p><button class="secondary-btn" on:click={() => panelOpen = false}>Buka peta untuk memilih titik</button>
          <p role="status">{location ? `${location.lat.toFixed(5)}, ${location.lng.toFixed(5)}` : 'Belum ada lokasi dipilih'}</p>
          <form on:submit|preventDefault={saveSupplier}>
            <fieldset disabled={saving}>
              <label for="supplier-name">Nama supplier</label>
              <input id="supplier-name" bind:value={supplierName} required maxlength="200" />
              <label for="supplier-region">Wilayah</label>
              <input id="supplier-region" on:input={() => regionRevision += 1} bind:value={region} required maxlength="200" />
              <label for="supplier-area">Luas lahan (ha)</label>
              <input id="supplier-area" type="number" min="0" max="1000000000" step="any" bind:value={area} required />
              <button class="primary-btn" type="submit" disabled={!location || saving || geocoding}>{saving ? 'Menyimpan…' : 'Simpan Supplier'}</button>
              <button class="secondary-btn" type="button" on:click={cancelAdding}>Batal</button>
            </fieldset>
          </form>
        {/if}
        {#if formError}<p class="form-error" role="alert">{formError}</p>{/if}
      </section>

      {#if !adding}
        <div class="saved-list">
          {#each suppliers.features as item}
            <button on:click={() => { mapView.focusSupplier(item); selectedLocation = { lng: item.geometry.coordinates[0], lat: item.geometry.coordinates[1], name: item.properties.entityname }; }}><strong>{item.properties.entityname}</strong><span>{item.properties.regionlabel} · {item.properties.plotareaha} ha</span></button>
          {:else}<p>Belum ada supplier baru. Pilih “Tambah supplier” untuk mulai mencatat lokasi.</p>{/each}
        </div>
      {/if}
      </div>
      <div class="tab-panel" hidden={activeTab !== 'map'}>
      <div class="menu-section">
        <div class="section-title">Tampilan peta</div>
        
        <div class="control-card">
          <label for="basemap">Peta dasar</label>
          <div class="select-wrapper">
            <select id="basemap" bind:value={basemap}>
              {#each options as option}
                <option value={option.id}>{option.label}</option>
              {/each}
            </select>
          </div>
        </div>

        <div class="control-card">
          <div class="toggle-row">
            <div class="toggle-info">
              <span class="toggle-title">Lokasi supplier</span>
              <span class="toggle-subtitle">Tampilkan layer supplier</span>
            </div>
            <label class="ios-switch">
              <input aria-label="Show supplier layer" type="checkbox" checked={layerVisible} on:change={togglePoints}>
              <span class="slider"></span>
            </label>
          </div>
        </div>
      </div>

      <div class="menu-section">
        <div class="section-title">Visualisasi</div>
        <div class="mode-selector">
          <button class="mode-btn" aria-pressed={currentMode === 'mvt'} class:active={currentMode === 'mvt'} on:click={() => setMode('mvt')}>
            Titik
          </button>
          <button class="mode-btn" aria-pressed={currentMode === 'heatmap'} class:active={currentMode === 'heatmap'} on:click={() => setMode('heatmap')}>
            Kepadatan
          </button>
        </div>
      </div>

      <div class="menu-section">
        <div class="section-title">Filter luas lahan</div>
        <div class="control-card">
          <div class="filter-header">
            <label for="min-area">Luas minimum</label>
            <span class="filter-value">{minArea} ha</span>
          </div>
          <input id="min-area" type="range" min="0" max="100" step="1" bind:value={minArea} on:input={handleFilterChange} class="range-slider">
          <div class="range-labels">
            <span>0 ha</span>
            <span>100 ha</span>
          </div>
        </div>
      </div>

      <div class="menu-section">
        <div class="section-title">Analisis jangkauan</div>
        <div class="control-card">
          <div class="buffer-header">
            <label for="buffer-radius">Radius jangkauan</label>
            <span class="filter-value">{bufferRadius} km</span>
          </div>
          <input id="buffer-radius" on:input={updateRadius} type="range" min="1" max="50" step="1" bind:value={bufferRadius} class="range-slider">
          <div class="range-labels">
            <span>1 km</span>
            <span>50 km</span>
          </div>
          <button class="secondary-btn" on:click={handleBufferAction} class:active={isBufferActive}>
            {isBufferActive ? 'Hapus buffer' : 'Pilih pusat buffer'}
          </button>
        </div>
      </div>

      </div>
    </div>
      <footer class="sidebar-footer">
        <div role="status" aria-live="polite" class="status-pill" class:loaded={isMvtLoaded}>
          <span class="dot"></span>
          {status}
        </div>
        <p class="footer-note">Klik titik untuk melihat detail supplier</p>
      </footer>
  </aside>

  <main class="map-viewport">
    <!-- PERBAIKAN: Menambahkan listener on:supplierClick -->
    <MapView routePicking={!!routePick} picking={adding && !saving} on:pointSelected={event => selectedLocation = event.detail} on:gpsLocated={event => { selectedLocation = event.detail; if (adding) selectLocation(event.detail, true); }} on:locationPicked={event => { selectLocation(event.detail); panelOpen = true; }} bind:this={mapView} {basemap} on:mapError={() => status = 'Peta atau data gagal dimuat. Periksa koneksi dan server data.'} on:supplierClick={onSupplierSelected} />
    <div class="map-guide">{routePick ? `Klik ${routePick === 'origin' ? 'asal A' : 'tujuan B'} untuk rute` : adding ? 'Pilih lokasi supplier di peta atau gunakan GPS' : isBufferActive ? 'Klik supplier untuk menggambar radius jangkauan' : 'Geser peta untuk menjelajah · klik titik untuk detail'}</div>
    <div class="map-legend"><strong>{currentMode === 'heatmap' ? 'Kepadatan relatif supplier' : 'Legenda lokasi'}</strong>
      {#if currentMode === 'heatmap'}<div class="density-bar"></div><span>Rendah ↔ Tinggi · berubah mengikuti zoom</span>
      {:else}<span><i class="green"></i> Supplier <i class="orange"></i> Hasil pencarian <i class="purple"></i> Perusahaan</span>{/if}
      {#if !layerVisible}<span>Layer supplier disembunyikan</span>{/if}
    </div>
    <div class="map-overlay">
      <div class="overlay-card">
        <strong>MODE PETA</strong>
        <span class="value">{currentMode === 'mvt' ? 'Titik supplier' : 'Kepadatan'}</span>
      </div>
    </div>
  </main>
</div>

<style>
  :global(body) { font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #20352f; background: #eef3f0; }
  :global(button), :global(input), :global(select) { font: inherit; }
  .app-container { display: grid; grid-template-columns: 360px minmax(0,1fr); grid-template-rows: 76px minmax(0,1fr); height: 100vh; height: 100dvh; overflow: hidden; }
  .workspace-header { grid-column: 1/-1; background: #fff; border-bottom: 1px solid #dde7e1; display: flex; align-items: center; justify-content: space-between; padding: 0 26px; gap: 16px; z-index: 5; }
  .identity, .header-actions { display: flex; gap: 14px; align-items: center; }
  .identity strong { display: block; font-size: 20px; letter-spacing: -.6px; }
  .identity small { display: block; color: #687d73; font-size: 11px; margin-top: 4px; }
  .brand-icon { display: grid; place-items: center; background: #145d45; color: #d7ef9c; border-radius: 13px; width: 40px; height: 40px; font-size: 25px; font-weight: 750; }
  .workspace-label { font-size: 11px; color: #6a7f74; letter-spacing: 1px; margin-right: 12px; }
  .sidebar { display: flex; flex-direction: column; min-height: 0; background: #fff; border-right: 1px solid #dde7e1; z-index: 3; }
  .panel-heading { padding: 26px 24px 18px; }
  .eyebrow { font-size: 10px; letter-spacing: 1.7px; color: #578170; font-weight: 700; }
  h1 { font-size: 22px; letter-spacing: -.6px; margin: 10px 0 7px; }
  .panel-heading p { color: #6a7f74; margin: 0; font-size: 12px; }
  .panel-tabs { display: flex; gap: 4px; padding: 5px; margin: 0 20px 20px; background: #f0f4f1; border-radius: 10px; }
  .panel-tabs button { flex: 1; background: transparent; border: 0; padding: 10px; font-size: 12px; border-radius: 7px; cursor: pointer; color: #64796f; font-weight: 650; }
  .panel-tabs .chosen { background: #fff; color: #145d45; box-shadow: 0 2px 6px #183d2510; }
  .sidebar-content { flex: 1; min-height: 0; overflow-y: auto; scrollbar-width: thin; scrollbar-color: #bdcec3 transparent; }
  .tab-panel[hidden] { display: none; }
  .main-action, .menu-section, .section-intro, .saved-list { padding: 0 24px 20px; }
  .section-title { font-size: 11px; font-weight: 750; color: #627b6d; letter-spacing: .7px; margin: 8px 0 12px; }
  .control-card { border: 1px solid #e0e9e3; background: #f9fbfa; border-radius: 12px; padding: 15px; margin-bottom: 10px; }
  label { display: block; font-size: 12px; font-weight: 650; margin-bottom: 8px; }
  select, .supplier-form input { width: 100%; background: #fff; border: 1px solid #cbdad1; padding: 11px; border-radius: 8px; color: #263f32; font-size: 13px; }
  .primary-btn, .secondary-btn, .mode-btn { border: 1px solid #cfddd3; border-radius: 8px; padding: 11px 14px; font-size: 12px; font-weight: 650; cursor: pointer; transition: background .15s; }
  .primary-btn { background: #166348; color: #fff; border-color: #166348; }
  .primary-btn:hover { background: #104b37; }
  .secondary-btn, .mode-btn { background: #fff; color: #315941; }
  .secondary-btn:hover, .mode-btn:hover { background: #edf5ef; }
  .main-action button, .supplier-form button, .control-card button { width: 100%; }
  .secondary-btn { margin-top: 10px; }
  .header-actions button { margin: 0; white-space: nowrap; }
  .mode-selector { display: flex; gap: 8px; }
  .mode-btn { flex: 1; }
  .active { background: #e5f1e8; color: #185539; border-color: #a9cbb6; }
  .toggle-row, .filter-header, .buffer-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
  .toggle-info { display: flex; flex-direction: column; gap: 5px; }
  .toggle-title { font-size: 13px; font-weight: 650; } .toggle-subtitle { font-size: 11px; color: #718479; }
  .ios-switch { width: 38px; height: 22px; position: relative; flex-shrink: 0; margin: 0; }
  .ios-switch input { position: absolute; opacity: 0; width: 100%; height: 100%; margin: 0; }
  .slider { position: absolute; inset: 0; border-radius: 20px; background: #bdcbc2; pointer-events: none; }
  .slider:before { content: ''; position: absolute; width: 16px; height: 16px; border-radius: 50%; top: 3px; left: 3px; background: white; transition: transform .15s; }
  input:checked + .slider { background: #166348; } input:checked + .slider:before { transform: translateX(16px); }
  input:focus-visible + .slider { outline: 2px solid #166348; outline-offset: 3px; }
  .filter-value { font-size: 12px; color: #166348; font-weight: 750; white-space: nowrap; }
  .range-slider { width: 100%; accent-color: #166348; margin-top: 12px; }
  .range-labels { display: flex; justify-content: space-between; color: #6d8275; font-size: 10px; }
  .sidebar-footer { flex-shrink: 0; padding: 14px 24px; border-top: 1px solid #e0e9e3; background: #f9fbfa; }
  .status-pill { display: flex; gap: 8px; font-size: 11px; line-height: 1.5; color: #4b6958; }
  .dot { width: 6px; height: 6px; border-radius: 50%; background: #80978a; flex-shrink: 0; margin-top: 5px; } .loaded .dot { background: #248153; }
  .footer-note { margin: 5px 0 0; font-size: 10px; color: #6c8374; }
  .supplier-form h2, .section-intro h2 { font-size: 17px; margin: 0 0 10px; }
  .supplier-form p, .section-intro p, .saved-list p { font-size: 12px; line-height: 1.6; color: #697f72; }
  .supplier-form fieldset { border: 0; padding: 0; margin: 0; min-width: 0; }
  .supplier-form input { margin-bottom: 14px; }
  .supplier-form .form-error { padding: 12px; border-radius: 8px; background: #fff0ed; color: #9e3826; }
  .saved-list button { display: block; width: 100%; text-align: left; padding: 14px; margin-bottom: 8px; border: 1px solid #e0e9e3; background: #fff; border-radius: 9px; cursor: pointer; overflow-wrap: anywhere; }
  .saved-list strong { display: block; font-size: 13px; } .saved-list span { display: block; margin-top: 6px; font-size: 11px; color: #6b7c71; }
  .map-viewport { position: relative; min-width: 0; min-height: 0; background: #e5ece6; }
  .map-overlay { position: absolute; top: 20px; left: 20px; pointer-events: none; }
  .overlay-card { padding: 12px 18px; background: #ffffffed; border: 1px solid #dce6df; border-radius: 10px; box-shadow: 0 3px 16px #19382510; }
  .overlay-card strong { display: block; color: #6a8273; font-size: 9px; letter-spacing: 1px; margin-bottom: 5px; }
  .value { font-size: 14px; font-weight: 700; }
  .map-guide { position: absolute; bottom: 110px; left: 20px; right: 20px; z-index: 1; pointer-events: none; font-size: 12px; background: #fffef5ed; border: 1px solid #e3e5d5; border-radius: 8px; padding: 10px 14px; width: fit-content; max-width: calc(100% - 40px); }
  .map-legend { position: absolute; bottom: 32px; left: 20px; padding: 12px 16px; background: #fffffff0; border: 1px solid #dde7e1; border-radius: 9px; max-width: calc(100% - 40px); pointer-events: none; }
  .map-legend strong { display: block; font-size: 11px; margin-bottom: 7px; } .map-legend span { display: block; font-size: 10px; color: #536c5d; }
  .map-legend i { display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin: 0 3px 0 8px; } .green { background: #0f6f4a; } .orange { background: #e88724; } .purple { background: #7c3aed; }
  .density-bar { height: 6px; border-radius: 4px; background: linear-gradient(90deg,#22c55e,#84cc16,#eab308,#ea580c,#b91c1c); margin-bottom: 6px; }
  .panel-hidden { display: none; } .app-container:has(.panel-hidden) { grid-template-columns: minmax(0,1fr); }
  button:disabled { opacity: .55; cursor: not-allowed; } :focus-visible { outline: 2px solid #21674c; outline-offset: 3px; }
  @media(max-width: 760px) {
    .app-container { grid-template-columns: 1fr; grid-template-rows: 68px minmax(0,1fr); }
    .workspace-header { padding: 0 12px; } .identity strong { font-size: 16px; } .identity small, .workspace-label, .brand-icon { display: none; }
    .header-actions { gap: 6px; } .header-actions button { font-size: 10px; padding: 10px; }
    .sidebar { position: absolute; top: 80px; left: 12px; bottom: 20px; width: min(340px, calc(100% - 24px)); border: 1px solid #dae5dd; border-radius: 16px; box-shadow: 0 10px 45px #19382530; overflow: hidden; }
    .map-viewport { grid-column: 1; grid-row: 2; }
    .panel-heading { padding: 18px 20px 14px; } h1 { font-size: 20px; }
  }
  @media(prefers-reduced-motion: reduce) { * { transition: none !important; } }
</style>
