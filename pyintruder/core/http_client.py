"""Cliente HTTP: parsea peticiones crudas y las envia."""

import http.client
import socket
import ssl
import time

from ..constants import MAX_VIEW_BODY


def parse_raw_request(raw):
    """Extrae metodo, ruta, cabeceras y cuerpo de una peticion cruda."""
    raw = raw.replace("\r\n", "\n")
    if "\n\n" in raw:
        head, body = raw.split("\n\n", 1)
    else:
        head, body = raw, ""
    lines = head.split("\n")
    request_line = lines[0].strip()
    try:
        method, path, _ = request_line.split(" ", 2)
    except ValueError:
        method, path = (request_line.split(" ", 1) + [""])[:2]
    headers = {}
    for line in lines[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip()] = v.strip()
    return method, path, headers, body


def send_request(raw, host, port, use_tls, timeout, update_content_length):
    """Envia la peticion y devuelve un dict:

        status   -> codigo HTTP (int) o None si hubo error
        length   -> longitud del cuerpo de respuesta en bytes
        elapsed  -> tiempo transcurrido en ms
        response -> respuesta cruda completa (estado + cabeceras + cuerpo)
        error    -> None o descripcion del error
    """
    method, path, headers, body = parse_raw_request(raw)
    if update_content_length and body:
        headers["Content-Length"] = str(len(body.encode("utf-8", "ignore")))

    start = time.perf_counter()
    try:
        if use_tls:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE  # laboratorios con certs self-signed
            conn = http.client.HTTPSConnection(host, port, timeout=timeout,
                                               context=ctx)
        else:
            conn = http.client.HTTPConnection(host, port, timeout=timeout)

        # Evita duplicar la cabecera Host (http.client la gestiona).
        send_headers = {k: v for k, v in headers.items() if k.lower() != "host"}
        conn.request(method, path, body=body or None, headers=send_headers)
        resp = conn.getresponse()
        data = resp.read()
        elapsed = (time.perf_counter() - start) * 1000

        version = "HTTP/1.1" if getattr(resp, "version", 11) == 11 else "HTTP/1.0"
        status_line = f"{version} {resp.status} {resp.reason}"
        hdr_lines = "\n".join(f"{k}: {v}" for k, v in resp.getheaders())
        body_text = data.decode("utf-8", "replace")
        if len(body_text) > MAX_VIEW_BODY:
            body_text = (body_text[:MAX_VIEW_BODY] +
                         "\n\n[... respuesta truncada para visualizacion ...]")
        raw_resp = f"{status_line}\n{hdr_lines}\n\n{body_text}"
        conn.close()
        return {"status": resp.status, "length": len(data),
                "elapsed": elapsed, "response": raw_resp, "error": None}
    except (socket.timeout, TimeoutError):
        return {"status": None, "length": 0,
                "elapsed": (time.perf_counter() - start) * 1000,
                "response": "", "error": "timeout"}
    except Exception as e:  # noqa: BLE001 - reportamos cualquier fallo de red
        return {"status": None, "length": 0,
                "elapsed": (time.perf_counter() - start) * 1000,
                "response": "", "error": str(e)}
