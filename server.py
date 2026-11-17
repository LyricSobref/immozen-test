#!/usr/bin/env python3
"""ImmoZen temporary password-protected test service for Render.

Standard-library Python, HTTPS provided by Render. Not production hardened.
Only allows fetching specific public listing/photo hosts, never bypasses restrictions.
"""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit, quote
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
import json
from urllib.parse import urlencode
import re
import html
import socket
import threading
import time
import webbrowser
import os
import base64
import secrets

HOST = '0.0.0.0'
PORT = int(__import__('os').environ.get('PORT', '10000'))
ROOT = Path(__file__).resolve().parent
PAGE = 'index.html'
MAX_IMAGE = 17_000_000
MAX_MARKDOWN = 1_800_000
MAX_DPE = 9_000_000
USER_AGENT = 'Mozilla/5.0 (compatible; ImmoZenLocalTest/1.0; +http://127.0.0.1)'


def _allowed(name: str, kind: str) -> bool:
    h = (name or '').rstrip('.').lower()
    if not h or any(x in h for x in ('@', ':', '/', '\\')):
        return False
    if kind == 'listing':
        return h in {'bienici.com', 'www.bienici.com'}
    if kind == 'reader':
        return h == 'r.jina.ai'
    if kind == 'dpe':
        return h == 'data.ademe.fr'
    return (
        h in {'file.bienici.com', 'storage.gra.cloud.ovh.net', 'photos.ubiflow.net'}
        or h.endswith('.bienici.com')
        or h.endswith('.ubiflow.net')
        or h.endswith('.apimo.pro')
    )


class _ConstrainedRedirect(HTTPRedirectHandler):
    def __init__(self, kind: str):
        self.kind = kind

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urlsplit(newurl)
        if target.scheme != 'https' or not _allowed(target.hostname or '', self.kind):
            raise ValueError('Redirection vers un domaine non autorisé')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url: str, kind: str, max_bytes: int) -> tuple[bytes, str]:
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or not _allowed(parsed.hostname or '', kind):
        raise ValueError('Adresse distante non autorisée')
    opener = build_opener(_ConstrainedRedirect(kind))
    # No cookies or authentication. A blocked origin stays blocked.
    req = Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'image/avif,image/webp,image/jpeg,image/png,image/*;q=0.8,*/*;q=0.1' if kind == 'image' else 'application/json' if kind == 'dpe' else 'text/markdown,text/html;q=0.9,*/*;q=0.6'})
    with opener.open(req, timeout=14) as response:
        content_type = response.headers.get('Content-Type', '').split(';')[0].lower()
        if kind == 'image' and not content_type.startswith('image/'):
            raise ValueError('Le lien ne renvoie pas une image')
        data = response.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise ValueError('Fichier trop volumineux')
        return data, content_type


