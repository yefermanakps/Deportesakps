from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import requests

app = Flask(__name__)
CORS(app, origins='*')

API_KEY = '3452c4980b41ab998975fde580bbae4b'  # <--- REEMPLAZA CON TU CLAVE
API_URL = 'https://v3.football.api-sports.io'
headers = {
    'x-rapidapi-key': API_KEY,
    'x-rapidapi-host': 'v3.football.api-sports.io'
}

def buscar_equipo(nombre):
    try:
        response = requests.get(f'{API_URL}/teams', headers=headers, params={'search': nombre})
        if response.status_code == 200:
            data = response.json()
            if data['results'] > 0:
                team = data['response'][0]['team']
                return {
                    'id': team['id'],
                    'nombre': team['name'],
                    'pais': team.get('country', '')
                }
    except Exception as e:
        print(f"Error buscando {nombre}: {e}")
    return None

@app.route('/buscar/<nombre>')
def buscar(nombre):
    equipo = buscar_equipo(nombre)
    if equipo:
        return jsonify(equipo)
    else:
        return jsonify({"error": "Equipo no encontrado"}), 404

@app.route('/')
def home():
    return jsonify({"mensaje": "API funcionando correctamente"})

@app.route('/test')
def test():
    return "Ruta test OK"

@app.route('/predecir', methods=['POST'])
def predecir():
    datos = request.get_json()
    local_nombre = datos.get('local')
    visitante_nombre = datos.get('visitante')

    # Buscar equipos en la API
    local = buscar_equipo(local_nombre)
    visitante = buscar_equipo(visitante_nombre)

    if not local or not visitante:
        return jsonify({'error': 'No se pudo encontrar uno o ambos equipos'}), 404

    # Nombres oficiales
    local_oficial = local['nombre']
    visitante_oficial = visitante['nombre']

    # Por ahora, devolvemos datos de prueba pero con nombres reales
    respuesta = {
        'ganador': local_oficial,  # temporal, luego lo cambiaremos
        'alta_baja': {'valor': 2.1, 'etiqueta': 'Baja'},
        'momento_equipos': {
            local_oficial: 'Excelente',
            visitante_oficial: 'Regular'
        },
        'favoritismo': {'local': 60, 'visitante': 30, 'empate': 10},
        'runline': 'Cubre -1.5'
    }
    return jsonify(respuesta)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
