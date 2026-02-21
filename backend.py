from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import random

app = Flask(__name__)
CORS(app, origins='*')  # Permitir cualquier origen

# Configuración de API-Football
API_KEY = '5b40287de0be64edc597970765e94826'  # <--- REEMPLAZA ESTO
API_URL = 'https://v3.football.api-sports.io'
headers = {
    'x-rapidapi-key': API_KEY,
    'x-rapidapi-host': 'v3.football.api-sports.io'
}

@app.route('/test-api')
def test_api():
    try:
        response = requests.get(f'{API_URL}/status', headers=headers)
        if response.status_code == 200:
            return jsonify({"status": "API conectada", "data": response.json()})
        else:
            return jsonify({"error": f"Error {response.status_code}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
def buscar_equipo(nombre):
    """Busca un equipo por nombre y devuelve su ID y nombre oficial."""
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
        print(f"Error buscando equipo {nombre}: {e}")
    return None

def obtener_estadisticas(team_id, liga, temporada):
    """Obtiene estadísticas de un equipo en una liga específica."""
    try:
        response = requests.get(f'{API_URL}/teams/statistics', headers=headers, params={
            'team': team_id,
            'league': liga,
            'season': temporada
        })
        if response.status_code == 200:
            data = response.json()
            if data['results'] > 0:
                return data['response']
    except Exception as e:
        print(f"Error obteniendo estadísticas: {e}")
    return None

@app.route('/predecir', methods=['POST'])
def predecir():
    datos = request.get_json()
    local_nombre = datos.get('local')
    visitante_nombre = datos.get('visitante')

    # 1. Buscar IDs de los equipos
    local = buscar_equipo(local_nombre)
    visitante = buscar_equipo(visitante_nombre)

    if not local or not visitante:
        return jsonify({'error': 'No se pudo encontrar uno o ambos equipos'}), 404

    # Por simplicidad, usaremos la liga española (ID 140) y temporada 2024
    # En un caso real, deberías detectar la liga automáticamente
    liga_id = 140  # La Liga
    temporada = 2024

    # 2. Obtener estadísticas de los equipos (opcional, por ahora usaremos datos simulados)
    # stats_local = obtener_estadisticas(local['id'], liga_id, temporada)
    # stats_visitante = obtener_estadisticas(visitante['id'], liga_id, temporada)

    # Por ahora, mientras probamos, usaremos datos semi-aleatorios pero con nombres reales
    # Más adelante implementaremos la lógica de predicción basada en estadísticas

    # Simulación mejorada: basada en los nombres reales
    ganador = random.choice([local['nombre'], visitante['nombre'], 'Empate'])
    cuota = round(random.uniform(1.5, 3.0), 2)
    alta_baja = 'Alta' if cuota > 2.2 else 'Baja'
    momentos = {
        local['nombre']: random.choice(['Excelente', 'Buena', 'Regular', 'Mala']),
        visitante['nombre']: random.choice(['Excelente', 'Buena', 'Regular', 'Mala'])
    }
    favoritismo_local = random.randint(30, 70)
    favoritismo_visitante = random.randint(20, 60)
    favoritismo_empate = 100 - favoritismo_local - favoritismo_visitante
    if favoritismo_empate < 0:
        favoritismo_empate = 5
        favoritismo_local = 50
        favoritismo_visitante = 45
    runline = random.choice(['Cubre -1.5', 'No cubre -1.5', 'Cubre +1.5'])

    respuesta = {
        'ganador': ganador,
        'alta_baja': {'valor': cuota, 'etiqueta': alta_baja},
        'momento_equipos': momentos,
        'favoritismo': {
            'local': favoritismo_local,
            'visitante': favoritismo_visitante,
            'empate': favoritismo_empate
        },
        'runline': runline
    }
    return jsonify(respuesta)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
