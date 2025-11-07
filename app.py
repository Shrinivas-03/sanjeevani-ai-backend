from app import create_app
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = create_app()
CORS(
    app,
    origins=[
        "http://localhost:3000",
        "http://localhost:19006",
        "http://localhost:8001",
        "http://localhost:8002",
        "*",
    ],
)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
