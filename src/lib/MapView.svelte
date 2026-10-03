<script>
  import { onMount, onDestroy, createEventDispatcher } from 'svelte';
  import maplibregl from 'maplibre-gl';
  import {
    basemaps,
    MVT_TILES,
    MVT_SOURCE_LAYER,
    MAP_CENTER,
    MAP_ZOOM
  } from './config.js';

  const dispatch = createEventDispatcher();

  export let basemap = 'street';
  export let picking = false;
  export let routePicking = false;
  let routeMarkers = [];
  let draftMarker;
  let geolocate;
  let customData = { type: 'FeatureCollection', features: [] };
  const CUSTOM = 'custom-suppliers';

  let locationMessage = '';
  let locationError = false;
  let resizeObserver;
  let container;
  let map;
  let appliedBasemap = basemap;
  let popup;
  let layerMode = 'none';
  let currentFilterValue = 0;
  let visible = true;
  let styleReady = false;
  let bufferData;
  
  const SOURCE_ID = 'suppliers';
  const LAYER_ID = 'suppliers-circles';
  const BUFFER_SOURCE_ID = 'buffer-source';
  const BUFFER_LAYER_ID = 'buffer-layer';

  const circlePaint = {
    'circle-radius': ['interpolate', ['linear'], ['zoom'], 6, 3, 12, 6, 16, 9],
    'circle-color': '#0f6f4a',
    'circle-stroke-width': 1,
    'circle-stroke-color': '#ffffff'
  };

  const heatmapPaint = {
    'heatmap-weight': 1,
    'heatmap-intensity': ['interpolate', ['linear'], ['zoom'], 0, 1, 9, 3],
    'heatmap-color': [
      'interpolate', ['linear'], ['heatmap-density'],
      0, 'rgba(34,197,94,0)',
      0.2, 'rgb(34,197,94)',
      0.4, 'rgb(132,204,22)',
      0.6, 'rgb(234,179,8)',
      0.8, 'rgb(234,88,12)',
      1, 'rgb(185,28,28)'
    ],
    'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 0, 2, 9, 20],
    'heatmap-opacity': 0.8
  };

  function escapeHtml(value) {
    return String(value ?? '—')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;');
  }

  function onSupplierClick(event) {
    if (routePicking || picking || layerMode === 'heatmap') return;
    const props = event.features?.[0]?.properties;
    if (!props) return;
    
    // Dispatch event to App.svelte for Buffer logic
    const [lng, lat] = event.features[0].geometry.coordinates;
    dispatch('supplierClick', { lng, lat });

    const area = props.plotareaha ?? '—';
    const html = `
      <div class="popup-container">
        <div class="popup-header">
          <span class="supplier-name">${escapeHtml(props.entityname)}</span>
        </div>
        <div class="popup-body">
          <div class="attr-row">
            <span class="attr-label">FID</span>
            <span class="attr-value">${escapeHtml(props.FID)}</span>
          </div>
          <div class="attr-row">
            <span class="attr-label">Plot Area</span>
            <span class="attr-value">${escapeHtml(area)} ha</span>
          </div>
          <div class="attr-row">
            <span class="attr-label">Region</span>
            <span class="attr-value">${escapeHtml(props.regionlabel)}</span>
          </div>
        </div>
      </div>
    `;

    popup
      .setLngLat(event.lngLat)
      .setHTML(html)
      .addTo(map);
  }

  function onPointer() {
    map.getCanvas().style.cursor = (picking || routePicking) ? 'crosshair' : 'pointer';
  }

  function onPointerOut() {
    map.getCanvas().style.cursor = (picking || routePicking) ? 'crosshair' : '';
  }

  function clearSupplierLayer() {
    if (!map) return;
    map.off('click', LAYER_ID, onSupplierClick);
      map.off('mouseenter', LAYER_ID, onPointer);
      map.off('mouseleave', LAYER_ID, onPointerOut);
    if (map.getLayer(LAYER_ID)) map.removeLayer(LAYER_ID);
    if (map.getSource(SOURCE_ID)) map.removeSource(SOURCE_ID);
  }

  function bindClicks() {
    map.on('click', LAYER_ID, onSupplierClick);
    map.on('mouseenter', LAYER_ID, onPointer);
    map.on('mouseleave', LAYER_ID, onPointerOut);
  }

  function applyLayer() {
    if (!map || !styleReady) return;
    popup?.remove();
    map.getCanvas().style.cursor = (picking || routePicking) ? 'crosshair' : '';
    clearSupplierLayer();
    renderCustom();
    if (layerMode === 'none') return;

    map.addSource(SOURCE_ID, {
      type: 'vector',
      tiles: [MVT_TILES],
      maxzoom: 14,
    });

    if (layerMode === 'mvt') {
      map.addLayer({
        id: LAYER_ID,
        type: 'circle',
        source: SOURCE_ID,
        'source-layer': MVT_SOURCE_LAYER,
        paint: circlePaint
      });
      bindClicks();
    } else if (layerMode === 'heatmap') {
      map.addLayer({
        id: LAYER_ID,
        type: 'heatmap',
        source: SOURCE_ID,
        'source-layer': MVT_SOURCE_LAYER,
        paint: heatmapPaint
      });
    }

    applyFilter(currentFilterValue);
    toggleLayer(visible);
  }

  export function useMvt() {
    layerMode = 'mvt';
    applyLayer();
  }

  export function setLayerMode(mode) {
    layerMode = mode;
    applyLayer();
  }

  export function applyFilter(minArea) {
    currentFilterValue = minArea;
    renderCustom();
    if (!map || !map.getLayer(LAYER_ID)) return;
    popup?.remove();
    map.setFilter(LAYER_ID, minArea > 0 ? ['>=', ['to-number', ['get', 'plotareaha'], -1], Number(minArea)] : null);
  }

  export function toggleLayer(value) {
    visible = value;
    renderCustom();
    if (!visible) { popup?.remove(); if (map) map.getCanvas().style.cursor = (picking || routePicking) ? 'crosshair' : ''; }
    if (!map || !map.getLayer(LAYER_ID)) return;
    map.setLayoutProperty(LAYER_ID, 'visibility', visible ? 'visible' : 'none');
  }

  export function updateSuppliers(data) {
    customData = data;
    renderCustom();
  }

  export function locateMe() {
    if (!geolocate?.trigger()) {
      locationMessage = 'Lokasi belum siap. Pastikan izin lokasi aktif dan gunakan HTTPS atau localhost.';
      locationError = true;
    }
  }

  export function markLocation(point) {
    if (!map) return;
    if (!draftMarker) draftMarker = new maplibregl.Marker({ color: '#e88724' });
    draftMarker.setLngLat([point.lng, point.lat]).addTo(map);
  }

  export function finishPicking() {
    draftMarker?.remove();
    draftMarker = null;
  }

  export function focusSupplier(feature) {
    map?.flyTo({ center: feature.geometry.coordinates, zoom: 12 });
  }

  const overlays = new Map();
  export function closeDetails() { popup?.remove(); }
  export function showPlacePopup(feature) {
    const props = feature.properties || {};
    popup?.setLngLat(feature.geometry.coordinates).setHTML(
      `<div class="popup-header">${escapeHtml(props.name || 'Lokasi')}</div><div class="popup-body"><p>${escapeHtml(props.address || props.kind || '')}</p>${props.distance !== undefined ? `<p>Jarak dari pusat: ${(Number(props.distance) / 1000).toFixed(1)} km</p>` : ''}<p>${feature.geometry.coordinates.map(n => Number(n).toFixed(5)).join(', ')}</p></div>`
    ).addTo(map);
  }
  export function showRoutePopup(feature, mode = feature.properties.modeLabel || 'Perjalanan') {
    const coords = feature.geometry.coordinates;
    popup?.setLngLat(coords[Math.floor(coords.length / 2)]).setHTML(
      `<div class="popup-header">Rute ${escapeHtml(mode)}</div><div class="popup-body"><strong>${(feature.properties.distance / 1000).toFixed(1)} km · ${Math.ceil(feature.properties.duration / 60)} menit</strong><p>Estimasi tanpa lalu lintas langsung.</p></div>`
    ).addTo(map);
  }

  export function setRouteEndpoints(origin, destination) {
    routeMarkers.forEach(marker => marker.remove());
    routeMarkers = [];
    if (!map) return;
    [origin, destination].forEach((point, index) => {
      if (!point) return;
      const el = document.createElement('div');
      el.textContent = index === 0 ? 'A' : 'B';
      el.setAttribute('aria-label', index === 0 ? 'Asal rute' : 'Tujuan rute');
      el.style.cssText = 'background:#166348;color:white;border:2px solid white;border-radius:50%;width:30px;height:30px;display:grid;place-items:center;font-weight:700;box-shadow:0 2px 8px #0004';
      routeMarkers.push(new maplibregl.Marker({ element: el }).setLngLat([point.lng, point.lat]).addTo(map));
    });
  }

  export function showOverlay(name, data, fit = false) {
    overlays.set(name, data);
    renderOverlays();
    if (fit && map && data.features.length) {
      const coordinates = data.features.flatMap(f => f.geometry.type === 'Point' ? [f.geometry.coordinates] : f.geometry.coordinates);
      const bounds = new maplibregl.LngLatBounds();
      coordinates.forEach(p => bounds.extend(p));
      map.fitBounds(bounds, { padding: 60, maxZoom: 14 });
    }
  }
  function renderOverlays() {
    if (!map || !styleReady) return;
    for (const [name, data] of overlays) {
      const id = 'tools-' + name;
      if (map.getSource(id)) map.getSource(id).setData(data);
      else map.addSource(id, { type: 'geojson', data });
      if (!map.getLayer(id)) map.addLayer({ id, source: id,
        type: name === 'route' ? 'line' : 'circle',
        paint: name === 'route' ? { 'line-color': '#2563eb', 'line-width': 5 } : {
          'circle-color': name === 'company' ? '#7c3aed' : '#e88724', 'circle-radius': 7,
          'circle-stroke-color': '#fff', 'circle-stroke-width': 2
        }
      });
    }
  }

  function renderCustom() {
    if (!map || !styleReady) return;
    if (map.getSource(CUSTOM)) map.getSource(CUSTOM).setData(customData);
    else map.addSource(CUSTOM, { type: 'geojson', data: customData });
    const type = layerMode === 'heatmap' ? 'heatmap' : 'circle';
    if (map.getLayer(CUSTOM) && map.getLayer(CUSTOM).type !== type) map.removeLayer(CUSTOM);
    if (!map.getLayer(CUSTOM)) {
      map.addLayer({ id: CUSTOM, type, source: CUSTOM, paint: type === 'heatmap' ? heatmapPaint : circlePaint });
    }
    map.setFilter(CUSTOM, currentFilterValue > 0 ? ['>=', ['get', 'plotareaha'], currentFilterValue] : null);
    map.setLayoutProperty(CUSTOM, 'visibility', visible ? 'visible' : 'none');
  }

  function createCircle(center, radiusInKm) {
    const points = [];
    const steps = 64;
    const radians = Math.PI / 180;
    const latitude = center[1] * radians;
    const longitude = center[0] * radians;
    const angularDistance = radiusInKm / 6371.0088;
    for (let i = 0; i < steps; i++) {
      const bearing = i / steps * Math.PI * 2;
      const lat = Math.asin(Math.sin(latitude) * Math.cos(angularDistance) +
        Math.cos(latitude) * Math.sin(angularDistance) * Math.cos(bearing));
      const lng = longitude + Math.atan2(Math.sin(bearing) * Math.sin(angularDistance) * Math.cos(latitude),
        Math.cos(angularDistance) - Math.sin(latitude) * Math.sin(lat));
      points.push([lng / radians, lat / radians]);
    }
    points.push(points[0]);
    return {
      type: 'Feature',
      properties: {},
      geometry: {
        type: 'Polygon',
        coordinates: [points]
      }
    };
  }

  export function createBuffer(lngLat, radiusKm) {
    if (!lngLat || !Number.isFinite(lngLat.lng) || !Number.isFinite(lngLat.lat) ||
        !Number.isFinite(radiusKm) || radiusKm <= 0) return;
    bufferData = createCircle([lngLat.lng, lngLat.lat], radiusKm);
    renderBuffer();
  }

  function renderBuffer() {
    if (!map || !styleReady || !bufferData) return;
    const source = map.getSource(BUFFER_SOURCE_ID);
    if (source) source.setData(bufferData);
    else map.addSource(BUFFER_SOURCE_ID, { type: 'geojson', data: bufferData });
    if (!map.getLayer(BUFFER_LAYER_ID)) map.addLayer({
      id: BUFFER_LAYER_ID,
      type: 'fill',
      source: BUFFER_SOURCE_ID,
      paint: { 'fill-color': '#0f6f4a', 'fill-opacity': 0.2, 'fill-outline-color': '#0f6f4a' }
    }, map.getLayer(LAYER_ID) ? LAYER_ID : undefined);
  }

  export function clearBuffer() {
    bufferData = null;
    if (!map || !styleReady) return;
    if (map.getLayer(BUFFER_LAYER_ID)) map.removeLayer(BUFFER_LAYER_ID);
    if (map.getSource(BUFFER_SOURCE_ID)) map.removeSource(BUFFER_SOURCE_ID);
  }

  onMount(() => {
    popup = new maplibregl.Popup({ 
      closeButton: true, 
      closeOnClick: true,
      className: 'custom-popup' 
    });
    map = new maplibregl.Map({
      container,
      style: basemaps[basemap],
      center: MAP_CENTER,
      locale: { 'GeolocateControl.FindMyLocation': 'Lokasi saya', 'GeolocateControl.LocationNotAvailable': 'Lokasi tidak tersedia' },
      zoom: MAP_ZOOM
    });
    resizeObserver = new ResizeObserver(() => map?.resize());
    resizeObserver.observe(container);
    map.addControl(new maplibregl.NavigationControl(), 'top-right');
    geolocate = new maplibregl.GeolocateControl({
      positionOptions: { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 },
      trackUserLocation: false,
      showUserLocation: true,
      showAccuracyCircle: true,
      fitBoundsOptions: { maxZoom: 16 }
    });
    map.addControl(geolocate, 'top-right');
    geolocate.on('geolocate', (event) => {
      dispatch('gpsLocated', { lng: event.coords.longitude, lat: event.coords.latitude });
      locationError = false;
      locationMessage = `Lokasi ditemukan · akurasi ±${Math.round(event.coords.accuracy)} m`;
    });
    geolocate.on('error', (event) => {
      locationError = true;
      locationMessage = event.code === 1
        ? 'Izin lokasi ditolak. Izinkan akses lokasi di pengaturan browser.'
        : event.code === 3
          ? 'Pencarian lokasi habis waktu. Tekan tombol lokasi untuk mencoba lagi.'
          : 'Lokasi belum tersedia. Aktifkan layanan lokasi perangkat dan coba lagi.';
    });
    if (!window.isSecureContext) {
      locationError = true;
      locationMessage = 'Lokasi perangkat memerlukan HTTPS atau localhost.';
    } else if (!navigator.geolocation) {
      locationError = true;
      locationMessage = 'Browser ini tidak mendukung lokasi perangkat.';
    }

    map.on('style.load', () => {
      styleReady = true;
      applyLayer();
      renderBuffer();
      renderCustom();
      renderOverlays();
    });
    map.on('click', CUSTOM, onSupplierClick);
    map.on('mouseenter', CUSTOM, onPointer);
    map.on('mouseleave', CUSTOM, onPointerOut);
    map.on('click', (event) => {
      const ids = [LAYER_ID, CUSTOM, ...[...overlays.keys()].filter(n => n !== 'route').map(n => 'tools-' + n)].filter(id => map.getLayer(id) && map.getLayer(id).type === 'circle');
      const feature = ids.length ? map.queryRenderedFeatures(event.point, { layers: ids })[0] : null;
      const coordinates = feature?.geometry.type === 'Point' ? feature.geometry.coordinates : [event.lngLat.lng, event.lngLat.lat];
      if (!picking && !routePicking && map.getLayer('tools-route')) {
        const routeHit = map.queryRenderedFeatures(event.point, { layers: ['tools-route'] })[0];
        if (routeHit) showRoutePopup(routeHit);
      }
      if (feature?.properties?.name && !picking && !routePicking) showPlacePopup(feature);
      dispatch('pointSelected', { lng: coordinates[0], lat: coordinates[1], name: feature?.properties?.name || feature?.properties?.entityname });
      if (!picking) return;
      const lng = ((event.lngLat.lng + 180) % 360 + 360) % 360 - 180;
      const lat = event.lngLat.lat;
      if (Math.abs(lat) > 85) return;
      popup?.remove();
      if (!draftMarker) draftMarker = new maplibregl.Marker({ color: '#e88724' });
      draftMarker.setLngLat([lng, lat]).addTo(map);
      dispatch('locationPicked', { lng, lat });
    });
    map.on('error', () => dispatch('mapError'));
  });

  $: if (map) map.getCanvas().style.cursor = (picking || routePicking) ? 'crosshair' : '';

  $: if (map && basemap !== appliedBasemap) {
    appliedBasemap = basemap;
    popup?.remove();
    styleReady = false;
    map.setStyle(basemaps[basemap], { diff: false });
  }

  onDestroy(() => {
    routeMarkers.forEach(marker => marker.remove());
    resizeObserver?.disconnect();
    finishPicking();
    popup?.remove();
    map?.remove();
  });
