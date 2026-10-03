# Supplier WebGIS — class

Svelte 4, Vite, and MapLibre. You switch the MAPID basemap, then load supplier points as vector tiles from your own laptop.

The slow GeoJSON demo is not in this folder. That stays on the projector.

You need Node 18 or newer, and Python 3. The tile file `data_mvt/suppliers.mbtiles` comes with the clone.

## Clone

```bash
git clone https://github.com/radenpranantya/webgis-binus-mapid-svelte.git
cd webgis-binus-mapid-svelte/webgis-binus-class
```

## Basemap key

```bash
cp .env.example .env
```

Open `.env` and set `VITE_MAPID_KEY` to the key shown in class. If you change it later, stop `npm run dev` and start it again.

## Tiles

From this folder, in one terminal:

```bash
python3 tiles/server.py
```

Leave it running. It serves `http://127.0.0.1:8080/suppliers/{z}/{x}/{y}.mvt` from the MBTiles in the repo. A missing square returns 204.

## Page

In a second terminal, from this same folder:

```bash
npm install
npm run dev
```

Open the local URL Vite prints (usually `http://127.0.0.1:5173/`).

1. Switch Street, Light, and Satellite.
2. Click **Use MVT**.
3. Pan the map. DevTools → Network shows small `.mvt` requests.
4. Click a green point. Read supplier, plot area, and region.

## Lokasi & perjalanan

Restart `python3 tiles/server.py` setelah pembaruan backend.

- **Cari tempat**: ketik alamat, tekan Cari, pilih hasil untuk menuju lokasinya. Tidak ada pencarian otomatis setiap ketikan.
- **Reverse geocoding**: Lokasi Saya atau pemilihan lokasi supplier mengisi wilayah yang dapat diedit.
- **Fasilitas sekitar**: pilih pusat lewat klik peta/hasil/GPS, pilih kategori dan radius, lalu cari. Maksimal 200 hasil; cakupan bergantung OpenStreetMap. Gudang memakai building=warehouse, pelabuhan landuse=port.
- **Rute**: pilih titik supplier/hasil/klik peta, tekan Jadikan asal; pilih gudang/tujuan dan tekan Jadikan tujuan; Hitung rute. Jarak dalam km dan waktu dalam menit. Estimasi mobil, tanpa lalu lintas langsung atau profil truk.
- **Perusahaan**: tombol Muat memanggil API yang dikonfigurasi di server. Token tidak dikirim ke frontend. Tidak ada data perusahaan contoh yang ditampilkan sebagai data nyata.

### Konfigurasi provider (environment server Python)

`GEOCODER_URL`: endpoint reverse Nominatim-compatible.
`GEOCODER_SEARCH_URL`: endpoint search Nominatim-compatible.
`GEOCODER_USER_AGENT`: identitas aplikasi dan kontak pengelola.
`OVERPASS_URL`: default https://overpass-api.de/api/interpreter.
`ROUTING_URL`: default https://router.project-osrm.org/route/v1/driving.
`COMPANY_LOCATIONS_URL`: URL API perusahaan milik Anda.
`COMPANY_API_TOKEN`: bearer token opsional (simpan di server).

Layanan publik digunakan untuk prototipe dan tidak menjamin ketersediaan. Nominatim membatasi total satu permintaan/detik per aplikasi; search dan reverse berbagi pembatas serta cache pada satu proses server. Jangan menjalankan banyak replika dengan limit terpisah. Baca https://operations.osmfoundation.org/policies/nominatim/ sebelum penggunaan; gunakan provider sendiri/komersial untuk kebutuhan skala lebih besar. Pencarian mengirim alamat/koordinat ke provider. Hindari pengiriman data rahasia ke layanan publik.

API perusahaan wajib mengembalikan GeoJSON berikut (maksimal 10000 titik):

```json
{
  "type": "FeatureCollection",
  "features": [{
    "type": "Feature",
    "id": "cabang-1",
    "geometry": {"type": "Point", "coordinates": [106.8, -6.2]},
    "properties": {"name": "Cabang Jakarta", "kind": "branch"}
  }]
}
```

`kind`: `branch`, `customer`, `supplier`, atau `warehouse`. Koordinat berurutan longitude, latitude. Endpoint API baru: GET `/api/search?q=...`, `/api/places?lng=...&lat=...&radius=2000&kind=hospital`, `/api/route?fromLng=...&fromLat=...&toLng=...&toLat=...`, `/api/company-locations`.

Uji adapter tanpa menghubungi provider: `python3 -m unittest discover -s tiles -p 'test_*.py'`.
Server ini masih merupakan backend lokal tanpa autentikasi; konektor bukan implementasi akses multi-organisasi.

## Pembaruan pencarian dan pengalaman pengguna

- Pencarian nama menerima kota/wilayah opsional, hingga 10 hasil. Bila Nominatim kosong, Photon mencoba pencocokan toleran ejaan; pengguna tetap perlu memeriksa alamat. Permintaan hanya setelah submit, bukan autocomplete Nominatim.
- `PHOTON_URL` mengganti endpoint Photon (default https://photon.komoot.io/api/). Layanan demo Photon hanya untuk penggunaan wajar dan tanpa jaminan ketersediaan: https://github.com/komoot/photon.
- Fasilitas mencakup 15 kategori; hasil diurutkan menurut jarak garis lurus dari pusat, bukan jarak jalan. Maksimal 200 hasil, bukan inventaris lengkap.
- Moda mobil memakai `ROUTING_URL`; sepeda memakai `ROUTING_BIKE_URL`, default https://routing.openstreetmap.de/routed-bike/route/v1/driving; jalan kaki memakai `ROUTING_FOOT_URL`, default https://routing.openstreetmap.de/routed-foot/route/v1/driving. Tiap server memiliki profil berbeda meskipun path API bernama driving. Motor dan truk belum didukung.
- Rute dibatasi satu permintaan per 1,1 detik dalam satu proses server. Ketentuan FOSSGIS: https://routing.openstreetmap.de/about.html.
- Loading/error/retry berada dekat kontrol masing-masing fitur. Batal menghentikan penantian browser; permintaan provider yang sudah berjalan di server mungkin tetap diselesaikan.
- Klik kartu hasil atau titik fasilitas untuk popup; klik garis rute untuk ringkasan perjalanan.