def photo_urls(content: str) -> list[str]:
    content = html.unescape(content).replace('\\/', '/')
    candidates = re.findall(r'!\[[^\]]*\]\((https?://[^\s)]+)', content)
    candidates += re.findall(r'<(?:img|source)[^>]+(?:src|srcset)=[\'\"](https?://[^\'\"]+)', content, re.I)
    candidates += re.findall(r'"(?:url|src|image)"\s*:\s*"(https?://[^"]+)"', content, re.I)
    found = []
    seen = set()
    for u in candidates:
        u = u.rstrip(').,')
        # Reader thumbnails can be limited to 600x370; prefer original for OCR.
        if urlsplit(u).hostname == 'file.bienici.com':
            u = u.split('?', 1)[0]
        p = urlsplit(u)
        if p.scheme != 'https' or not _allowed(p.hostname or '', 'image'):
            continue
        if '/photo/' not in p.path and not re.search(r'\.(?:jpe?g|png|webp)$', p.path, re.I):
            continue
        if u not in seen:
            seen.add(u)
            found.append(u)
        if len(found) >= 45:
            break
    return found


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Do not log URLs of individual listings or photo paths to disk.
        print('[ImmoZen]', self.command, self.path.split('?')[0], args[1] if len(args)>1 else '')

    def send_bytes(self, status: int, data: bytes, content_type: str, cache: int = 0):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', f'private, max-age={cache}' if cache else 'no-store')
        if content_type.startswith('text/html'):
            self.send_header('X-ImmoZen-Version', 'v8-progress-candidates-earth')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Referrer-Policy', 'strict-origin-when-cross-origin')
        self.end_headers()
        self.wfile.write(data)

    def error(self, status: int, message: str):
        self.send_bytes(status, json.dumps({'error': message}, ensure_ascii=False).encode('utf-8'), 'application/json; charset=utf-8')

    def do_GET(self):
        # This temporary test server must not expose a public image proxy anonymously.
        expected = os.environ.get('IMMOZEN_TEST_PASSWORD', '')
        if not expected:
            self.error(503, 'Serveur de test non configuré (mot de passe manquant)')
            return
        supplied = self.headers.get('Authorization', '')
        valid = False
        if supplied.startswith('Basic '):
            try:
                value = base64.b64decode(supplied[6:], validate=True).decode('utf-8')
                username, password = value.split(':', 1)
                valid = secrets.compare_digest(username, 'immozen') and secrets.compare_digest(password, expected)
            except (ValueError, UnicodeError):
                valid = False
        if not valid:
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="ImmoZen test prive", charset="UTF-8"')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
        url = urlsplit(self.path)
        if url.path in ('/', '/index.html', '/' + PAGE):
            self.send_bytes(200, (ROOT / PAGE).read_bytes(), 'text/html; charset=utf-8')
            return
        if url.path == '/api/repere.kml':
            qs = parse_qs(url.query)
            try:
                lat = float((qs.get('lat') or [''])[0])
                lon = float((qs.get('lon') or [''])[0])
                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    raise ValueError('Coordonnees hors bornes')
            except (TypeError, ValueError):
                self.error(400, 'Coordonnees invalides')
                return
            # KML uses longitude first, then latitude. This is only a candidate placemark.
            label = html.escape(str((qs.get('label') or ['Position candidate ImmoZen'])[0])[:90])
            kml = (
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>'
                '<name>ImmoZen - repere candidat</name>'
                '<Placemark><name>' + label + '</name>'
                '<description>Localisation candidate : a verifier sur les photographies.</description>'
                '<Point><coordinates>' + f'{lon:.7f},{lat:.7f},0' + '</coordinates></Point>'
                '</Placemark></Document></kml>'
            ).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/vnd.google-earth.kml+xml; charset=utf-8')
            self.send_header('Content-Length', str(len(kml)))
            self.send_header('Content-Disposition', 'attachment; filename="immozen-repere.kml"')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(kml)
            return
        if url.path == '/api/status':
            self.send_bytes(200, b'{"status":"ok","mode":"render-test"}', 'application/json')
            return
        qs = parse_qs(url.query)
        target = (qs.get('url') or [''])[0]
        if url.path == '/api/dpe':
            # Authenticated, narrowly scoped ADEME query; no arbitrary URL passed by clients.
            insee = (qs.get('insee') or [''])[0]
            if not re.fullmatch(r'\d{5}', insee):
                self.error(400, 'Code commune invalide')
                return
            fields = 'conso_5_usages_par_m2_ep,etiquette_dpe,etiquette_ges,surface_habitable_logement,type_batiment,annee_construction,numero_voie_ban,nom_rue_ban,_geopoint,numero_dpe'
            query = urlencode({'size':'2000','select':fields,'qs':'code_insee_ban:'+insee})
            api_url = 'https://data.ademe.fr/data-fair/api/v1/datasets/dpe03existant/lines?' + query
            try:
                # Pagination: otherwise the best address may be on a later ADEME page.
                rows = []
                next_url = api_url
                total = 0
                for page_no in range(5):  # Budget compatible with the free test instance.
                    data, _ = fetch(next_url, 'dpe', MAX_DPE)
                    payload = json.loads(data)
                    total = int(payload.get('total') or 0)
                    rows.extend(payload.get('results') or [])
                    candidate_next = payload.get('next') or ''
                    if not candidate_next or len(rows) >= 9000:
                        break
                    parsed_next = urlsplit(candidate_next)
                    if parsed_next.hostname != 'data.ademe.fr' or '/datasets/' not in parsed_next.path or not parsed_next.path.endswith('/lines'):
                        break
                    next_url = candidate_next
                records = []
                for item in rows:
                    gp = str(item.get('_geopoint') or '').split(',')
                    if len(gp) != 2:
                        continue
                    try:
                        lat, lon = float(gp[0]), float(gp[1])
                        size = float(item.get('surface_habitable_logement') or 0)
                        conso = float(item.get('conso_5_usages_par_m2_ep') or 0)
                    except (ValueError, TypeError):
                        continue
                    if not (40 < lat < 52 and -6 < lon < 11 and 9 < size < 2000):
                        continue
                    typ = str(item.get('type_batiment') or '').lower()
                    typ = 'M' if 'maison' in typ else 'A' if 'appartement' in typ else 'U'
                    address = (str(item.get('numero_voie_ban') or '') + ' ' + str(item.get('nom_rue_ban') or '')).strip()
                    if not address:
                        continue
                    records.append([round(conso), round(size), typ, item.get('annee_construction') or 0,
                        item.get('etiquette_dpe') or '', address, [lon, lat], item.get('etiquette_ges') or '', item.get('numero_dpe') or ''])
                response = {'records': records, 'partial': total > len(rows)}
                self.send_bytes(200, json.dumps(response, ensure_ascii=False).encode('utf-8'), 'application/json; charset=utf-8')
            except (HTTPError, URLError, ValueError, TimeoutError, OSError, json.JSONDecodeError):
                self.error(502, 'Données DPE temporairement indisponibles')
            return
        if url.path == '/api/photo':
            try:
                data, content_type = fetch(target, 'image', MAX_IMAGE)
                self.send_bytes(200, data, content_type, 240)
            except (HTTPError, URLError, ValueError, TimeoutError, OSError) as exc:
                self.error(502, 'Photo indisponible sur le site d’origine')
            return
        if url.path == '/api/annonce':
            try:
                p = urlsplit(target)
                if p.scheme != 'https' or not _allowed(p.hostname or '', 'listing'):
                    raise ValueError('Annonce non autorisée')
                reader = 'https://r.jina.ai/' + target
                try:
                    data, _ = fetch(reader, 'reader', MAX_MARKDOWN)
                except (HTTPError, URLError, ValueError, TimeoutError, OSError):
                    data, _ = fetch(target, 'listing', MAX_MARKDOWN)
                text = data.decode('utf-8', 'replace')
                payload = {'text': text[:120000], 'photos': photo_urls(text)}
                self.send_bytes(200, json.dumps(payload, ensure_ascii=False).encode('utf-8'), 'application/json; charset=utf-8')
            except (HTTPError, URLError, ValueError, TimeoutError, OSError):
                self.error(502, 'L’annonce ne peut pas être consultée automatiquement')
            return
        self.error(404, 'Ressource indisponible')


if __name__ == '__main__':
    if not (ROOT / PAGE).is_file():
        raise SystemExit(f'Fichier absent : {PAGE}')
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f'ImmoZen test — écoute sur le port {PORT}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
