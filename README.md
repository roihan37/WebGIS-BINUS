# Supplier Atlas — WebGIS

Aplikasi Svelte 4, Vite, dan MapLibre untuk menampilkan supplier dari MVT, menambah lokasi supplier, mencari fasilitas, dan menghitung rute.

## Cara menjalankan secara lokal

Aplikasi membutuhkan **dua terminal yang tetap berjalan**: server Python untuk tile/API dan Vite untuk halaman web. Langkah berikut menggunakan terminal macOS/Linux atau Git Bash.

### 1. Persiapan

Siapkan Node.js 18 atau lebih baru yang kompatibel dengan Vite 5, npm, Python 3, dan curl. Git diperlukan jika mengambil proyek dengan clone.

```bash
node --version
npm --version
python3 --version
curl --version
git --version
```

Pada Windows, gunakan `python` atau `py` sebagai pengganti `python3` jika diperlukan. Jalankan `curl.exe --version` di PowerShell untuk memeriksa curl.

`curl` digunakan sebagai koneksi cadangan apabila adapter API mengalami kegagalan negosiasi TLS melalui Python. Verifikasi sertifikat HTTPS tetap aktif. curl diperlukan pada komputer server, bukan pada perangkat pengguna yang hanya membuka browser. Pembacaan MVT lokal tidak memerlukan curl.

### 2. Masuk ke folder aplikasi

Jika proyek sudah tersedia di workspace `webgis-event`, jalankan dari folder tersebut:

```bash
cd webgis-binus-mapid-svelte
```

Folder yang benar berisi `package.json`, `src`, `tiles`, dan `data_mvt`. Semua perintah berikut dijalankan dari folder ini. Jika sudah berada di sana, jangan menjalankan `cd` lagi.

Jika belum memiliki proyek, repository bahan kelas dapat diambil dengan:

```bash
git clone https://github.com/radenpranantya/webgis-binus-mapid-svelte.git
cd webgis-binus-mapid-svelte
```

Repository bahan kelas belum tentu memuat perubahan Supplier Atlas pada workspace ini. Untuk menjalankan versi yang telah dikembangkan, gunakan salinan proyek terbaru ini.

### 3. Instal dependensi dan konfigurasi basemap

```bash
npm install
```

Hanya jika file `.env` belum ada, salin template berikut. Jangan menimpa `.env` yang sudah berisi konfigurasi Anda.

```bash
cp .env.example .env
```

Pada Windows Command Prompt gunakan `copy .env.example .env`.

Isi `.env` dengan API key MAPID Anda:

```dotenv
VITE_MAPID_KEY=isi_api_key_mapid_anda
```

Jika belum memiliki key, biarkan nilainya kosong: aplikasi memilih basemap Demo sebagai tampilan awal. Basemap MAPID Street, Light, dan Satellite membutuhkan key valid. Setelah mengubah `.env`, restart Vite.

Pastikan `data_mvt/suppliers.mbtiles` tersedia. Server memakai pustaka standar Python; tidak ada langkah `pip install` untuk backend ini.

### 4. Terminal pertama: jalankan server data

```bash
python3 tiles/server.py
```

Server mencetak:

```text
Tiles on http://127.0.0.1:8080/suppliers/{z}/{x}/{y}.mvt
```

Biarkan terminal tetap terbuka. Server melayani tile MVT dan endpoint API pada port **8080**. Membuka `http://127.0.0.1:8080/` menampilkan keterangan endpoint, bukan halaman aplikasi.

### 5. Terminal kedua: jalankan halaman web

Buka terminal baru dan masuk ke folder aplikasi yang sama, lalu jalankan:

```bash
npm run dev -- --host 127.0.0.1
```

Buka **URL yang dicetak Vite**, biasanya `http://127.0.0.1:5173/`. Jika port terpakai, Vite dapat memilih `5174` atau port lain. Biarkan terminal ini tetap berjalan juga.

### 6. Periksa fitur utama

1. Buka tab **Peta**, lalu klik **Tampilkan data supplier**. Teks **Layer supplier diaktifkan** berarti layer diaktifkan, bukan konfirmasi seluruh tile telah selesai dimuat.
2. Gunakan mode **Titik**, lalu klik titik hijau untuk melihat popup nama, FID, luas lahan, dan wilayah.
3. Matikan dan nyalakan switch **Lokasi supplier** untuk menyembunyikan/menampilkan titik.
4. Buka **Analisis** untuk pencarian tempat, fasilitas sekitar, dan rute perjalanan.
5. Untuk menambah data, klik **Tambah supplier**, pilih lokasi di peta atau **Lokasi Saya**, periksa wilayah, isi nama serta luas lahan, lalu simpan.

