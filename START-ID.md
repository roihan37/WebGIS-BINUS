# Supplier WebGIS — instal, mulai, dan coding

Ikuti halaman ini dari atas ke bawah. Setiap perintah dan setiap file yang Anda butuhkan ada di blok yang bisa disalin.

Anda menjalankan dua program, dan kedua jendela tetap terbuka:

1. Server tile Python di port **8080**. Server ini membaca titik supplier dari `data_mvt/suppliers.mbtiles` di laptop Anda dan mengirim vector tile `.mvt` yang kecil.
2. Halaman, di port **5173**. Ini aplikasi Svelte. MapLibre menggambar basemap MAPID, lalu menggambar titik supplier di atasnya.

Menutup terminal menghentikan program itu. Server ini hanya memakai pustaka standar Python. Tidak ada `pip install` dan tidak ada database terpisah.

Instruktur menunjukkan kunci MAPID di kelas. Biarkan `VITE_MAPID_KEY=` kosong sampai Anda mendapat kunci itu.

---

## 1. Instal

Instal ketiga hal ini, lalu buka terminal **baru** supaya perintah baru ada di PATH.

### Node.js 18 atau lebih baru

Unduh installer **LTS** dari [https://nodejs.org](https://nodejs.org). Paket ini sudah termasuk npm.

```bash
node -v
npm -v
```

Anda harus melihat versi `v18` atau lebih tinggi, dan versi npm di baris berikutnya.

Jika `node -v` di bawah 18, instal LTS lagi dan buka terminal baru. Jika terminal mengatakan `node` tidak ditemukan, instal selesai di jendela lama. Tutup jendela itu dan buka yang baru.

### Git

Unduh Git dari [https://git-scm.com](https://git-scm.com).

Di Windows, instal **Git for Windows** dan pakai **Git Bash** untuk blok di panduan ini.

```bash
git --version
```

Anda harus melihat baris versi seperti `git version 2.x`.

### Python 3

Unduh Python 3 dari [https://www.python.org](https://www.python.org).

Di Windows, centang **Add python.exe to PATH** di installer sebelum Anda menekan Install.

macOS:

```bash
python3 --version
```

Windows (Command Prompt, PowerShell, atau Git Bash):

```bash
python --version
```

Anda harus melihat `Python 3.x`. Jika Windows mengatakan Python tidak ditemukan, tutup terminal, buka yang baru, lalu jalankan pemeriksaan lagi.

---

## 2. Ambil proyek

macOS atau Git Bash:

```bash
git clone https://github.com/radenpranantya/webgis-binus-mapid-svelte.git
cd webgis-binus-mapid-svelte
```

Anda berada di folder yang benar jika nama-nama ini muncul.

macOS atau Git Bash:

```bash
ls
```

Windows Command Prompt:

```bat
dir
```

Anda harus melihat `package.json`, `src`, `tiles`, dan `data_mvt`.

Jika `cd webgis-binus-mapid-svelte` mengatakan folder tidak ada, Anda sudah berada di dalamnya. Jalankan `ls` atau `dir` dan lanjutkan.

---

## 3. Kunci basemap

File ini tetap di laptop Anda. Git tidak menyimpan `.env`.

macOS atau Git Bash:

```bash
cp .env.example .env
```

Windows Command Prompt, dari folder yang sama:

```bat
copy .env.example .env
```

Buka `.env`. Isinya satu baris. Taruh kunci dari kelas setelah tanda sama dengan:

```bash
VITE_MAPID_KEY=
```

Bentuk contoh, dengan kunci palsu:

```bash
VITE_MAPID_KEY=paste-the-class-key-here
```

Tanpa tanda kutip. Tanpa spasi di sekitar `=`.

Simpan file.

Vite membaca `.env` hanya saat mulai. Jika Anda mengubah kunci setelah halaman sudah berjalan, pergi ke terminal tempat `npm run dev` berjalan, tekan **Ctrl+C**, lalu jalankan `npm run dev` lagi.

---

## 4. Mulai tile (terminal 1)

Tetap di folder proyek. Jalankan server dan biarkan jendela ini terbuka.

macOS:

```bash
python3 tiles/server.py
```

Windows:

```bash
python tiles/server.py
```

Berhasil jika baris ini muncul, dan kursor tidak kembali:

```text
Tiles on http://127.0.0.1:8080/suppliers/{z}/{x}/{y}.mvt
```

`{z}`, `{x}`, dan `{y}` tetap berupa kata itu. Peta mengisinya saat meminta satu kotak.

Jika perintah gagal:

| Yang Anda lihat | Yang dilakukan |
| --- | --- |
| `command not found` atau `Python was not found` | macOS memakai `python3`. Windows memakai `python`. Jika Windows masih gagal, buka terminal baru setelah menginstal Python dengan **Add python.exe to PATH**. |
| `Missing ... suppliers.mbtiles` | Anda berada di folder yang salah. `cd` ke folder yang berisi `tiles` dan `data_mvt`, lalu jalankan perintah lagi. |
| `Address already in use` | Port 8080 sudah terpakai. Tutup server tile sebelumnya, atau hentikan program lain yang memakai 8080, lalu jalankan perintah lagi. |

---

## 5. Mulai halaman (terminal 2)

Buka terminal **kedua**. Biarkan terminal 1 tetap berjalan.

Masuk ke folder proyek yang sama, lalu instal dan mulai halaman.

macOS atau Git Bash:

```bash
cd webgis-binus-mapid-svelte
npm install
npm run dev
```

Jika Anda sudah berada di folder itu, lewati baris `cd`.

Windows Command Prompt, jika Anda belum berada di folder:

```bat
cd webgis-binus-mapid-svelte
npm install
npm run dev
```

`npm install` dijalankan sekali, pada kali pertama. Proses ini bisa memakan waktu satu menit. Setelah itu `npm run dev` tetap berjalan.

Berhasil jika tampilannya seperti ini:

```text
  VITE v5.x.x  ready in ... ms

  ➜  Local:   http://127.0.0.1:5173/
```

Buka URL lokal itu di browser. Jika Vite mencetak port lain, buka URL yang dicetaknya.

Jika perintah gagal:

| Yang Anda lihat | Yang dilakukan |
| --- | --- |
| `npm` was not found | Instal Node.js 18 atau lebih baru, lalu buka terminal baru. |
| Port `5173` is in use | `npm run dev` sebelumnya masih berjalan. Pergi ke terminal itu dan tekan **Ctrl+C**, atau tutup terminal itu, lalu jalankan `npm run dev` lagi. |

---

## 6. Periksa peta yang berjalan

Lakukan ini berurutan di browser.

1. Judul sidebar adalah **Supplier WebGIS**. Baris status mengatakan `Basemap only. Points are not loaded yet.`
2. Buka daftar **Basemap** dan ganti **MAPID Street 2D**, **MAPID Light**, **MAPID Satellite**, dan **MapLibre Demo (fallback)**. Gaya peta berubah setiap kali.
3. Klik **Use MVT**. Baris status berubah menjadi `MVT is on. Pan the map and watch the small .mvt requests.`
4. Geser dan perbesar peta. Titik hijau muncul.
5. Buka DevTools (**F12** atau **Cmd+Option+I**), pilih **Network**, dan saring dengan `mvt`. Menggeser peta memuat permintaan kecil ke `127.0.0.1:8080`.
6. Klik satu titik hijau. Popup menampilkan nama supplier, **FID**, luas plot dalam **ha**, dan region.

Jika basemap tetap kosong, kunci di `.env` belum diisi atau salah. Perbaiki baris itu, tekan **Ctrl+C** di terminal 2, lalu jalankan `npm run dev` lagi.

Jika **Use MVT** dijalankan dan tidak ada titik hijau, terminal 1 tidak berjalan. Jalankan `tiles/server.py` lagi dan biarkan jendela itu terbuka. Lalu klik **Use MVT** sekali lagi.

---

## 7. Coding

Hasil clone sudah berisi file-file ini. Buka file yang disebut di setiap langkah. Jika file Anda kosong, atau Anda sedang menyusul, pilih seluruh isinya dan tempel blok lengkap untuk file itu. Simpan. Halaman memperbarui dirinya sendiri selama `npm run dev` berjalan.

Tempel ke file yang disebut di langkah itu.

### 7.1 `src/lib/config.js`

File ini menyimpan URL dan tampilan pertama peta.

- `street`, `light`, dan `satellite` adalah URL gaya MAPID. Masing-masing menambahkan `VITE_MAPID_KEY` Anda.
- `demo` adalah gaya contoh MapLibre yang publik, dipakai saat Anda memilih fallback di daftar.
- `MVT_TILES` adalah URL tile di laptop Anda. MapLibre mengganti `{z}`, `{x}`, dan `{y}`.
- `MVT_SOURCE_LAYER` adalah nama layer di dalam setiap tile: `suppliers`.
- `MAP_CENTER` adalah `[longitude, latitude]`: `[-7.7, 7.2]`.
- `MAP_ZOOM` adalah `9`.

Ganti seluruh file dengan:

```js
const MAPID_KEY = import.meta.env.VITE_MAPID_KEY;

export const basemaps = {
  street: `https://basemap.mapid.io/styles/street-2d-building/style.json?key=${MAPID_KEY}`,
  light: `https://basemap.mapid.io/styles/light/style.json?key=${MAPID_KEY}`,
  satellite: `https://basemap.mapid.io/styles/satellite/style.json?key=${MAPID_KEY}`,
  demo: 'https://demotiles.maplibre.org/style.json'
};

export const MVT_TILES = 'http://127.0.0.1:8080/suppliers/{z}/{x}/{y}.mvt';
export const MVT_SOURCE_LAYER = 'suppliers';
export const MAP_CENTER = [-7.7, 7.2];
export const MAP_ZOOM = 9;
```

Simpan. Daftar basemap tetap mengganti gaya. URL yang salah atau kunci yang kosong membuat peta blank sampai Anda memperbaiki `.env` dan menjalankan ulang Vite.

### 7.2 `src/lib/MapView.svelte`

File ini membuat peta, mengganti basemap, menggambar titik hijau, dan membuka popup. Blok di bawah adalah file yang sama, berurutan, supaya Anda melihat fungsi tiap bagian. Blok terakhir adalah seluruh file. Tempel blok itu jika Anda perlu mengganti file.

**Buat peta dan kontrol navigasi.** `onMount` berjalan setelah halaman punya tempat untuk menggambar. Gaya datang dari sidebar. Pusat dan zoom datang dari `config.js`. Kontrol `+` dan `−` ada di kanan atas.

```svelte
  onMount(() => {
    popup = new maplibregl.Popup({ closeButton: true, closeOnClick: true });
    map = new maplibregl.Map({
      container,
      style: basemaps[basemap],
      center: MAP_CENTER,
      zoom: MAP_ZOOM
    });
    map.addControl(new maplibregl.NavigationControl(), 'top-right');
    map.on('style.load', applyLayer);
  });
```

**Ganti basemap.** Saat sidebar mengubah `basemap`, kode ini menjalankan `setStyle` dengan `{ diff: false }`. Pergantian gaya menghapus layer kustom. `diff: false` membuat `style.load` menyala lagi, dan `applyLayer` mengembalikan titik. Diff bawaan menghapus layer itu tanpa memberitahu Anda.

```svelte
  $: if (map && basemap !== appliedBasemap) {
    appliedBasemap = basemap;
    popup?.remove();
    map.setStyle(basemaps[basemap], { diff: false });
  }
```

**Tambah vector source dan lingkaran hijau.** `useMvt()` mengatur mode, lalu `applyLayer` menambah source dan layer lingkaran. Nama source layer harus `suppliers`. Lingkaran berwarna hijau (`#0f6f4a`) dengan garis putih, dan membesar saat Anda memperbesar peta.

```svelte
  function applyLayer() {
    if (!map.getStyle()) return;
    clearSupplierLayer();
    if (layerMode !== 'mvt') return;
    map.addSource(SOURCE_ID, {
      type: 'vector',
      tiles: [MVT_TILES],
      minzoom: 0,
      maxzoom: 14
    });
    map.addLayer({
      id: LAYER_ID,
      type: 'circle',
      source: SOURCE_ID,
      'source-layer': MVT_SOURCE_LAYER,
      paint: circlePaint
    });
    bindClicks();
  }

  export function useMvt() {
    layerMode = 'mvt';
    applyLayer();
  }
```

**Popup.** Satu klik membaca fitur pertama. Popup menampilkan `entityname`, `FID`, `plotareaha` (hektar), dan `regionlabel`.

```svelte
  function onSupplierClick(event) {
    const props = event.features?.[0]?.properties;
    if (!props) return;
    const area = props.plotareaha ?? '—';
    popup
      .setLngLat(event.lngLat)
      .setHTML(
        `<strong>${escapeHtml(props.entityname)}</strong><br>` +
          `FID ${escapeHtml(props.FID)}<br>` +
          `Plot ${escapeHtml(area)} ha<br>` +
          `${escapeHtml(props.regionlabel)}`
      )
      .addTo(map);
  }
```

**Seluruh file.** Buka `src/lib/MapView.svelte`, pilih semua, tempel ini, lalu simpan.

```svelte
<script>
  import { onMount, onDestroy } from 'svelte';
  import maplibregl from 'maplibre-gl';
  import {
    basemaps,
    MVT_TILES,
    MVT_SOURCE_LAYER,
    MAP_CENTER,
    MAP_ZOOM
  } from './config.js';

  export let basemap = 'street';

  let container;
  let map;
  let appliedBasemap = basemap;
  let popup;
  let layerMode = 'none';

  const SOURCE_ID = 'suppliers';
  const LAYER_ID = 'suppliers-circles';

  const circlePaint = {
    'circle-radius': ['interpolate', ['linear'], ['zoom'], 6, 3, 12, 6, 16, 9],
    'circle-color': '#0f6f4a',
    'circle-stroke-width': 1,
    'circle-stroke-color': '#ffffff'
  };

  function escapeHtml(value) {
    return String(value ?? '—')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;');
  }

  function onSupplierClick(event) {
    const props = event.features?.[0]?.properties;
    if (!props) return;
    const area = props.plotareaha ?? '—';
    popup
      .setLngLat(event.lngLat)
      .setHTML(
        `<strong>${escapeHtml(props.entityname)}</strong><br>` +
          `FID ${escapeHtml(props.FID)}<br>` +
          `Plot ${escapeHtml(area)} ha<br>` +
          `${escapeHtml(props.regionlabel)}`
      )
      .addTo(map);
  }

  function onPointer() {
    map.getCanvas().style.cursor = 'pointer';
  }

  function onPointerOut() {
    map.getCanvas().style.cursor = '';
  }

  function clearSupplierLayer() {
    if (!map.getStyle()) return;
    if (map.getLayer(LAYER_ID)) {
      map.off('click', LAYER_ID, onSupplierClick);
      map.off('mouseenter', LAYER_ID, onPointer);
      map.off('mouseleave', LAYER_ID, onPointerOut);
      map.removeLayer(LAYER_ID);
    }
    if (map.getSource(SOURCE_ID)) map.removeSource(SOURCE_ID);
  }

  function bindClicks() {
    map.on('click', LAYER_ID, onSupplierClick);
    map.on('mouseenter', LAYER_ID, onPointer);
    map.on('mouseleave', LAYER_ID, onPointerOut);
  }

  // setStyle drops custom layers. style.load calls this again for the active mode.
  function applyLayer() {
    if (!map.getStyle()) return;
    clearSupplierLayer();
    if (layerMode !== 'mvt') return;
    map.addSource(SOURCE_ID, {
      type: 'vector',
      tiles: [MVT_TILES],
      minzoom: 0,
      maxzoom: 14
    });
    map.addLayer({
      id: LAYER_ID,
      type: 'circle',
      source: SOURCE_ID,
      'source-layer': MVT_SOURCE_LAYER,
      paint: circlePaint
    });
    bindClicks();
  }

  export function useMvt() {
    layerMode = 'mvt';
    applyLayer();
  }

  onMount(() => {
    popup = new maplibregl.Popup({ closeButton: true, closeOnClick: true });
    map = new maplibregl.Map({
      container,
      style: basemaps[basemap],
      center: MAP_CENTER,
      zoom: MAP_ZOOM
    });
    map.addControl(new maplibregl.NavigationControl(), 'top-right');
    map.on('style.load', applyLayer);
  });

  // diff:false makes style.load fire again. The default diff drops custom layers quietly.
  $: if (map && basemap !== appliedBasemap) {
    appliedBasemap = basemap;
    popup?.remove();
    map.setStyle(basemaps[basemap], { diff: false });
  }

  onDestroy(() => {
    popup?.remove();
    map?.remove();
  });
</script>

<div class="map" bind:this={container}></div>

<style>
  .map {
    flex: 1;
    height: 100%;
    min-height: 400px;
  }
</style>
```

Simpan. Ganti basemap: gaya berubah, dan titik hijau tetap ada jika **Use MVT** sudah menyala. Klik satu titik: popup menampilkan nama, FID, luas plot, dan region. Jika halaman menampilkan error merah dari Vite, Anda menempel di file yang salah atau tempelan terpotong. Pilih semua di `src/lib/MapView.svelte` dan tempel seluruh blok lagi.

### 7.3 `src/App.svelte`

Sidebar ada di sini. `<select>` mengikat `basemap` dan meneruskannya ke peta. Tombol memanggil `useMvt()` pada peta dan memperbarui baris status.

Ganti seluruh file dengan:

```svelte
<script>
  import MapView from './lib/MapView.svelte';

  let basemap = 'street';
  let mapView;
  let status = 'Basemap only. Points are not loaded yet.';

  function useMvt() {
    mapView.useMvt();
    status = 'MVT is on. Pan the map and watch the small .mvt requests.';
  }

  const options = [
    { id: 'street', label: 'MAPID Street 2D' },
    { id: 'light', label: 'MAPID Light' },
    { id: 'satellite', label: 'MAPID Satellite' },
    { id: 'demo', label: 'MapLibre Demo (fallback)' }
  ];
</script>

<div class="app">
  <aside>
    <p class="kicker">MAPID × BINUS</p>
    <h1>Supplier WebGIS</h1>
    <label for="basemap">Basemap</label>
    <select id="basemap" bind:value={basemap}>
      {#each options as option}
        <option value={option.id}>{option.label}</option>
      {/each}
    </select>
    <button type="button" on:click={useMvt}>Use MVT</button>
    <p class="hint">{status}</p>
    <p class="note">Click a green point to read supplier, plot area, and region.</p>
  </aside>
  <MapView bind:this={mapView} {basemap} />
</div>

<style>
  .app {
    display: flex;
    height: 100%;
    min-height: 100vh;
  }

  aside {
    width: 280px;
    flex-shrink: 0;
    padding: 20px 18px;
    background: #f4f1ea;
    border-right: 1px solid #ddd6c8;
    box-sizing: border-box;
  }

  .kicker {
    margin: 0 0 8px;
    font-size: 12px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #6b6458;
  }

  h1 {
    margin: 0 0 20px;
    font-size: 22px;
    line-height: 1.2;
    font-weight: 650;
  }

  label {
    display: block;
    margin-bottom: 6px;
    font-size: 13px;
    font-weight: 600;
  }

  select,
  button {
    width: 100%;
    padding: 8px 10px;
    font: inherit;
    background: #fff;
    border: 1px solid #c9c1b2;
    border-radius: 6px;
  }

  button {
    margin-top: 8px;
    text-align: left;
    cursor: pointer;
  }

  .hint,
  .note {
    margin: 16px 0 0;
    font-size: 14px;
    line-height: 1.45;
    color: #3f3a33;
  }

  .note {
    margin-top: 8px;
    color: #6b6458;
  }
</style>
```

Simpan. Sidebar menampilkan empat basemap dan **Use MVT**. Klik tombol itu dan baris status berubah.

### File yang tidak diubah

| File | Fungsinya |
| --- | --- |
| `src/main.js` | Memuat CSS MapLibre, CSS halaman, dan `App.svelte` ke elemen `#app`. |
| `src/app.css` | Membuat halaman memenuhi jendela. |
| `index.html` | Kerangka HTML. `<div id="app">` yang kosong adalah tempat Svelte menggambar. |
| `vite.config.js` | Menyalakan plugin Svelte untuk Vite. |
| `tiles/server.py` | Membaca `data_mvt/suppliers.mbtiles` dan menjawab `GET /suppliers/{z}/{x}/{y}.mvt`. Kotak tanpa data mengembalikan **204**. |

---

## 8. Berhenti, dan mulai lagi lain kali

Di terminal 2, tekan **Ctrl+C**. Di terminal 1, tekan **Ctrl+C**.

Lain kali Anda membuka proyek, lewati instal dan lewati `npm install`. Dari folder proyek:

Terminal 1, macOS:

```bash
python3 tiles/server.py
```

Terminal 1, Windows:

```bash
python tiles/server.py
```

Terminal 2:

```bash
npm run dev
```

Jalankan `npm install` lagi hanya setelah `package.json` berubah.
