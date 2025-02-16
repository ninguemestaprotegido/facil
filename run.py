from app import create_app
import os

app = create_app()

if __name__ == "__main__":
    # Pega a porta definida pelo Railway ou usa a 8080 como padrão
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
