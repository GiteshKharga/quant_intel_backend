import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "false").lower() in ("true", "1", "yes")
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=debug)
