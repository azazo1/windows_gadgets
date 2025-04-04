import os
import argparse
from pathlib import Path
import requests
from flask import Flask, request, Response
import urllib.parse
import logging

os.chdir(Path(__file__).parent)
app = Flask(__name__)


@app.route("/", methods=["GET"])
def forward_request():
    url = request.args.get("url")
    proxy = request.args.get("proxy")
    if not url:
        return "Missing 'url' parameter", 400
    url = urllib.parse.unquote(url)
    proxies = {}
    if proxy:
        proxies = {"http": proxy, "https": proxy}
    try:
        response = requests.get(url, proxies=proxies)
        return Response(
            response.content,
            status=response.status_code,
            headers={"Content-Type": response.headers.get("Content-Type", "text/html")},
        )
    except requests.exceptions.RequestException as e:
        return str(e), 500


def main():
    file = Path(__file__)
    os.chdir(file.parent)
    log_file = file.with_suffix(".log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    )
    root_logger = logging.getLogger()
    file_handler = logging.FileHandler(filename=log_file, mode="w", encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")
    )
    root_logger.addHandler(file_handler)

    parser = argparse.ArgumentParser(description="Forward URL Proxy Server")
    parser.add_argument(
        "--port",
        type=int,
        default=40211,
        help="Port to run the server on (default: 40211)",
    )
    args = parser.parse_args()
    port = args.port

    logging.info(f"Starting Forward URL Proxy on http://localhost:{port}")
    logging.info(
        f"Example usage: http://localhost:{port}?url=https%3A%2F%2Fgoogle.com&proxy=http%3A%2F%2Flocalhost%3A7890"
    )
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
