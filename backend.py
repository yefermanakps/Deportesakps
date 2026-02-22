from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import requests
import random

app = Flask(__name__)
CORS(app, origins='*')

# --- Configuración de la API de Fútbol ---
API_KEY = '3452c4980b41ab998975fde580bbae4b'  # <--- ¡REEMPLAZA ESTO CON TU CLAVE REAL!
API_URL = 'https://v3.football.api-sports.io'
headers = {
    'x-rapidapi-key': API_KEY,
    'x-rapidapi-host': 'v3.football.api-sports.io'
}

def buscar_equipo(nombre):
    try:
        response = requests.get(f'{API_URL}/teams', headers=headers, params={'search': nombre})
        # Registrar información de la respuesta en los logs
        print(f"🔍 Buscando equipo: {nombre} - Código HTTP: {response.status_code}")
        print(f"📦 Respuesta completa: {response.text}")  # Esto es crucial

        if response.status_code == 200:
            data = response.json()
            print(f"📊 Resultados encontrados: {data['results']}")
            if data['results'] > 0:
                team = data['response'][0]['team']
                return {
                    'id': team['id'],
                    'nombre': team['name'],
                    'pais': team.get('country', '')
                }
            else:
                print(f"⚠️ No se encontraron resultados para: {nombre}")
        else:
            print(f"❌ Error HTTP {response.status_code} al buscar {nombre}")
    except Exception as e:
        print(f"💥 Excepción en buscar_equipo para {nombre}: {e}")
    return None

def obtener_ultimos_resultados(team_id, liga=140, temporada=2024, num_partidos=5):
    """
    Obtiene los últimos 'num_partidos' resultados de un equipo en una liga específica.
    Devuelve una lista con los resultados: 'G' (ganó), 'E' (empató), 'P' (perdió).
    """
    try:
        response = requests.get(
            f'{API_URL}/fixtures',
            headers=headers,
            params={
                'team': team_id,
                'league': liga,
                'season': temporada,
                'last': num_partidos,
                'status': 'FT'  # Solo partidos finalizados
            }
        )
        if response.status_code == 200:
            data = response.json()
            resultados = []
            for partido in data['response']:
                # Determinar si el equipo local o visitante es el nuestro
                if partido['teams']['home']['id'] == team_id:
                    goles_favor = partido['goals']['home']
                    goles_contra = partido['goals']['away']
                else:
                    goles_favor = partido['goals']['away']
                    goles_contra = partido['goals']['home']

                if goles_favor > goles_contra:
                    resultados.append('G')
                elif goles_favor < goles_contra:
                    resultados.append('P')
                else:
                    resultados.append('E')
            return resultados
    except Exception as e:
        print(f"Error obteniendo resultados para equipo {team_id}: {e}")
    return []  # Devolver lista vacía si hay error

def calcular_puntos_forma(resultados):
    """Calcula puntos de forma (3 por victoria, 1 por empate) a partir de una lista de resultados."""
    puntos = 0
    for res in resultados:
        if res == 'G':
            puntos += 3
        elif res == 'E':
            puntos += 1
        # 'P' no suma puntos
    return puntos

def obtener_liga_para_equipo(equipo_nombre):
    """
    Función auxiliar para determinar una liga y temporada por defecto.
    Por simplicidad, usaremos La Liga (ID 140) y temporada 2024.
    En un caso real, esto sería más complejo.
    """
    return 140, 2024

# --- Rutas de la API ---
@app.route('/')
def home():
    return jsonify({"mensaje": "API de DEPORTES AKPS con datos reales"})

@app.route('/buscar/<nombre>')
def buscar(nombre):
    """Ruta de prueba para verificar la búsqueda de equipos."""
    equipo = buscar_equipo(nombre)
    if equipo:
        return jsonify(equipo)
    else:
        return jsonify({"error": "Equipo no encontrado"}), 404

@app.route('/predecir', methods=['POST'])
def predecir():
    datos = request.get_json()
    local_nombre = datos.get('local')
    visitante_nombre = datos.get('visitante')

    # 1. Buscar los equipos en la API
    local = buscar_equipo(local_nombre)
    visitante = buscar_equipo(visitante_nombre)

    if not local or not visitante:
        no_encontrado = []
        if not local:
            no_encontrado.append(local_nombre)
        if not visitante:
            no_encontrado.append(visitante_nombre)
        return jsonify({
            'error': f"No se pudo encontrar el/los equipo(s): {', '.join(no_encontrado)}. Verifica el nombre o prueba con la versión en inglés."
        }), 404

    # 2. Obtener la liga y temporada (simplificado)
    liga_id, temporada = obtener_liga_para_equipo(local['nombre'])

    # 3. Obtener últimos resultados para calcular forma
    resultados_local = obtener_ultimos_resultados(local['id'], liga_id, temporada)
    resultados_visitante = obtener_ultimos_resultados(visitante['id'], liga_id, temporada)

    # 4. Calcular puntos de forma (puedes ajustar el número de partidos)
    puntos_local = calcular_puntos_forma(resultados_local)
    puntos_visitante = calcular_puntos_forma(resultados_visitante)

    # 5. Lógica de predicción simple basada en la forma
    total_puntos = puntos_local + puntos_visitante
    if total_puntos == 0:
        # Si no hay datos, asignamos probabilidades iguales
        prob_local = 33
        prob_visitante = 33
        prob_empate = 34
    else:
        # Probabilidad base proporcional a los puntos de forma
        prob_local = round((puntos_local / total_puntos) * 70)  # Se da un peso del 70% a la forma
        prob_visitante = round((puntos_visitante / total_puntos) * 70)
        # El resto (30%) se asigna al empate y se ajusta
        prob_empate = 100 - prob_local - prob_visitante

    # Determinar el ganador más probable
    if prob_local > prob_visitante and prob_local > prob_empate:
        ganador = local['nombre']
    elif prob_visitante > prob_local and prob_visitante > prob_empate:
        ganador = visitante['nombre']
    else:
        ganador = 'Empate'

    # 6. Generar otros campos del pronóstico (simulados con lógica)
    # Alta/Baja (simulada)
    cuota = round(random.uniform(1.8, 2.8), 2)
    alta_baja_etiqueta = 'Alta' if cuota > 2.3 else 'Baja'

    # Momento del equipo (basado en puntos)
    momento_local = 'Excelente' if puntos_local >= 10 else 'Buena' if puntos_local >= 6 else 'Regular' if puntos_local >= 3 else 'Mala'
    momento_visitante = 'Excelente' if puntos_visitante >= 10 else 'Buena' if puntos_visitante >= 6 else 'Regular' if puntos_visitante >= 3 else 'Mala'

    # Runline (hándicap - simulado)
    runline = random.choice(['Cubre -1.5', 'No cubre -1.5', 'Cubre +1.5'])

    # 7. Construir y devolver la respuesta
    respuesta = {
        'ganador': ganador,
        'alta_baja': {
            'valor': cuota,
            'etiqueta': alta_baja_etiqueta
        },
        'momento_equipos': {
            local['nombre']: momento_local,
            visitante['nombre']: momento_visitante
        },
        'favoritismo': {
            'local': prob_local,
            'visitante': prob_visitante,
            'empate': prob_empate
        },
        'runline': runline,
        'debug': {  # Información adicional para depurar (opcional, puedes eliminarla)
            'puntos_local': puntos_local,
            'puntos_visitante': puntos_visitante,
            'resultados_local': resultados_local,
            'resultados_visitante': resultados_visitante
        }
    }
    return jsonify(respuesta)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
