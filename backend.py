from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app, origins='*')

@app.route('/')
def home():
    return jsonify({"mensaje": "API funcionando correctamente"})

@app.route('/test')
def test():
    return "Ruta test OK"

@app.route('/predecir', methods=['POST'])
def predecir():
    datos = request.get_json()
    local = datos.get('local', 'Local')
    visitante = datos.get('visitante', 'Visitante')
    return jsonify({
        "ganador": local,
        "alta_baja": {"valor": 2.1, "etiqueta": "Baja"},
        "momento_equipos": {local: "Excelente", visitante: "Regular"},
        "favoritismo": {"local": 60, "visitante": 30, "empate": 10},
        "runline": "Cubre -1.5"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
