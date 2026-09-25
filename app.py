import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import io

# ====================================================================
# 🧮 FUNCIONES MATEMÁTICAS Y GEOLÓGICAS (Motor Estadístico Base)
# ====================================================================

def normal_random(mu, sigma):
    """Generador Gaussiano (Equivalente al Box-Muller de VBA)"""
    return float(np.random.normal(mu, sigma))

def log_normal_from_mean_sd(mean, sd):
    """Generador Lognormal para leyes de Oro (Equivalente al de VBA)"""
    if mean <= 0 or sd <= 0:
        return 0.01
    sigma_ln = np.sqrt(np.log(1 + (sd ** 2) / (mean ** 2)))
    mu_ln = np.log((mean ** 2) / np.sqrt(sd ** 2 + mean ** 2))
    return float(np.random.lognormal(mu_ln, sigma_ln))

# ====================================================================
# 💻 CONFIGURACIÓN INTERFAZ WEB (Streamlit)
# ====================================================================
st.set_page_config(page_title="Simulador Geológico 3D Online", layout="wide")

st.title("⚒️ Software de Simulación Geológica y Campañas de Perforación 3D")
st.markdown("---")

# PANEL LATERAL DE CONTROL (UserForm Web)
st.sidebar.header("⚙️ Parámetros del Proyecto")

b_este = st.sidebar.number_input("Coordenada ESTE Base (X):", value=369957)
b_norte = st.sidebar.number_input("Coordenada NORTE Base (Y):", value=6986970)
b_cota = st.sidebar.number_input("ELEVACIÓN / Cota Terreno (Z):", value=2200)
var_cota = st.sidebar.number_input("Rugosidad de Topografía (+/- m):", value=15)
espaciamiento = st.sidebar.number_input("Espaciamiento de Malla (m):", value=40)
cant_sondajes = st.sidebar.number_input("Cantidad Total de Pozos:", value=60, step=10)

tipo_yacimiento = st.sidebar.selectbox(
    "Geometría del Depósito:",
    ["Pórfido Cuprífero (Cilíndrico)", "Cuerpo Masivo / Skarn (Botín)", "Veta Estructural (Tabular)"]
)

tipo_malla = st.sidebar.selectbox(
    "Configuración Geométrica:",
    ["Malla Regular (Grilla)", "Malla Dispersa (Scout Drilling)"]
)

elemento_render = st.sidebar.radio(
    "Visualizar Leyes Metalúrgicas de:",
    ["Cobre (Cu %)", "Oro (Au g/t)"]
)
# ====================================================================
# ⚙️ MOTOR DE CÁLCULO TRIDIMENSIONAL RELACIONAL (CELDAS SEPARADAS)
# ====================================================================

collars = []
assays = []
lithologies = []
surveys = []

dimension_malla = espaciamiento * 20
centro_x = b_este + (dimension_malla / 2)
centro_y = b_norte + (dimension_malla / 2)
centro_z = b_cota - 250

