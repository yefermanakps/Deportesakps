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

# ================= CACHÉ DE EQUIPOS POR COMPETICIÓN =================
teams_cache = {}
CACHE_DURATION = 3600  # 1 hora en segundos

def get_teams_from_competition(competition_code):
    """Obtiene la lista de equipos de una competición y la cachea."""
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
            print(f"Error al obtener equipos de {competition_code}: {response.status_code}")
            return []
    except Exception as e:
        print(f"Excepción en get_teams_from_competition: {e}")
        return []

def buscar_equipo(nombre):
    """
    Busca un equipo por nombre en las principales ligas.
    Devuelve dict con id, nombre y país, o None si no se encuentra.
    """
    # Lista de códigos de competición en orden de prioridad
    competitions = ['PD', 'PL', 'BL1', 'SA', 'FL1']  # La Liga, Premier, Bundesliga, Serie A, Ligue 1
    nombre_lower = nombre.lower()

    for comp in competitions:
        teams = get_teams_from_competition(comp)
        for team in teams:
            # Comparación flexible: si el nombre buscado está contenido en el nombre oficial
            if nombre_lower in team['name'].lower():
                return {
                    'id': team['id'],
                    'nombre': team['name'],
                    'pais': team.get('area', {}).get('name', 'Desconocido')
                }
    return None

def obtener_ultimos_partidos(team_id, num_partidos=5):
    """Obtiene los últimos 'num_partidos' partidos de un equipo."""
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
                    goles_favor = partido['score']['fullTime']['home']
                    goles_contra = partido['score']['fullTime']['away']
                else:
                    goles_favor = partido['score']['fullTime']['away']
                    goles_contra = partido['score']['fullTime']['home']

                if goles_favor > goles_contra:
                    resultados.append('G')
                elif goles_favor < goles_contra:
                    resultados.append('P')
                else:
                    resultados.append('E')
            return resultados
        else:
            print(f"Error obteniendo partidos para {team_id}: {response.status_code}")
            return []
    except Exception as e:
        print(f"Excepción en obtener_ultimos_partidos: {e}")
        return []

def calcular_puntos_forma(resultados):
    """Calcula puntos de forma (3 por victoria, 1 por empate)."""
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
    return jsonify({"mensaje": "API DEPORTES AKPS con football-data.org funcionando"})

@app.route('/buscar/<nombre>')
def buscar(nombre):
    """Ruta de prueba para buscar un equipo por nombre."""
    equipo = buscar_equipo(nombre)
    if equipo:
        return jsonify(equipo)
    else:
        return jsonify({"error": "Equipo no encontrado en la API"}), 404

@app.route('/predecir', methods=['POST'])
def predecir():
    try:
        datos = request.get_json()
        local_nombre = datos.get('local')
        visitante_nombre = datos.get('visitante')

        # 1. Buscar equipos
        local = buscar_equipo(local_nombre)
        visitante = buscar_equipo(visitante_nombre)

        if not local:
            return jsonify({"error": f"Equipo local '{local_nombre}' no encontrado"}), 404
        if not visitante:
            return jsonify({"error": f"Equipo visitante '{visitante_nombre}' no encontrado"}), 404

        # 2. Obtener últimos resultados
        resultados_local = obtener_ultimos_partidos(local['id'])
        resultados_visitante = obtener_ultimos_partidos(visitante['id'])

        puntos_local = calcular_puntos_forma(resultados_local)
        puntos_visitante = calcular_puntos_forma(resultados_visitante)

        # 3. Calcular probabilidades basadas en la forma
        total_puntos = puntos_local + puntos_visitante
        if total_puntos == 0:
            prob_local = 33
            prob_visitante = 33
            prob_empate = 34
        else:
            prob_local = round((puntos_local / total_puntos) * 70)
            prob_visitante = round((puntos_visitante / total_puntos) * 70)
            prob_empate = 100 - prob_local - prob_visitante
            if prob_empate < 0:
                prob_empate = 5
                prob_local = 50
                prob_visitante = 45

        # 4. Determinar ganador
        if prob_local > prob_visitante and prob_local > prob_empate:
            ganador = local['nombre']
        elif prob_visitante > prob_local and prob_visitante > prob_empate:
            ganador = visitante['nombre']
        else:
            ganador = 'Empate'

        # 5. Generar otros campos
        cuota = round(2.0 + (prob_empate / 100), 2)
        alta_baja_etiqueta = 'Alta' if cuota > 2.3 else 'Baja'

        def momento(puntos):
            if puntos >= 10: return 'Excelente'
            elif puntos >= 6: return 'Buena'
            elif puntos >= 3: return 'Regular'
            else: return 'Mala'

        runline = 'Cubre -1.5' if prob_local > 60 else 'No cubre -1.5' if prob_local < 40 else 'Cubre +1.5'

        respuesta = {
            'ganador': ganador,
            'alta_baja': {'valor': cuota, 'etiqueta': alta_baja_etiqueta},
            'momento_equipos': {
                local['nombre']: momento(puntos_local),
                visitante['nombre']: momento(puntos_visitante)
            },
            'favoritismo': {
                'local': prob_local,
                'visitante': prob_visitante,
                'empate': prob_empate
            },
            'runline': runline
        }
        return jsonify(respuesta)

    except Exception as e:
        print(f"Error en /predecir: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
