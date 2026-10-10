import os
import sys
import socket
from pathlib import Path
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

# Add root folder to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from Backend.config.settings import settings
from Backend.routes import auth_bp, user_bp, hierarchy_bp, report_bp, enem_bp, paaeb_bp, school_bp

FRONTEND_DIR = ROOT_DIR / "Frontend"


def ensure_port_available(port):
    """Fail clearly instead of letting multiple Windows servers share one port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        if sock.connect_ex(("127.0.0.1", port)) == 0:
            raise RuntimeError(f"A porta {port} já está em uso. Encerre o servidor anterior antes de iniciar outro.")

def create_app():
    app = Flask(__name__, static_folder=None)
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register API Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(hierarchy_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(enem_bp)
    app.register_blueprint(paaeb_bp)
    app.register_blueprint(school_bp, url_prefix='/api/schools')

    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "healthy", "service": "Pluraal SaaS API", "version": "1.0.0"}), 200

    # Serve static assets
    @app.route("/assets/<path:filename>")
    def serve_assets(filename):
        return send_from_directory(FRONTEND_DIR / "assets", filename)

    @app.route("/css/<path:filename>")
    def serve_css(filename):
        return send_from_directory(FRONTEND_DIR / "css", filename)

    @app.route("/js/<path:filename>")
    def serve_js(filename):
        return send_from_directory(FRONTEND_DIR / "js", filename)

    # Route for SPA pages
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        if path.startswith("api/"):
            return jsonify({"error": "NOT_FOUND", "message": "Endpoint da API não encontrado."}), 404
        if path and (FRONTEND_DIR / path).exists() and not (FRONTEND_DIR / path).is_dir():
            return send_from_directory(FRONTEND_DIR, path)
        return send_from_directory(FRONTEND_DIR, "index.html")

    return app

if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("SERVER_PORT", 5050))
    ensure_port_available(port)
    print(f"Starting Pluraal Server on http://127.0.0.1:{port}...")
    app.run(host="0.0.0.0", port=port, debug=False)