</script>

<div class="map" bind:this={container}></div>
{#if locationMessage}
  <div class="location-notice" class:location-error={locationError} role="status" aria-live="polite">
    <span>{locationMessage}</span>
    <button aria-label="Tutup pesan lokasi" on:click={() => locationMessage = ''}>×</button>
  </div>
{/if}

<style>
  .location-notice {
    position: absolute; bottom: 158px; left: 16px; right: 16px; z-index: 2;
    width: fit-content; max-width: calc(100% - 32px); box-sizing: border-box;
    display: flex; align-items: center; gap: 12px; padding: 12px 16px;
    background: white; color: #14532d; border: 1px solid #bbd6c5;
    border-radius: 10px; box-shadow: 0 4px 16px #0002; font-size: 13px;
  }
  .location-error { color: #9a3412; border-color: #fed7aa; }
  .location-notice button { background: transparent; border: 0; cursor: pointer; color: inherit; font-size: 22px; min-width: 32px; min-height: 32px; }

  .map {
    flex: 1;
    height: 100%;
    min-height: 0;
  }

  :global(.custom-popup .maplibre-gl-popup-content) {
    padding: 0;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 15px rgba(0,0,0,0.15);
    font-family: system-ui, -apple-system, sans-serif;
  }

  :global(.popup-container) {
    min-width: 200px;
  }

  :global(.popup-header) {
    background: #0f6f4a;
    color: white;
    padding: 14px 34px 14px 16px;
    font-weight: 600;
    font-size: 14px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
  }

  :global(.supplier-name) {
    display: block;
    white-space: normal;
    overflow-wrap: anywhere;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  :global(.popup-body) {
    padding: 8px 12px;
    background: #fff;
  }

  :global(.attr-row) {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    padding: 8px 0;
    font-size: 12px;
    border-bottom: 1px solid #f0f0f0;
  }

  :global(.attr-row:last-child) {
    border-bottom: none;
  }

  :global(.attr-label) {
    color: #666;
    font-weight: 500;
  }

  :global(.attr-value) {
    color: #333;
    font-weight: 600;
    text-align: right;
    overflow-wrap: anywhere;
    min-width: 0;
  }
</style>
