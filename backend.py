from flask import Flask, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app, origins='*')  # Permitir cualquier origen para pruebas

@app.route('/')
def home():
    return jsonify({"mensaje": "API funcionando correctamente"})

@app.route('/predecir', methods=['POST'])
def predecir():
    # Respuesta de prueba fija para verificar que la ruta funciona
    return jsonify({
        "ganador": "Equipo de prueba",
        "alta_baja": {"valor": 2.1, "etiqueta": "Baja"},
        "momento_equipos": {"Local": "Excelente", "Visitante": "Regular"},
        "favoritismo": {"local": 60, "visitante": 30, "empate": 10},
        "runline": "Cubre -1.5"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
