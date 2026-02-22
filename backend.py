from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import requests
import random

app = Flask(__name__)
CORS(app, origins='*')

# --- Configuración de la API de Fútbol ---
API_KEY = '3452c4980b41ab998975fde580bbae4b'  # <--- ¡REEMPLAZA CON TU CLAVE REAL!
API_URL = 'https://v3.football.api-sports.io'
headers = {
    'x-rapidapi-key': API_KEY,
    'x-rapidapi-host': 'v3.football.api-sports.io'
}

# --- Función de búsqueda de equipos (con logs para depuración) ---
def buscar_equipo(nombre):
    try:
        response = requests.get(f'{API_URL}/teams', headers=headers, params={'search': nombre})
        print(f"[DEBUG] Buscando '{nombre}' - Código HTTP: {response.status_code}")
        print(f"[DEBUG] Respuesta: {response.text}")  # Veremos qué devuelve la API

        if response.status_code == 200:
            data = response.json()
            if data['results'] > 0:
                team = data['response'][0]['team']
                return {
                    'id': team['id'],
                    'nombre': team['name'],
                    'pais': team.get('country', '')
                }
            else:
                print(f"[DEBUG] No se encontraron resultados para '{nombre}'")
        else:
            print(f"[DEBUG] Error HTTP {response.status_code} en la API externa")
    except Exception as e:
        print(f"[DEBUG] Excepción en buscar_equipo: {e}")
    return None

# --- Rutas del backend ---
@app.route('/')
def home():
    return jsonify({"mensaje": "API de DEPORTES AKPS funcionando correctamente"})

@app.route('/test')
def test():
    return "Ruta test OK"

@app.route('/buscar/<nombre>')
def buscar(nombre):
    """Ruta para probar la búsqueda de un equipo."""
    equipo = buscar_equipo(nombre)
    if equipo:
        return jsonify(equipo)
    else:
        return jsonify({"error": "Equipo no encontrado en la API"}), 404

@app.route('/predecir', methods=['POST'])
def predecir():
    datos = request.get_json()
    local_nombre = datos.get('local')
    visitante_nombre = datos.get('visitante')

    # Buscar ambos equipos
    local = buscar_equipo(local_nombre)
    visitante = buscar_equipo(visitante_nombre)

    if not local or not visitante:
        return jsonify({"error": "Uno o ambos equipos no fueron encontrados en la API"}), 404

    # Respuesta de ejemplo con los nombres reales (luego mejoraremos la lógica)
    respuesta = {
        'ganador': local['nombre'],
        'alta_baja': {'valor': 2.1, 'etiqueta': 'Baja'},
        'momento_equipos': {
            local['nombre']: 'Excelente',
            visitante['nombre']: 'Regular'
        },
        'favoritismo': {'local': 60, 'visitante': 30, 'empate': 10},
        'runline': 'Cubre -1.5'
    }
    return jsonify(respuesta)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