for i in range(1, cant_sondajes + 1):
    pozo_id = f"DDH-{i:03d}"
    
    if tipo_malla == "Malla Regular (Grilla)":
        x = b_este + ((i - 1) % 20) * espaciamiento
        y = b_norte + ((i - 1) // 20) * espaciamiento
    else:
        x = b_este + np.random.rand() * dimension_malla
        y = b_norte + np.random.rand() * dimension_malla
        
    pendiente_x = (x - b_este) * 0.03
    pendiente_y = (y - b_norte) * 0.02
    elev = np.round(b_cota + pendiente_x + pendiente_y + np.random.normal(0, var_cota / 2), 1)
    
    depth = int(250 + np.random.rand() * 150) if tipo_yacimiento == "Veta Estructural (Tabular)" else int(400 + np.random.rand() * 200)
    sobrecarga = int(60 + np.random.rand() * 60)
    
    if tipo_yacimiento == "Veta Estructural (Tabular)":
        azimuth = int(90 + np.random.normal(0, 10))
        dip = int(-50 - np.random.rand() * 15)
    else:
        azimuth = int(np.random.rand() * 360)
        dip = -90 if i % 3 == 0 else int(-60 - np.random.rand() * 15)
        
    # CORRECCIÓN: Separamos estrictamente 'Zona' (19) y 'Hemisferio' (S) en celdas independientes
    collars.append({
        "Nombre": pozo_id,
        "UTM Este": int(x),
        "UTM Norte": int(y),
        "Z_Cota": elev,             
        "Profundidad": depth,        
        "Zona": 19,
        "Hemisferio": "S",
        "Descripcion": "sondajes",
        "Estilo": "Marcador Gota Azul"
    })
    
    surveys.append({"ID": pozo_id, "Depth": depth, "Azimuth": azimuth, "Dip": dip})
    
    rad_azimuth = np.radians(azimuth)
    rad_dip = np.radians(dip)
    
    for j in range(depth // 10):
        from_m = j * 10
        to_m = from_m + 10
        p_medio = from_m + 5
        
        int_x = x + (p_medio * np.cos(rad_dip) * np.sin(rad_azimuth))
        int_y = y + (p_medio * np.cos(rad_dip) * np.cos(rad_azimuth))
        int_z = elev + (p_medio * np.sin(rad_dip))
        
        if from_m < sobrecarga:
            cu, au, lit = 0.0, 0.0, "Overburden"
        else:
            dist_h = np.sqrt((int_x - centro_x)**2 + (int_y - centro_y)**2)
            
            if dist_h < 650:
                cu = np.clip(normal_random(1.2, 0.45), 0.3, 2.5)
                au = np.clip(normal_random(6.0, 2.2), 0.9, 12.0)
                if dist_h < 300:
                    lit = "Quartz_Vein_Core" if "Tabular" in tipo_yacimiento else "Massive_Body_Core"
                else:
                    lit = "Stockwork_Halo" if "Tabular" in tipo_yacimiento else "Mineralized_Breccia"
            else:
                lit = "Country_Rock"
                cu = np.clip(normal_random(0.45, 0.1), 0.3, 0.8)
                au = np.clip(normal_random(2.1, 0.5), 0.9, 3.2)
                
        cu = np.round(max(0.0, cu), 2)
        au = np.round(max(0.0, au), 2)
                
        lithologies.append({"ID": pozo_id, "From": from_m, "To": to_m, "Lithology": lit})
        assays.append({"ID": pozo_id, "From": from_m, "To": to_m, "Cu_pct": cu, "Au_gpt": au})

df_collar = pd.DataFrame(collars)
df_assays = pd.DataFrame(assays)
df_lithology = pd.DataFrame(lithologies)
df_surveys = pd.DataFrame(surveys)
# ====================================================================
# 📋 TABLAS DE DESCARGA E INTEGRACIÓN DE EXCEL REAL NATIVO (.XLSX)
# ====================================================================
st.markdown("---")
st.subheader("📋 Base de Datos del Proyecto (Hojas de Exploración)")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📌 1. Collar", "🧪 2. Assays (Leyes)", "🪨 3. Litología", "📐 4. Surveys", "🌍 5. Convertidor Google Earth"
])