GPS membutuhkan izin lokasi browser dan akses melalui localhost atau HTTPS. Peta dasar dan layanan pencarian/rute membutuhkan internet. Supplier tambahan disimpan pada `data_mvt/custom-suppliers.sqlite`; pertahankan file ini agar data tidak hilang.

### 7. Berhenti dan menjalankan kembali

Tekan `Ctrl+C` di masing-masing terminal untuk berhenti. Pada penggunaan berikutnya cukup jalankan kembali server Python dan Vite di dua terminal; tidak perlu mengulang `npm install` kecuali dependensi berubah.

- Setelah mengubah kode backend Python: hentikan server dengan `Ctrl+C`, lalu jalankan kembali `python3 tiles/server.py`.
- Setelah mengubah `.env`: hentikan Vite dan jalankan kembali perintah pada langkah 5.
- Setelah server kembali aktif: refresh halaman browser.

### Build dan pemeriksaan

```bash
npm run build
python3 -m unittest discover -s tiles -p 'test_*.py'
```

Untuk melihat hasil build secara lokal:

```bash
npm run preview -- --host 127.0.0.1
```

Buka URL yang dicetak perintah preview. Server Python harus tetap berjalan untuk tile dan API. Preview ini bukan deployment produksi.

### Kendala umum

| Gejala | Tindakan |
| --- | --- |
| `package.json` tidak ditemukan | Masuk ke folder `webgis-binus-mapid-svelte` yang berisi `package.json`. |
| `Missing ... suppliers.mbtiles` | Pastikan file tile tersedia di `data_mvt/suppliers.mbtiles`. |
| Port 8080 sudah digunakan | Periksa terminal server yang sudah berjalan; hentikan server lama jika perlu restart. |
| Titik atau API tidak dapat dimuat | Pastikan server Python berjalan pada port 8080, lalu refresh. |
| Basemap MAPID tidak muncul | Periksa key MAPID; restart Vite setelah perubahan `.env`, atau gunakan basemap Demo. |
| Error koneksi TLS pada layanan rute | Pastikan `curl --version` berhasil pada terminal server; restart backend setelah pembaruan kode. |
| GPS ditolak | Izinkan lokasi di browser dan gunakan localhost atau HTTPS. |
| API perusahaan belum dikonfigurasi | Atur konfigurasi server pada bagian berikut. Fitur lain dapat digunakan tanpa API perusahaan. |

## Lokasi & perjalanan

Restart `python3 tiles/server.py` setelah pembaruan backend.

- **Cari tempat**: ketik alamat, tekan Cari, pilih hasil untuk menuju lokasinya. Tidak ada pencarian otomatis setiap ketikan.
- **Reverse geocoding**: saat form **Tambah supplier** aktif, **Lokasi Saya** atau klik lokasi di peta mengisi koordinat dan mencari wilayah yang dapat diedit. Di luar form, GPS hanya memperbarui lokasi pilihan dan posisi peta.
- **Fasilitas sekitar**: pilih pusat lewat klik peta/hasil/GPS, pilih kategori dan radius, lalu cari. Maksimal 200 hasil; cakupan bergantung OpenStreetMap. Gudang memakai building=warehouse, pelabuhan landuse=port.
- **Rute**: buka **Analisis → Rute perjalanan**, pilih moda **Mobil**, **Sepeda**, atau **Jalan kaki**. Klik **Pilih asal di peta**, pilih titik A, lalu **Pilih tujuan di peta** dan titik B. Tekan **Hitung rute**. Lokasi hasil pencarian/GPS juga dapat ditetapkan sebagai asal atau tujuan. Jarak dalam km dan waktu dalam menit; tanpa lalu lintas langsung atau profil truk.
- **Perusahaan**: tombol Muat memanggil API yang dikonfigurasi di server. Token tidak dikirim ke frontend. Tidak ada data perusahaan contoh yang ditampilkan sebagai data nyata.

### Konfigurasi provider (environment server Python)

Konfigurasi ini dibaca dari environment proses Python. Backend tidak otomatis membaca file `.env` Vite. Pada macOS/Linux, atur dengan `export NAMA_VARIABEL="nilainya"` di terminal server sebelum menjalankan Python. Jangan memakai awalan `VITE_` untuk token rahasia backend.

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
