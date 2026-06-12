from flask import Flask, request, jsonify
from flask_cors import CORS
import Cortador_planchas as cp  

app = Flask(__name__)
CORS(app)

@app.route('/calcular', methods=['POST'])
def procesar_cortes():
    try:
        datos = request.json
        print("📥 Nuevo cálculo recibido:", datos)
        
        ancho = float(datos['config']['ancho'])
        alto = float(datos['config']['alto'])
        kerf = float(datos['config']['kerf'])
        
        piezas_raw = []
        for p in datos['piezas']:
            piezas_raw.append({
                "nombre": p['nombre'],
                "ancho": float(p['ancho']),
                "alto": float(p['alto']),
                "cantidad": int(p['cantidad']),
                "rotacion_permitida": True  
            })
            
        piezas_listas, mapa, colores = cp.expandir_piezas(piezas_raw)
        planchas_resultados, imposibles = cp.calcular_multiples_planchas(ancho, alto, kerf, piezas_listas)
        
        if not planchas_resultados:
            return jsonify({"error": "Las piezas son demasiado grandes para la plancha."}), 400
            
        primera_plancha = planchas_resultados[0]
        
        cortes_frontend = []
        area_usada = 0
        
        for pieza in primera_plancha:
            cortes_frontend.append({
                "x": pieza["x"],
                "y": pieza["y"],
                "w": pieza["ancho"],
                "h": pieza["alto"],
                "nombre": pieza["nombre"]
            })
            area_usada += (pieza["ancho"] * pieza["alto"])
            
        area_total = ancho * alto
        desperdicio = 100 - ((area_usada / area_total) * 100)
        
        respuesta = {
            "planchas": len(planchas_resultados),
            "desperdicio": round(desperdicio, 1),
            "cortes": cortes_frontend
        }
        
        return jsonify(respuesta)
        
    except Exception as e:
        print("❌ Error en el servidor:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)