def crear_boton_excel(dataframe, nombre_archivo, ocultar_columnas=None):
    output = io.BytesIO()
    df_salida = dataframe.copy()
    if ocultar_columnas:
        df_salida = df_salida.drop(columns=ocultar_columnas, errors='ignore')
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_salida.to_excel(writer, index=False, sheet_name='Datos_Sondajes')
    st.download_button(
        label=f"📊 Descargar {nombre_archivo}.xlsx",
        data=output.getvalue(),
        file_name=f"{nombre_archivo}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

with tab1:
    st.dataframe(df_collar.drop(columns=["Z_Cota", "Profundidad"]), use_container_width=True, height=220)
    crear_boton_excel(df_collar, "Collar_Sondajes", ocultar_columnas=["Z_Cota", "Profundidad"])
with tab2:
    st.dataframe(df_assays, use_container_width=True, height=220)
    crear_boton_excel(df_assays, "Assays_Leyes")
with tab3:
    st.dataframe(df_lithology, use_container_width=True, height=220)
    crear_boton_excel(df_lithology, "Litologia_Sondajes")
with tab4:
    st.dataframe(df_surveys, use_container_width=True, height=220)
    crear_boton_excel(df_surveys, "Surveys_Trayectorias")

with tab5:
    st.write("### 🛰️ Convertidor Integrado: Carga tu Excel y Genera tu KML")
    st.write("Sube el archivo Excel oficial para transformarlo de manera inmediata al formato georreferenciado compatible con Google Earth Pro.")
    
    archivo_cargado = st.file_uploader(
        "📂 Arrastra aquí tu archivo 'Collar_Sondajes.xlsx' descargado de la pestaña 1:",
        type=["xlsx"]
    )
    
    if archivo_cargado is not None:
        try:
            df_excel_alumno = pd.read_excel(archivo_cargado)
            
            # Verificación de Seguridad Calibrada: Exigimos estrictamente que existan las columnas por separado
            columnas_requeridas = ["Nombre", "UTM Este", "UTM Norte", "Zona", "Hemisferio"]
            if not all(col in df_excel_alumno.columns for col in columnas_requeridas):
                st.error("❌ El archivo Excel subido no tiene la estructura oficial. Debe contener las columnas independientes: Nombre, UTM Este, UTM Norte, Zona, Hemisferio.")
            else:
                st.success("📊 Estructura de Excel verificada con éxito (Celdas de Zona y Hemisferio alineadas). Procesando conversión geodésica para Huso 19S...")
                
                lineas_kml = [
                    '<?xml version="1.0" encoding="UTF-8"?>',
                    '<kml xmlns="http://opengis.net">',
                    '  <Document>',
                    '    <name>Malla de Perforacion Diamantina - Norte de Chile</name>',
                    '    <Style id="marcadorMinero">',
                    '      <IconStyle>',
                    '        <color>ff0000ff</color>',
                    '        <scale>1.2</scale>',
                    '        <Icon>',
                    '          <href>http://google.com</href>',
                    '        </Icon>',
                    '      </IconStyle>',
                    '      <LabelStyle>',
                    '        <scale>0.8</scale>',
                    '      </LabelStyle>',
                    '    </Style>'
                ]

                # Coordenadas geográficas de anclaje base para el Norte Grande de Chile
                lat_chile = -24.250  
                lon_chile = -69.050  
                
                for idx, row in df_excel_alumno.iterrows():
                    x_utm = float(row["UTM Este"])
                    y_utm = float(row["UTM Norte"])
                    p_nombre = str(row["Nombre"])
                    p_desc = str(row["Descripcion"]) if "Descripcion" in df_excel_alumno.columns else "sondajes"
                    
                    # Ecuaciones Geodésicas Transversas de Mercator
                    a = 6378137.0         
                    f = 1 / 298.257223563 
                    b = a * (1 - f)
                    e2 = (a**2 - b**2) / a**2
                    e_prim2 = (a**2 - b**2) / b**2
                    c = a / (1 - f)
                    
                    x_profe = x_utm - 500000.0
                    y_profe = y_utm - 10000000.0 
                    
                    phi = y_profe / (6367449.146)
                    
                    n = c / np.sqrt(1 + e_prim2 * np.cos(phi)**2)
                    m = c / (1 + e_prim2 * np.cos(phi)**2)**1.5
                    t = np.tan(phi)**2
                    psi = e_prim2 * np.cos(phi)**2
                    
                    fact_lat = x_profe / n
                    lat_rad = phi - (fact_lat**2 * np.tan(phi) / 2) * (1 + (fact_lat**2 / 12) * (5 + 3 * t + psi - 9 * t * psi))
                    
                    fact_lon = x_profe / (n * np.cos(phi))
                    lon_rad = fact_lon - (fact_lon**3 / 6) * (1 + 2 * t + psi) + (fact_lon**5 / 120) * (5 + 28 * t + 24 * t**2)
                    
                    lat_decimal = np.degrees(lat_rad)
                    lon_decimal = -69.0 + np.degrees(lon_rad) 
                    
                    lineas_kml.append('    <Placemark>')
                    lineas_kml.append(f'      <name>{p_nombre}</name>')
                    lineas_kml.append('      <description><![CDATA[')
                    lineas_kml.append('        <b>Sondaje Diamantino Profesional</b><br><br>')
                    lineas_kml.append(f'        • Tipo: {p_desc}<br>')
                    lineas_kml.append(f'        • Coordenada Este (X): {x_utm:,.1f} m UTM<br>')
                    lineas_kml.append(f'        • Coordenada Norte (Y): {y_utm:,.1f} m UTM')
                    lineas_kml.append('      ]]></description>')
                    lineas_kml.append('      <styleUrl>#marcadorMinero</styleUrl>')
                    lineas_kml.append('      <Point>')
                    lineas_kml.append('        <altitudeMode>clampToGround</altitudeMode>')
                    lineas_kml.append(f'        <coordinates>{lon_decimal:.7f},{lat_decimal:.7f},0</coordinates>')
                    lineas_kml.append('      </Point>')
                    lineas_kml.append('    </Placemark>')

                lineas_kml.append('  </Document>')
                lineas_kml.append('</kml>')
                
                kml_final_texto = "\n".join(lineas_kml)
                kml_bytes_limpios = bytes(kml_final_texto, "utf-8")
                
                st.markdown("---")
                st.write("#### 🎉 ¡Conversión Completada de Forma Exitosa!")
                
                st.download_button(
                    label="🌍 Descargar Malla_Sondajes_Chile.kml",
                    data=kml_bytes_limpios,
                    file_name="Malla_Sondajes_Chile.kml",
                    mime="application/vnd.google-earth.kml+xml"
                )
                
        except Exception as e:
            st.error(f"❌ Error al procesar el archivo. Detalle técnico: {e}")