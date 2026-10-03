import traceback

import services
import sqlite3
import json
import math
import uuid
import os
import time
import threading
from urllib.parse import parse_qs, urlsplit, urlencode
from urllib.request import Request, urlopen
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DATA_MVT = Path(__file__).resolve().parents[1] / "data_mvt"
MBTILES = DATA_MVT / "suppliers.mbtiles"
SUPPLIERS_DB = DATA_MVT / "custom-suppliers.sqlite"
HOST = "0.0.0.0"
PORT = 8080
TILE_CONTENT_TYPE = "application/vnd.mapbox-vector-tile"


GEOCODER_URL = os.environ.get("GEOCODER_URL", "https://nominatim.openstreetmap.org/reverse")
GEOCODER_AGENT = os.environ.get("GEOCODER_USER_AGENT", "SupplierWebGIS/1.0 (local supplier mapping application)")
geocoder_lock = threading.Lock()
geocoder_cache = {}
geocoder_last_request = 0.0


def reverse_geocode(lat, lng):
    global geocoder_last_request
    if not math.isfinite(lat) or not math.isfinite(lng) or not -85 <= lat <= 85 or not -180 <= lng <= 180:
        raise ValueError("Koordinat tidak valid")
    key = (round(lat, 5), round(lng, 5))
    with geocoder_lock:
        if key in geocoder_cache:
            return geocoder_cache[key]
        time.sleep(max(0, 1.1 - (time.monotonic() - geocoder_last_request)))
        geocoder_last_request = time.monotonic()
        params = urlencode({"lat": key[0], "lon": key[1], "format": "jsonv2", "addressdetails": 1, "accept-language": "id"})
        request = Request(GEOCODER_URL + "?" + params, headers={"User-Agent": GEOCODER_AGENT})
        with urlopen(request, timeout=10) as response:
            data = json.load(response)
        address = data.get("address") or {}
        names = [address.get(k) for k in ("village", "town", "city", "municipality", "county", "state", "country")]
        region = ", ".join(dict.fromkeys(n for n in names if n))
        result = {"region": (region or data.get("display_name", ""))[:200], "address": data.get("display_name", "")}
        if not result["region"]:
            raise ValueError("Alamat tidak ditemukan. Isi wilayah secara manual.")
        if len(geocoder_cache) >= 1000:
            geocoder_cache.pop(next(iter(geocoder_cache)))
        geocoder_cache[key] = result
        return result


def search_places(text):
    global geocoder_last_request
    text = text.strip()
    if not 2 <= len(text) <= 200:
        raise ValueError("Pencarian harus 2–200 karakter")
    key = ("search", text.lower())
    with geocoder_lock:
        if key in geocoder_cache:
            return geocoder_cache[key]
        time.sleep(max(0, 1.1 - (time.monotonic() - geocoder_last_request)))
        geocoder_last_request = time.monotonic()
        url = os.environ.get("GEOCODER_SEARCH_URL", "https://nominatim.openstreetmap.org/search")
        data = services.fetch_route_json(url + "?" + urlencode({"q": text, "format": "jsonv2", "limit": 10, "accept-language": "id"}))
        result = services.collection([services.feature(item['place_id'], item['display_name'], services.point(item['lon'], item['lat']), 'search') for item in data])
        if not result['features']:
            result = services.fuzzy_search(text)
            result['approximate'] = True
        if len(geocoder_cache) >= 1000:
            geocoder_cache.pop(next(iter(geocoder_cache)))
        geocoder_cache[key] = result
        return result


def read_tile(zoom, x, tms_y):
    connection = sqlite3.connect(f"file:{MBTILES}?mode=ro", uri=True)
    try:
        return connection.execute(
            "SELECT tile_data FROM tiles WHERE zoom_level = ? AND tile_column = ? AND tile_row = ?",
            (zoom, x, tms_y),
        ).fetchone()
    finally:
        connection.close()


def supplier_db():
    db = sqlite3.connect(SUPPLIERS_DB)
    db.execute("CREATE TABLE IF NOT EXISTS suppliers (id TEXT PRIMARY KEY, feature TEXT NOT NULL)")
    return db


def validate_supplier(data):
    if not isinstance(data, dict):
        raise ValueError("Data supplier tidak valid")
    for key in ("entityname", "regionlabel"):
        if not isinstance(data.get(key), str) or not data[key].strip() or len(data[key]) > 200:
            raise ValueError("Nama dan wilayah wajib diisi, maksimal 200 karakter")
    for key, low, high in (("lng", -180, 180), ("lat", -85, 85), ("plotareaha", 0, 1e9)):
        value = data.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError("Koordinat atau luas lahan tidak valid")
    identifier = str(uuid.uuid4())
    return {"type": "Feature", "id": identifier,
            "geometry": {"type": "Point", "coordinates": [data["lng"], data["lat"]]},
            "properties": {"FID": identifier, "entityname": data["entityname"].strip(),
                           "regionlabel": data["regionlabel"].strip(), "plotareaha": data["plotareaha"]}}


class TileHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def _send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors()
        self.end_headers()

    def send_json(self, status, data):
        self._send_bytes(status, "application/json; charset=utf-8", json.dumps(data).encode(), False)

    def do_POST(self):
        if self.path.rstrip("/") != "/api/suppliers":
            self.send_json(404, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 8192:
                raise ValueError("Ukuran data tidak valid")
            feature = validate_supplier(json.loads(self.rfile.read(length)))
            with supplier_db() as db:
                db.execute("INSERT INTO suppliers VALUES (?, ?)", (feature["id"], json.dumps(feature)))
            db.close()
            self.send_json(201, feature)
        except (ValueError, UnicodeDecodeError) as error:
            self.send_json(400, {"error": str(error)})
        except sqlite3.Error:
            self.send_json(500, {"error": "Gagal menyimpan supplier"})

    def do_HEAD(self):
        self.do_GET(head_only=True)

    def do_GET(self, head_only=False):
        path = self.path.split("?", 1)[0].rstrip("/")
        if path in (
            "/api/search",
            "/api/places",
            "/api/route",
            "/api/company-locations",
        ):
            try:
                query = parse_qs(urlsplit(self.path).query)

                if path == "/api/search":
                    data = search_places(
                        query.get("q", [""])[0]
                    )

                elif path == "/api/places":
                    data = services.places(query)

                elif path == "/api/route":


                    data = services.route(query)



                else:
                    data = services.company_locations()

                self.send_json(200, data)

            except services.ProviderError as error:
                self.send_json(502, {"error": str(error)})

            except (ValueError, KeyError, IndexError) as error:
                print("BAD REQUEST:", repr(error))

                self.send_json(
                    400,
                    {"error": str(error)}
                )

            except Exception as error:
                print("SERVER ERROR:", repr(error))
                traceback.print_exc()

                self.send_json(
                    502,
                    {
                        "error": "Layanan lokasi gagal merespons.",
                        "detail": str(error)
                    }
                )

            return
        if path == "/api/reverse-geocode":
            try:
                query = parse_qs(urlsplit(self.path).query)
                result = reverse_geocode(float(query["lat"][0]), float(query["lng"][0]))
                self.send_json(200, result)
            except (ValueError, KeyError, IndexError) as error:
                self.send_json(400, {"error": str(error)})
            except Exception:
                self.send_json(502, {"error": "Pencarian alamat gagal. Isi wilayah manual atau coba lagi."})
            return
        if path == "/api/suppliers":
            try:
                with supplier_db() as db:
                    features = [json.loads(row[0]) for row in db.execute("SELECT feature FROM suppliers")]
                db.close()
                self.send_json(200, {"type": "FeatureCollection", "features": features})
            except sqlite3.Error:
                self.send_json(500, {"error": "Gagal membaca supplier"})
            return
        if path in ("", "/"):
            body = b"Supplier tiles:\nGET /suppliers/{z}/{x}/{y}.mvt\n"
            self._send_bytes(200, "text/plain; charset=utf-8", body, head_only)
            return

        parts = path.strip("/").split("/")
        if len(parts) != 4 or parts[0] != "suppliers" or not parts[3].endswith(".mvt"):
            self.send_error(404)
            return

        try:
            zoom = int(parts[1])
            x = int(parts[2])
            y = int(parts[3][: -len(".mvt")])
        except ValueError:
            self.send_error(400)
            return

        tms_y = (1 << zoom) - 1 - y
        row = read_tile(zoom, x, tms_y)

        if not row:
            self.send_response(204)
            self._send_cors()
            self.end_headers()
            return
        self._send_bytes(200, TILE_CONTENT_TYPE, row[0], head_only)

    def _send_bytes(self, status, content_type, body, head_only):
        self.send_response(status)
        self._send_cors()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if not head_only:
            self.wfile.write(body)


def main():
    if not MBTILES.exists():
        raise SystemExit(f"Missing {MBTILES}. The tile file is data_mvt/suppliers.mbtiles in the repo.")
    server = ThreadingHTTPServer((HOST, PORT), TileHandler)
    print(f"Tiles on http://127.0.0.1:{PORT}/suppliers/{{z}}/{{x}}/{{y}}.mvt")
    server.serve_forever()


if __name__ == "__main__":
    main()
