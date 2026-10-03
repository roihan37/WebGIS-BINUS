import unittest
import ssl
import subprocess
from urllib.error import URLError
from unittest.mock import patch
import services

class ServiceTests(unittest.TestCase):
    def test_tls_fallback(self):
        error = URLError(ssl.SSLError('SSLV3_ALERT_HANDSHAKE_FAILURE'))
        with patch.object(services, 'fetch_json', side_effect=error), patch.object(services.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, b'{"code":"Ok"}', b'')) as curl:
            self.assertEqual(services.fetch_route_json('https://example.org/route')['code'], 'Ok')
            self.assertNotIn('--insecure', curl.call_args.args[0])
            self.assertNotIn('-k', curl.call_args.args[0])

    def test_certificate_failure_not_bypassed(self):
        with patch.object(services, 'fetch_json', side_effect=URLError(ssl.SSLCertVerificationError('untrusted'))), patch.object(services.subprocess, 'run') as curl:
            with self.assertRaises(services.ProviderError): services.fetch_route_json('https://example.org')
            curl.assert_not_called()

    def test_network_failure(self):
        with patch.object(services, 'fetch_json', side_effect=URLError('DNS failed')):
            with self.assertRaises(services.ProviderError): services.fetch_route_json('https://example.org')

    def test_vehicle_profiles(self):
        query = {'fromLng': ['106'], 'fromLat': ['-6'], 'toLng': ['107'], 'toLat': ['-7']}
        response = {'code': 'Ok', 'routes': [{'geometry': {'type': 'LineString', 'coordinates': [[106,-6],[107,-7]]}, 'distance': 100, 'duration': 90}]}
        for mode, endpoint in [('bike', 'routed-bike'), ('foot', 'routed-foot')]:
            with patch.object(services, 'fetch_route_json', return_value=response) as fetch, patch.object(services.time, 'sleep'):
                services.route({**query, 'mode': [mode]})
                self.assertIn(endpoint, fetch.call_args.args[0])
        with self.assertRaises(ValueError): services.route({**query, 'mode': ['motorcycle']})

    def test_search_fallback(self):
        import server
        server.geocoder_cache.clear()
        with patch.object(services, 'fetch_route_json', return_value=[]), patch.object(services, 'fuzzy_search', return_value=services.collection([])) as fallback:
            result = server.search_places('pesantren amana')
            self.assertTrue(result['approximate'])
            fallback.assert_called_once_with('pesantren amana')

    def test_facility_distance_order(self):
        with patch.object(services, 'fetch_route_json', return_value={'elements': [
            {'type': 'node', 'id': 1, 'lon': 106.05, 'lat': -6},
            {'type': 'node', 'id': 2, 'lon': 106.001, 'lat': -6}]}):
            data = services.places({'lng': ['106'], 'lat': ['-6'], 'kind': ['education']})
            self.assertEqual(data['features'][0]['id'], 'node/2')

    def test_coordinates(self):
        for point in [(181, 0), (0, 91), (float('nan'), 0)]:
            with self.assertRaises(ValueError): services.point(*point)

    def test_places_centers(self):
        with patch.object(services, 'fetch_json', return_value={'elements': [
            {'type': 'way', 'id': 3, 'center': {'lon': 106, 'lat': -6}, 'tags': {'name': 'RS A'}}]}):
            result = services.places({'lng': ['106'], 'lat': ['-6']})
            self.assertEqual(result['features'][0]['geometry']['coordinates'], [106, -6])
            self.assertEqual(result['features'][0]['properties']['name'], 'RS A')

    def test_invalid_category(self):
        with self.assertRaises(ValueError):
            services.places({'lng': ['106'], 'lat': ['-6'], 'kind': ['invalid']})

    def test_route_and_no_route(self):
        query = {'fromLng': ['106'], 'fromLat': ['-6'], 'toLng': ['107'], 'toLat': ['-7']}
        with patch.object(services, 'fetch_json', return_value={'code': 'Ok', 'routes': [{'geometry': {'type': 'LineString', 'coordinates': [[106,-6],[107,-7]]}, 'distance': 1500, 'duration': 300}]}):
            self.assertEqual(services.route(query)['properties'], {'distance': 1500, 'duration': 300})
        with patch.object(services, 'fetch_json', return_value={'code': 'NoRoute'}):
            with self.assertRaises(ValueError): services.route(query)

    def test_company_token_and_schema(self):
        with patch.dict(services.os.environ, {'COMPANY_LOCATIONS_URL': 'https://company.example/locations', 'COMPANY_API_TOKEN': 'test-token'}):
            with patch.object(services, 'fetch_json', return_value=services.collection([services.feature('1','Branch',[106,-6],'branch')])) as fetch:
                self.assertEqual(services.company_locations()['features'][0]['properties']['kind'], 'branch')
                self.assertEqual(fetch.call_args.kwargs['headers']['Authorization'], 'Bearer test-token')
            with patch.object(services, 'fetch_json', return_value=[]):
                with self.assertRaises(ValueError): services.company_locations()

if __name__ == '__main__': unittest.main()
