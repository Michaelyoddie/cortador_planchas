import os  # Necesario para detectar rutas de carpetas en Windows/Mac/Linux
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patches as patches
from matplotlib.table import Table
import matplotlib.cm as cm
import string
from collections import Counter
from typing import List, Dict, Tuple, Any

# ==========================================
# 1. MÓDULO DE UTILIDADES E INTERFAZ (UI)
# ==========================================

def pedir_float(mensaje: str) -> float:
    """Solicita un número decimal y valida que no sea texto ni negativo."""
    while True:
        try:
            val = float(input(mensaje))
            if val <= 0:
                print("⚠️  Por favor ingresa un valor positivo.")
                continue
            return val
        except ValueError:
            print("❌ Ingresa un número válido (ej. 12.5).")

def pedir_int(mensaje: str) -> int:
    """Solicita un número entero y valida la entrada."""
    while True:
        try:
            val = int(input(mensaje))
            if val < 0:
                print("⚠️  El valor no puede ser negativo.")
                continue
            return val
        except ValueError:
            print("❌ Ingresa un número entero.")

def pedir_si_no(mensaje: str) -> bool:
    """Solicita una respuesta de sí o no y retorna un Booleano."""
    while True:
        resp = input(mensaje + " (s/n): ").lower().strip()
        if resp in ["s", "si", "sí"]:
            return True
        elif resp in ["n", "no"]:
            return False
        print("❌ Responde con 's' o 'n'.")



def elegir_dimensiones_plancha() -> Tuple[float, float]:
    """Muestra un menú con dimensiones estándar y permite ingreso manual."""
    print("\n=== 📏 DIMENSIONES DE LA PLANCHA ===")
    print("1. Estándar OSB/Terciado (122 cm x 244 cm)")
    print("2. Estándar Melamina Grande (183 cm x 250 cm)")
    print("3. Ingreso Manual Personalizado")
    
    while True:
        opcion = input("Selecciona una opción (1, 2 o 3): ").strip()
        
        if opcion == "1":
            print("✅ Seleccionado: 122 x 244 cm")
            return 122.0, 244.0
        elif opcion == "2":
            print("✅ Seleccionado: 183 x 250 cm")
            return 183.0, 250.0
        elif opcion == "3":
            ancho = pedir_float("Ancho de la plancha (X) en cm: ")
            alto = pedir_float("Alto de la plancha (Y) en cm: ")
            return ancho, alto
        else:
            print("❌ Opción inválida. Intenta ingresando 1, 2 o 3.")


def elegir_espesor_sierra() -> float:
    """Muestra un menú con grosores de sierra comunes y permite ingreso manual."""
    print("\n=== 🪚 ESPESOR DE LA SIERRA (KERF) ===")
    print("1. Disco estándar (0.5 cm / 5 mm)")
    print("2. Disco fino (0.3 cm / 3 mm)")
    print("3. Ingreso Manual Personalizado")
    
    while True:
        opcion = input("Selecciona una opción (1, 2 o 3): ").strip()
        
        if opcion == "1":
            print("✅ Seleccionado: Disco estándar (0.5 cm)")
            return 0.5
        elif opcion == "2":
            print("✅ Seleccionado: Disco fino (0.3 cm)")
            return 0.3
        elif opcion == "3":
            return pedir_float("Ingresa el grosor exacto de la sierra en cm: ")
        else:
            print("❌ Opción inválida. Intenta ingresando 1, 2 o 3.")




def obtener_datos_usuario() -> Dict[str, Any]:
    """
    Función principal de interacción por consola.
    Retorna un diccionario con la configuración de la plancha y la lista de piezas.
    """
    print("\n=== ⚙️  CONFIGURACIÓN DE LA PLANCHA ===")
    # Llamamos al nuevo menú
    ancho_plancha, alto_plancha = elegir_dimensiones_plancha()
    
    kerf = pedir_float("\nEspacio de corte (kerf/grosor de la sierra) en cm: ")
    permitir_rotacion = pedir_si_no("¿Permitir rotación de piezas para encajar mejor?")

    print("\n=== 📦 INGRESO DE PIEZAS A CORTAR ===")
    print("Escribe 'terminar' en el nombre para finalizar el ingreso.\n")
    
    piezas = []
    
    while True:
        nombre = input("Nombre de la pieza: ").strip()
        # Condición de salida del bucle
        if nombre.lower() == "terminar":
            if not piezas:
                print("⚠️  Debes ingresar al menos una pieza.")
                continue
            break
            
        cantidad = pedir_int(f"Cantidad de '{nombre}': ")
        ancho = pedir_float("Ancho (cm): ")
        alto  = pedir_float("Alto (cm): ")
        
        # Lógica para permitir rotación global o restringirla por pieza
        rotar_pieza = permitir_rotacion
        if permitir_rotacion:
            if not pedir_si_no(f"¿La pieza '{nombre}' se puede rotar?"):
                rotar_pieza = False

        piezas.append({
            "nombre": nombre,
            "cantidad": cantidad,
            "ancho": ancho,
            "alto": alto,
            "rotacion_permitida": rotar_pieza
        })

    return {
        "plancha": (ancho_plancha, alto_plancha),
        "kerf": kerf,
        "piezas": piezas
    }

