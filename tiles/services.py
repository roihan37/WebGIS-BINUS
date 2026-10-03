"""Provider adapters for the local WebGIS API."""
import json
import math
import os
import ssl
import subprocess
import time
import threading
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class ProviderError(RuntimeError):
    """Safe, actionable message for upstream connection failures."""


def fetch_json(url, data=None, headers=None):
    request = Request(url, data=data, headers={"User-Agent": "SupplierWebGIS/1.0", **(headers or {})})
    with urlopen(request, timeout=10) as response:
        return json.load(response)


def fetch_route_json(url):
    try:
        return fetch_json(url)
    except (URLError, ssl.SSLError, TimeoutError) as error:
        reason = getattr(error, 'reason', error)
        # Retry only TLS negotiation failures, never bypass certificate checks.
        if isinstance(reason, ssl.SSLError) and not isinstance(reason, ssl.SSLCertVerificationError):
            try:
                result = subprocess.run([
                    'curl', '--fail', '--silent', '--show-error',
                    '--proto', '=https', '--connect-timeout', '5', '--max-time', '15',
                    '--user-agent', 'SupplierWebGIS/1.0', '--url', url
                ], capture_output=True, timeout=17, check=False)
            except FileNotFoundError as exc:
                raise ProviderError('Koneksi TLS layanan lokasi gagal. Instal curl atau perbarui Python pada server.') from exc
            except subprocess.TimeoutExpired as exc:
                raise ProviderError('Layanan lokasi terlalu lama merespons. Coba lagi.') from exc
            if result.returncode:
                raise ProviderError('Koneksi HTTPS ke layanan lokasi gagal. Periksa jaringan server lalu coba lagi.')
            try:
                return json.loads(result.stdout)
            except (ValueError, UnicodeDecodeError) as exc:
                raise ProviderError('Layanan lokasi mengirim respons tidak valid. Coba lagi.') from exc
        if isinstance(reason, ssl.SSLCertVerificationError):
            raise ProviderError('Sertifikat HTTPS layanan lokasi tidak dapat diverifikasi oleh server.') from error
        if isinstance(reason, TimeoutError):
            raise ProviderError('Layanan lokasi terlalu lama merespons. Coba lagi.') from error
        raise ProviderError('Server tidak dapat menghubungi layanan lokasi. Periksa koneksi internet server.') from error


def point(lng, lat):
    lng, lat = float(lng), float(lat)
    if not math.isfinite(lng) or not math.isfinite(lat) or not -180 <= lng <= 180 or not -85 <= lat <= 85:
        raise ValueError("Koordinat tidak valid")
    return [lng, lat]


def feature(identifier, name, coords, kind):
    return {"type": "Feature", "id": str(identifier), "geometry": {"type": "Point", "coordinates": coords},
            "properties": {"name": str(name), "kind": kind}}


def collection(features):
    return {"type": "FeatureCollection", "features": features}


POI_TAGS = {
    'hospital': ['amenity=hospital', 'amenity=clinic'], 'market': ['amenity=marketplace'],
    'warehouse': ['building=warehouse'], 'port': ['landuse=port', 'harbour=yes'],
    'education': ['amenity=school', 'amenity=university', 'amenity=college'],
    'worship': ['amenity=place_of_worship'], 'pharmacy': ['amenity=pharmacy'],
    'fuel': ['amenity=fuel'], 'food': ['amenity=restaurant', 'amenity=cafe'],
    'bank': ['amenity=bank', 'amenity=atm'], 'hotel': ['tourism=hotel', 'tourism=guest_house'],
    'shop': ['shop=supermarket', 'shop=convenience'], 'transport': ['amenity=bus_station', 'railway=station'],
    'parking': ['amenity=parking'], 'police': ['amenity=police']
}
route_lock = threading.Lock()
route_last = 0.0


def fuzzy_search(text):
    url = os.environ.get('PHOTON_URL', 'https://photon.komoot.io/api/')
    data = fetch_route_json(url + '?' + urlencode({'q': text, 'limit': 10}))
    results = []
    for item in data.get('features', []):
        props = item.get('properties', {})
        name = props.get('name') or props.get('street') or props.get('city') or text
        f = feature(str(props.get('osm_type', '')) + str(props.get('osm_id', len(results))), name, point(*item['geometry']['coordinates']), 'search')
        f['properties']['address'] = ', '.join(dict.fromkeys(str(props[k]) for k in ('street', 'district', 'city', 'state', 'country') if props.get(k)))
        results.append(f)
    return collection(results)

