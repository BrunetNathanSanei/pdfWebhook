from flask import Flask
import logging
from pdfWebhook import courtia

app = Flask(__name__)
app.register_blueprint(courtia)

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    app.run(host = "0.0.0.0",port = 5000)