# ==========================================
# 2. MÓDULO DE LÓGICA DE NEGOCIO (CORE)
# ==========================================

def expandir_piezas(piezas_raw: List[Dict]) -> Tuple[List[Dict], Dict, Dict]:
    """
    Convierte la entrada 'Agrupada' (ej: 5 sillas) en una lista 'Plana'
    (ej: silla_1, silla_2, silla_3...). Asigna IDs y colores únicos por tipo.
    """
    piezas_individuales = []
    mapa_leyenda = {} # Para saber qué letra corresponde a qué nombre en el PDF
    colores = {}
    
    abc = list(string.ascii_uppercase)
    # Usamos un mapa de colores "tab20" que tiene 20 colores distintivos
    cmap = plt.get_cmap('tab20')

    idx_global = 0
    for i, p in enumerate(piezas_raw):
        # Asignar letra (A, B, C...) o P1, P2 si se acaban las letras
        letra = abc[i] if i < len(abc) else f"P{i}"
        color = cmap(i % 20)
        
        mapa_leyenda[letra] = {
            "nombre": p["nombre"],
            "dims": f"{p['ancho']}x{p['alto']}"
        }
        colores[letra] = color

        # Crear copias individuales según la cantidad solicitada
        for _ in range(p["cantidad"]):
            piezas_individuales.append({
                "id": idx_global,
                "letra": letra,
                "nombre": p["nombre"],
                "ancho": p["ancho"],
                "alto": p["alto"],
                "rotacion": p["rotacion_permitida"]
            })
            idx_global += 1
            
    # OPTIMIZACIÓN IMPORTANTE:
    # Ordenar las piezas de mayor a menor área ayuda al algoritmo a llenar
    # los huecos grandes primero y usar las piezas pequeñas para rellenar.
    piezas_individuales.sort(key=lambda x: x["ancho"] * x["alto"], reverse=True)
    
    return piezas_individuales, mapa_leyenda, colores

def verificar_colision(candidato: Dict, colocadas: List[Dict], kerf: float) -> bool:
    """
    Verifica si un rectángulo 'candidato' se superpone con alguno de la lista 'colocadas'.
    Considera el 'kerf' (grosor de la sierra) como parte del espacio ocupado.
    """
    cx, cy, cw, ch = candidato["x"], candidato["y"], candidato["ancho"], candidato["alto"]
    
    for otra in colocadas:
        ox, oy, ow, oh = otra["x"], otra["y"], otra["ancho"], otra["alto"]
        
        # Matemáticamente, dos rectángulos NO se tocan si están separados
        # totalmente a la izquierda, derecha, arriba o abajo.
        # Aquí comprobamos lo contrario (si se tocan).
        no_solapa = (cx + cw + kerf <= ox) or \
                    (ox + ow + kerf <= cx) or \
                    (cy + ch + kerf <= oy) or \
                    (oy + oh + kerf <= cy)
        
        if not no_solapa:
            return True # ¡Chocan!
            
    return False