def places(query):
    lng, lat = point(query['lng'][0], query['lat'][0])
    radius = int(query.get('radius', ['2000'])[0])
    if not 100 <= radius <= 10000:
        raise ValueError('Radius harus 100–10000 meter')
    kind = query.get('kind', ['hospital'])[0]
    if kind not in POI_TAGS:
        raise ValueError('Kategori tidak valid')
    parts = ''.join(f'nwr(around:{radius},{lat},{lng})[{tag}];' for tag in POI_TAGS[kind])
    q = f'[out:json][timeout:20];({parts});out center 200;'
    data = fetch_route_json(os.environ.get('OVERPASS_URL', 'https://overpass-api.de/api/interpreter') + '?' + urlencode({'data': q}))
    if data.get('remark'):
        raise RuntimeError('Pencarian fasilitas belum selesai; coba radius lebih kecil')
    results = []
    for item in data.get('elements', []):
        center = item.get('center', item)
        if 'lon' not in center or 'lat' not in center:
            continue
        results.append(feature(f"{item['type']}/{item['id']}", item.get('tags', {}).get('name', kind), point(center['lon'], center['lat']), kind))
    for item in results:
        x, y = item['geometry']['coordinates']
        r = math.pi / 180
        a = math.sin((y-lat)*r/2)**2 + math.cos(lat*r)*math.cos(y*r)*math.sin((x-lng)*r/2)**2
        item['properties']['distance'] = round(6371008.8 * 2 * math.asin(min(1, math.sqrt(a))))
    results.sort(key=lambda item: item['properties']['distance'])
    return collection(results)


def route(query):

    start = point(
        query["fromLng"][0],
        query["fromLat"][0]
    )

    end = point(
        query["toLng"][0],
        query["toLat"][0]
    )


    if start == end:
        raise ValueError(
            "Asal dan tujuan harus berbeda"
        )

    mode = query.get('mode', ['car'])[0]
    defaults = {
        'car': ('ROUTING_URL', 'https://router.project-osrm.org/route/v1/driving'),
        'bike': ('ROUTING_BIKE_URL', 'https://routing.openstreetmap.de/routed-bike/route/v1/driving'),
        'foot': ('ROUTING_FOOT_URL', 'https://routing.openstreetmap.de/routed-foot/route/v1/driving')
    }
    if mode not in defaults:
        raise ValueError('Moda belum didukung. Pilih mobil, sepeda, atau jalan kaki.')
    env, default = defaults[mode]
    base = os.environ.get(env, default).rstrip('/')

    url = (
        f"{base}/"
        f"{start[0]},{start[1]};"
        f"{end[0]},{end[1]}"
        "?overview=full&geometries=geojson"
    )


    global route_last
    with route_lock:
        time.sleep(max(0, 1.1 - (time.monotonic() - route_last)))
        route_last = time.monotonic()
        data = fetch_route_json(url)

    if data.get("code") != "Ok" or not data.get("routes"):
        raise ValueError(
            "Rute jalan tidak ditemukan untuk lokasi ini"
        )

    result = data["routes"][0]


    return {
        "type": "Feature",
        "geometry": result["geometry"],
        "properties": {
            "distance": result["distance"],
            "duration": result["duration"],
        }
    }

def company_locations():
    url = os.environ.get('COMPANY_LOCATIONS_URL')
    if not url:
        raise ValueError('API perusahaan belum dikonfigurasi. Atur COMPANY_LOCATIONS_URL pada server.')
    token = os.environ.get('COMPANY_API_TOKEN')
    data = fetch_json(url, headers={'Authorization': f'Bearer {token}'} if token else {})
    if not isinstance(data, dict) or data.get('type') != 'FeatureCollection' or not isinstance(data.get('features'), list):
        raise ValueError('API perusahaan harus mengembalikan GeoJSON FeatureCollection')
    if len(data['features']) > 10000:
        raise ValueError('Maksimal 10000 lokasi per permintaan')
    results = []
    for i, item in enumerate(data['features']):
        geometry = item.get('geometry') or {}
        props = item.get('properties') or {}
        if geometry.get('type') != 'Point' or len(geometry.get('coordinates', [])) != 2:
            raise ValueError('Lokasi perusahaan harus berupa Point [longitude, latitude]')
        kind = props.get('kind', 'supplier')
        if kind not in ('branch', 'customer', 'supplier', 'warehouse'):
            raise ValueError('kind harus branch/customer/supplier/warehouse')
        results.append(feature(item.get('id', i), props.get('name', 'Lokasi perusahaan'), point(*geometry['coordinates']), kind))
    return collection(results)
