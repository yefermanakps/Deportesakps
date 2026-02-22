from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import requests
import time

app = Flask(__name__)
CORS(app, origins='*')

# ================= CONFIGURACIÓN DE LA API =================
API_TOKEN = '2a6b0d2539cb497abbb64b18fbd11eb2'  # <--- REEMPLAZA CON TU TOKEN
API_URL = 'https://api.football-data.org/v4'
headers = { 'X-Auth-Token': API_TOKEN }

# ================= CACHÉ DE EQUIPOS =================
teams_cache = {}
CACHE_DURATION = 3600  # 1 hora

def get_teams_from_competition(competition_code):
    """Obtiene equipos de una competición con caché."""
    if competition_code in teams_cache:
        data, timestamp = teams_cache[competition_code]
        if time.time() - timestamp < CACHE_DURATION:
            return data
    try:
        response = requests.get(f'{API_URL}/competitions/{competition_code}/teams', headers=headers)
        if response.status_code == 200:
            data = response.json()
            teams = data.get('teams', [])
            teams_cache[competition_code] = (teams, time.time())
            return teams
        else:
            print(f"Error {competition_code}: {response.status_code}")
            return []
    except Exception as e:
        print(f"Excepción en get_teams: {e}")
        return []

def buscar_equipo(nombre):
    """Busca equipo en las principales ligas por coincidencia de nombre."""
    # Ligas: PD (LaLiga), PL (Premier), BL1 (Bundesliga), SA (Serie A), FL1 (Ligue 1)
    competitions = ['PD', 'PL', 'BL1', 'SA', 'FL1']
    nombre_lower = nombre.lower()
    for comp in competitions:
        teams = get_teams_from_competition(comp)
        for team in teams:
            if nombre_lower in team['name'].lower():
                return {
                    'id': team['id'],
                    'nombre': team['name'],
                    'pais': team.get('area', {}).get('name', 'Desconocido')
                }
    return None

def obtener_ultimos_partidos(team_id, num_partidos=5):
    """Últimos partidos de un equipo."""
    try:
        response = requests.get(
            f'{API_URL}/teams/{team_id}/matches',
            headers=headers,
            params={'status': 'FINISHED', 'limit': num_partidos}
        )
        if response.status_code == 200:
            data = response.json()
            resultados = []
            for partido in data['matches']:
                if partido['homeTeam']['id'] == team_id:
                    gf = partido['score']['fullTime']['home']
                    gc = partido['score']['fullTime']['away']
                else:
                    gf = partido['score']['fullTime']['away']
                    gc = partido['score']['fullTime']['home']
                if gf > gc:
                    resultados.append('G')
                elif gf < gc:
                    resultados.append('P')
                else:
                    resultados.append('E')
            return resultados
        else:
            print(f"Error partidos {team_id}: {response.status_code}")
            return []
    except Exception as e:
        print(f"Excepción partidos: {e}")
        return []

def calcular_puntos_forma(resultados):
    puntos = 0
    for r in resultados:
        if r == 'G':
            puntos += 3
        elif r == 'E':
            puntos += 1
    return puntos

# ================= RUTAS =================
@app.route('/')
def home():
    return jsonify({"mensaje": "API DEPORTES AKPS funcionando con football-data.org"})

@app.route('/buscar/<nombre>')
def buscar(nombre):
    equipo = buscar_equipo(nombre)
    if equipo:
        return jsonify(equipo)
    else:
        return jsonify({"error": "Equipo no encontrado"}), 404

@app.route('/predecir', methods=['POST'])
def predecir():
    try:
        datos = request.get_json()
        local_nombre = datos.get('local')
        visitante_nombre = datos.get('visitante')

        local = buscar_equipo(local_nombre)
        visitante = buscar_equipo(visitante_nombre)

        if not local:
            return jsonify({"error": f"Local '{local_nombre}' no encontrado"}), 404
        if not visitante:
            return jsonify({"error": f"Visitante '{visitante_nombre}' no encontrado"}), 404

        res_local = obtener_ultimos_partidos(local['id'])
        res_visit = obtener_ultimos_partidos(visitante['id'])

        pts_local = calcular_puntos_forma(res_local)
        pts_visit = calcular_puntos_forma(res_visit)

        total = pts_local + pts_visit
        if total == 0:
            prob_local = prob_visit = 33
            prob_empate = 34
        else:
            prob_local = round((pts_local / total) * 70)
            prob_visit = round((pts_visit / total) * 70)
            prob_empate = 100 - prob_local - prob_visit
            if prob_empate < 0:
                prob_empate = 5
                prob_local = 50
                prob_visit = 45

        if prob_local > prob_visit and prob_local > prob_empate:
            ganador = local['nombre']
        elif prob_visit > prob_local and prob_visit > prob_empate:
            ganador = visitante['nombre']
        else:
            ganador = 'Empate'

        cuota = round(2.0 + (prob_empate / 100), 2)
        alta_baja = 'Alta' if cuota > 2.3 else 'Baja'

        def momento(puntos):
            if puntos >= 10: return 'Excelente'
            elif puntos >= 6: return 'Buena'
            elif puntos >= 3: return 'Regular'
            else: return 'Mala'

        runline = 'Cubre -1.5' if prob_local > 60 else 'No cubre -1.5' if prob_local < 40 else 'Cubre +1.5'

        respuesta = {
            'ganador': ganador,
            'alta_baja': {'valor': cuota, 'etiqueta': alta_baja},
            'momento_equipos': {
                local['nombre']: momento(pts_local),
                visitante['nombre']: momento(pts_visit)
            },
            'favoritismo': {
                'local': prob_local,
                'visitante': prob_visit,
                'empate': prob_empate
            },
            'runline': runline
        }
        return jsonify(respuesta)
    except Exception as e:
        print(f"Error en /predecir: {e}")
        return jsonify({"error": "Error interno"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