def calcular_cortes_una_plancha(ancho_plancha: float, alto_plancha: float, kerf: float, piezas_pendientes: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    Intenta colocar el máximo número de piezas pendientes en UNA sola plancha.
    Utiliza una heurística de 'Puntos Candidatos' (Bottom-Left).
    """
    colocadas = []
    no_colocadas = []

    for pieza in piezas_pendientes:
        colocada_flag = False
        
        # Puntos donde tiene sentido intentar poner una pieza:
        # 1. El origen (0,0)
        # 2. Justo a la derecha de una pieza existente
        # 3. Justo arriba de una pieza existente
        puntos_candidatos = [(0.0, 0.0)]
        for p in colocadas:
            puntos_candidatos.append((p["x"] + p["ancho"] + kerf, p["y"]))
            puntos_candidatos.append((p["x"], p["y"] + p["alto"] + kerf))
        
        # Ordenamos los puntos: preferimos abajo (Y menor) y luego izquierda (X menor)
        puntos_candidatos.sort(key=lambda pos: (pos[1], pos[0]))
        
        # Probamos cada punto candidato
        for x, y in puntos_candidatos:
            # Optimización: Si el punto de inicio ya está fuera, ni lo intentamos
            if x >= ancho_plancha or y >= alto_plancha:
                continue

            # Definimos orientaciones: Normal y (si se permite) Rotada
            orientaciones = [(pieza["ancho"], pieza["alto"])]
            if pieza["rotacion"]:
                orientaciones.append((pieza["alto"], pieza["ancho"]))
            
            # Usamos 'set' para evitar probar lo mismo dos veces si la pieza es cuadrada
            for w, h in set(orientaciones): 
                # 1. ¿Cabe en la plancha?
                if x + w > ancho_plancha or y + h > alto_plancha:
                    continue
                
                # 2. ¿Choca con otras piezas?
                candidato = {"x": x, "y": y, "ancho": w, "alto": h}
                if not verificar_colision(candidato, colocadas, kerf):
                    # Si pasa las pruebas, guardamos la pieza
                    pieza_final = pieza.copy()
                    pieza_final.update(candidato)
                    colocadas.append(pieza_final)
                    colocada_flag = True
                    break # Salimos del bucle de rotaciones
            
            if colocada_flag:
                break # Salimos del bucle de puntos, pasamos a la siguiente pieza
        
        if not colocada_flag:
            no_colocadas.append(pieza) # No cupo en esta hoja

    return colocadas, no_colocadas

def calcular_multiples_planchas(ancho, alto, kerf, todas_las_piezas):
    """
    Orquestador principal:
    Llama al cálculo de una plancha, guarda el resultado, toma las sobras
    y crea una nueva plancha hasta que no queden piezas.
    """
    planchas_resultados = [] # Lista de listas (Página 1, Página 2...)
    pendientes = todas_las_piezas
    imposibles = []

    max_planchas = 100 # Límite de seguridad para evitar bucles infinitos
    
    while pendientes and len(planchas_resultados) < max_planchas:
        # Intentamos llenar una hoja con lo que tengamos pendiente
        colocadas, restantes = calcular_cortes_una_plancha(ancho, alto, kerf, pendientes)
        
        # Si no colocamos NADA y todavía sobran cosas, significa que la pieza es
        # más grande que la plancha vacía. Es un error físico.
        if not colocadas and restantes:
            print(f"⚠️  La pieza '{restantes[0]['nombre']}' es demasiado grande para la plancha. Se omite.")
            imposibles.append(restantes[0])
            pendientes = restantes[1:] # Saltamos esa pieza y seguimos
            continue

        planchas_resultados.append(colocadas)
        pendientes = restantes # Las que sobraron pasan a la siguiente vuelta

    return planchas_resultados, imposibles

# ==========================================
# 3. MÓDULO DE REPORTE Y VISUALIZACIÓN
# ==========================================

def generar_pdf_multipage(filename: str, ancho_plancha: float, alto_plancha: float, 
                          planchas_resultados: List[List[Dict]], imposibles: List[Dict], 
                          mapa_leyenda: Dict, colores: Dict):
    """
    Genera un PDF con múltiples páginas, una por cada plancha calculada.
    """
    
    with PdfPages(filename) as pdf:
        total_planchas = len(planchas_resultados)

        for i, colocadas in enumerate(planchas_resultados):
            # Crear figura gráfica
            fig, ax = plt.subplots(figsize=(16, 10))
            
            ax.set_title(f"Plancha {i+1} de {total_planchas}", fontsize=18, pad=20)
            ax.set_xlim(0, ancho_plancha)
            ax.set_ylim(0, alto_plancha)
            ax.set_aspect('equal') # Mantiene la proporción visual real (cuadrados se ven cuadrados)
            ax.set_xlabel("Ancho (cm)")
            ax.set_ylabel("Alto (cm)")

            # Dibujar el fondo de la plancha
            border = patches.Rectangle((0, 0), ancho_plancha, alto_plancha, 
                                     linewidth=3, edgecolor='navy', facecolor='#f9f9f9', zorder=0)
            ax.add_patch(border)

            # Dibujar cada pieza colocada
            for p in colocadas:
                rect = patches.Rectangle(
                    (p["x"], p["y"]), p["ancho"], p["alto"],
                    linewidth=1, edgecolor='black', facecolor=colores[p["letra"]], alpha=0.9, zorder=10
                )
                ax.add_patch(rect)
                
                # Etiqueta dentro de la pieza (solo si es lo bastante grande)
                if p["ancho"] > 2 and p["alto"] > 2:
                    texto = f"{p['letra']}\n{p['ancho']:.1f}x{p['alto']:.1f}"
                    ax.text(p["x"] + p["ancho"]/2, p["y"] + p["alto"]/2, texto,
                            ha='center', va='center', fontsize=8, color='white', fontweight='bold', zorder=11)

            # Grilla suave de fondo
            ax.grid(True, linestyle='--', alpha=0.3)

            # --- GENERACIÓN DE TABLA LATERAL ---
            # Solo listamos las piezas que están en ESTA hoja específica
            cell_text = []
            piezas_en_hoja = [p["letra"] for p in colocadas]
            conteo = Counter(piezas_en_hoja)
            
            letras_ordenadas = sorted(set(piezas_en_hoja))
            
            for letra in letras_ordenadas:
                info = mapa_leyenda[letra]
                cell_text.append([letra, info["nombre"], info["dims"], conteo[letra]])

            col_labels = ["ID", "Nombre", "Medidas", "Cant."]
            tabla = Table(ax, bbox=[1.02, 0.1, 0.3, 0.8]) # Posición a la derecha
            
            # Estilo de encabezados
            for col_idx, label in enumerate(col_labels):
                cell = tabla.add_cell(0, col_idx, 0.1, 0.05, text=label, loc='center', facecolor='#dddddd')
                cell.get_text().set_weight('bold')

            # Llenar celdas de datos
            for row_idx, row_data in enumerate(cell_text, start=1):
                for col_idx, val in enumerate(row_data):
                    color_celda = 'white'
                    # Coloreamos la columna ID igual que la pieza en el mapa
                    if col_idx == 0: color_celda = colores[val]
                    
                    cell = tabla.add_cell(row_idx, col_idx, 0.1, 0.05, text=str(val), loc='center', facecolor=color_celda)
                    
                    if col_idx == 0: # Texto blanco si el fondo es de color
                        cell.get_text().set_color('white')
                        cell.get_text().set_weight('bold')

            ax.add_table(tabla)
            
            # Calcular eficiencia de esta hoja
            area_total = ancho_plancha * alto_plancha
            area_usada = sum(p["ancho"] * p["alto"] for p in colocadas)
            eficiencia = (area_usada / area_total) * 100
            
            resumen = f"Eficiencia Plancha {i+1}: {eficiencia:.1f}%"
            props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            ax.text(1.02, 0.98, resumen, transform=ax.transAxes, fontsize=12, verticalalignment='top', bbox=props)

            plt.subplots_adjust(left=0.05, right=0.75) # Ajuste márgenes
            pdf.savefig(fig) # Guardar página actual
            plt.close()
            
        # Si hubo piezas imposibles, agregamos una página final de reporte de error
        if imposibles:
            fig, ax = plt.subplots()
            ax.axis('off')
            ax.text(0.5, 0.5, "PIEZAS QUE NO CUPIERON EN NINGUNA PLANCHA\n(Probablemente más grandes que la plancha madre)", 
                    ha='center', fontsize=14, color='red')
            lista_err = "\n".join([f"- {p['nombre']} ({p['ancho']}x{p['alto']})" for p in imposibles])
            ax.text(0.5, 0.3, lista_err, ha='center', fontsize=12)
            pdf.savefig(fig)
            plt.close()

# ==========================================
# 4. MAIN (EJECUCIÓN)
# ==========================================

def main():
    # 1. Obtener datos del usuario
    datos = obtener_datos_usuario()
    ancho_plancha, alto_plancha = datos["plancha"]
    
    # 2. Expandir datos para cálculo
    piezas_listas, mapa, colores = expandir_piezas(datos["piezas"])
    
    print(f"\n🧠 Calculando distribución para {len(piezas_listas)} piezas...")
    
    # 3. Calcular distribución en múltiples hojas
    planchas_resultados, imposibles = calcular_multiples_planchas(
        ancho_plancha, 
        alto_plancha, 
        datos["kerf"], 
        piezas_listas
    )
    
    # 4. Mostrar resumen en consola
    print(f"\n✅ Cálculo finalizado.")
    print(f"📦 Se necesitan un total de: {len(planchas_resultados)} PLANCHA(S).")
    
    if imposibles:
        print(f"⚠️  Hay {len(imposibles)} piezas que son físicamente imposibles de cortar (revisar tamaño).")

    # 5. Detectar ruta del escritorio automáticamente (Cross-platform)
    user_home = os.path.expanduser("~") # Directorio 'Home' del usuario
    ruta_escritorio = os.path.join(user_home, "Desktop")
    
    # Verificar si es en español
    if not os.path.exists(ruta_escritorio):
        ruta_escritorio = os.path.join(user_home, "Escritorio")
    
    # Si falla todo, usar directorio actual
    if not os.path.exists(ruta_escritorio):
        ruta_escritorio = "."

    nombre_archivo = os.path.join(ruta_escritorio, "resultado_cortes_multiples.pdf")
    
    # 6. Generar el archivo final
    generar_pdf_multipage(nombre_archivo, ancho_plancha, alto_plancha, planchas_resultados, imposibles, mapa, colores)
    print(f"\n📄 Reporte multipágina generado en: {nombre_archivo}")

# Punto de entrada estándar de Python
if __name__ == "__main__":
    main()