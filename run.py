from Backend.server import create_app, ensure_port_available
import os

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("SERVER_PORT", 5050))
    ensure_port_available(port)
    print(f"==================================================")
    print(f"  Pluraal SaaS - Servidor Iniciado")
    print(f"  Acesse em: http://127.0.0.1:{port}")
    print(f"==================================================")
    app.run(host="0.0.0.0", port=port, debug=False)
