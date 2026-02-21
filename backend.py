from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import random

app = Flask(__name__)
CORS(app)  # Permitir peticiones desde cualquier origen

@app.route('/')
def home():
    return jsonify({
        "mensaje": "API de DEPORTES AKPS funcionando correctamente",
        "estado": "activo",
        "version": "1.0"
    })

@app.route('/predecir', methods=['POST'])
def predecir():
    try:
        # Recibir los datos del partido desde la app
        datos = request.get_json()
        
        if not datos:
            return jsonify({"error": "No se recibieron datos"}), 400
            
        equipo_local = datos.get('local', 'Local')
        equipo_visitante = datos.get('visitante', 'Visitante')

        # SIMULACIÓN: Esto será reemplazado después con datos reales de APIs
        # Por ahora generamos predicciones semi-aleatorias pero consistentes
        
        # 1. Ganador (basado en longitud del nombre para que no sea 100% aleatorio)
        if len(equipo_local) > len(equipo_visitante):
            ganador = equipo_local
        elif len(equipo_visitante) > len(equipo_local):
            ganador = equipo_visitante
        else:
            ganador = 'Empate'

        # 2. Alta/Baja (simulamos una cuota entre 1.5 y 3.0)
        cuota = round(random.uniform(1.5, 3.0), 2)
        alta_baja = 'Alta' if cuota > 2.2 else 'Baja'

        # 3. Momento del equipo
        momentos = {
            equipo_local: random.choice(['Excelente', 'Buena', 'Regular', 'Mala']),
            equipo_visitante: random.choice(['Excelente', 'Buena', 'Regular', 'Mala'])
        }

        # 4. Porcentaje favoritismo
        favoritismo_local = random.randint(30, 70)
        favoritismo_visitante = random.randint(20, 60)
        favoritismo_empate = 100 - favoritismo_local - favoritismo_visitante
        if favoritismo_empate < 0:
            favoritismo_empate = 5
            favoritismo_local = 50
            favoritismo_visitante = 45

        # 5. Posibilidad runline (hándicap)
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
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ¡IMPORTANTE! Esta parte es crucial para que funcione en Render
if __name__ == '__main__':
    # Render asigna el puerto automáticamente mediante la variable de entorno PORT
    port = int(os.environ.get('PORT', 5000))
    # Siempre debe escuchar en 0.0.0.0 para ser accesible desde internet
    app.run(host='0.0.0.0', port=port, debug=False)
