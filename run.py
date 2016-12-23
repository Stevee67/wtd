from app import create_app, socket_io
import sys
from config import Config

app = create_app()

if __name__ == '__main__':
    socket_io.run(app, port=int(Config.PORT), host=Config.HOST)
