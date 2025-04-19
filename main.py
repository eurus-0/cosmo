import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 4000))
    app.run(host="0.0.0.0", port=port)
from app import app  # noqa: F401
from routes import *  # noqa: F401

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000, debug=True)
