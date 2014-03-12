from app import app
from app.settings import HOST, PORT

if __name__ == "__main__":
    app.run(host=HOST, port=int(PORT))