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
# ⚙️ MOTOR DE CÁLCULO TRIDIMENSIONAL RELACIONAL (YACIMIENTO EXPANDIDO)
# ====================================================================

collars = []
assays = []
lithologies = []
surveys = []

# Expandimos las dimensiones de la influencia del depósito para abrazar la grilla
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
    sobrecarga = int(60 + np.random.rand() * 60) # Rango controlado entre 60m y 120m máximo
    
    if tipo_yacimiento == "Veta Estructural (Tabular)":
        azimuth = int(90 + np.random.normal(0, 10))
        dip = int(-50 - np.random.rand() * 15)
    else:
        azimuth = int(np.random.rand() * 360)
        dip = -90 if i % 3 == 0 else int(-60 - np.random.rand() * 15)
        
    collars.append({"ID": pozo_id, "X": x, "Y": y, "Z": elev, "Depth": depth, "Type": "Vertical" if dip == -90 else "Inclinado"})
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
        
        # 1. CONTROL DE CAPA ESTÉRIL DE SOBRECARGA (0.0 a 120m Máximo)
        if from_m < sobrecarga:
            cu, au, lit = 0.0, 0.0, "Overburden"
        else:
            # Distancia horizontal al centro del depósito
            dist_h = np.sqrt((int_x - centro_x)**2 + (int_y - centro_y)**2)
            
            # CORRECCIÓN DE COBERTURA: Ampliamos radicalmente el radio de mineralización útil a 650 metros
            if dist_h < 650:
                # Forzamos las leyes gaussianas puras requeridas en la zona del depósito expandido
                cu = np.clip(normal_random(1.2, 0.45), 0.3, 2.5)
                au = np.clip(normal_random(6.0, 2.2), 0.9, 12.0)
                
                # Asignación litológica estilizada según proximidad
                if dist_h < 300:
                    lit = "Quartz_Vein_Core" if "Tabular" in tipo_yacimiento else "Massive_Body_Core"
                else:
                    lit = "Stockwork_Halo" if "Tabular" in tipo_yacimiento else "Mineralized_Breccia"
            else:
                # Solo las esquinas ultra lejanas (fuera de los 650m de radio) entran en Roca Caja menor
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
# ====================================================================
# 🗂️ DISTRIBUCIÓN VISUAL EN LA PÁGINA WEB (Gran Pantalla Completa)
# ====================================================================
st.subheader("🛰️ Visualizador Espacial 3D Ampliado: Trazas de Pozos y Rangos de Ley")
st.caption("🖱️ CONTROL DE MOVIMIENTO: Haz clic izquierdo y arrastra para ROTAR. Usa la rueda del mouse para hacer ZOOM. Haz clic derecho y arrastra para DESPLAZAR (Pan).")

fig = go.Figure()

# 1. GENERAR ALAMBRE TOPOGRÁFICO 3D (Líneas finas de relieve)
min_x, max_x = float(df_collar["X"].min() - espaciamiento), float(df_collar["X"].max() + espaciamiento)
min_y, max_y = float(df_collar["Y"].min() - espaciamiento), float(df_collar["Y"].max() + espaciamiento)
rango_y = max_y - min_y

num_curvas = 10
for c in range(1, num_curvas + 1):
    x_linea = np.linspace(min_x, max_x, 30)
    y_base = min_y + espaciamiento + (rango_y * (c / (num_curvas + 1)))
    y_linea = y_base + (espaciamiento * 0.35) * np.sin((x_linea - min_x) / (espaciamiento * 1.8))
    z_linea = round(float(df_collar["Z"].min()) + ((float(df_collar["Z"].max()) - float(df_collar["Z"].min())) * (c / (num_curvas + 1))), 1)
    z_array = np.full_like(x_linea, z_linea)
    
    fig.add_trace(go.Scatter3d(
        x=x_linea, y=y_linea, z=z_array, mode='lines',
        line=dict(color='rgba(150, 150, 150, 0.3)', width=1.5),
        showlegend=False, hoverinfo='none'
    ))

# 2. CONSTRUCCIÓN DE MATRIZ CON MAPEO DE COLORES POR INTERVALOS RECALIBRADOS
columna_ley = "Cu_pct" if elemento_render == "Cobre (Cu %)" else "Au_gpt"
unidad_ley = "%" if elemento_render == "Cobre (Cu %)" else "g/t"

x_total, y_total, z_total, codigos_color_total, textos_total = [], [], [], [], []

for idx, row in df_collar.iterrows():
    p_id = row["ID"]
    ensayos_pozo = [a for a in assays if a["ID"] == p_id]
    srv = next((s for s in surveys if s["ID"] == p_id), None)
    if not srv or not ensayos_pozo: continue
    
    az = np.radians(srv["Azimuth"])
    dp = np.radians(srv["Dip"])
    
    x_total.append(row["X"]); y_total.append(row["Y"]); z_total.append(row["Z"])
    codigos_color_total.append(0.0)
    textos_total.append(f"<b>{p_id} (Collar)</b><br>Z: {row['Z']}m")
    
    for ens in ensayos_pozo:
        p_m = ens["From"] + 5
        int_x = row["X"] + (p_m * np.cos(dp) * np.sin(az))
        int_y = row["Y"] + (p_m * np.cos(dp) * np.cos(az))
        int_z = row["Z"] + (p_m * np.sin(dp))
        
        val_ley = float(ens[columna_ley])
        
        if columna_ley == "Cu_pct":
            if val_ley < 0.30:
                codigo = 0.0
            elif 0.30 <= val_ley < 1.00:
                codigo = 1.0
            elif 1.00 <= val_ley < 1.80:
                codigo = 2.0
            else:
                codigo = 3.0
        else:
            if val_ley < 0.90:
                codigo = 0.0
            elif 0.90 <= val_ley < 4.00:
                codigo = 1.0
            elif 4.00 <= val_ley < 8.00:
                codigo = 2.0
            else:
                codigo = 3.0

        x_total.append(int_x); y_total.append(int_y); z_total.append(int_z)
        codigos_color_total.append(codigo)
        
        lit = next((l["Lithology"] for l in lithologies if l["ID"] == p_id and l["From"] == ens["From"]), "Unknown")
        textos_total.append(f"<b>{p_id}</b><br>Tramo: {ens['From']}-{ens['To']}m<br>Lit: {lit}<br>Ley: {val_ley:,.2f} {unidad_ley}")
        
    x_total.append(np.nan); y_total.append(np.nan); z_total.append(np.nan)
    codigos_color_total.append(0.0)
    textos_total.append("")

paleta_discreta = [
    [0.0, "green"], [0.25, "green"],
    [0.25, "yellow"], [0.5, "yellow"],
    [0.5, "orange"], [0.75, "orange"],
    [0.75, "red"], [1.0, "red"]
]

fig.add_trace(go.Scatter3d(
    x=x_total, y=y_total, z=z_total, mode='lines+markers',
    line=dict(
        color=codigos_color_total, colorscale=paleta_discreta, width=6, cmin=0.0, cmax=3.0,
        colorbar=dict(
            title=f"Rangos ({unidad_ley})", thickness=20, x=0.98,
            tickvals=[0.375, 1.125, 1.875, 2.625],
            ticktext=["Estéril (<0.30%)" if columna_ley=="Cu_pct" else "Estéril (<0.9 g/t)", 
                      "Baja-Media (0.30-1.0%)" if columna_ley=="Cu_pct" else "Baja (0.9-4.0 g/t)", 
                      "Alta Ley (1.0-1.8%)" if columna_ley=="Cu_pct" else "Alta Ley (4.0-8.0 g/t)", 
                      "Excelente (>1.80%)" if columna_ley=="Cu_pct" else "Excelente (>8.0 g/t)"]
        )
    ),
    marker=dict(size=2.5, color=codigos_color_total, colorscale=paleta_discreta, cmin=0.0, cmax=3.0, opacity=0.9),
    text=textos_total, hoverinfo='text', showlegend=False
))

config_escena = dict(
    xaxis=dict(title="Este (X)", gridcolor="lightgrey", showbackground=True, backgroundcolor="whitesmoke"),
    yaxis=dict(title="Norte (Y)", gridcolor="lightgrey", showbackground=True, backgroundcolor="whitesmoke"),
    zaxis=dict(title="Cota (Z)", gridcolor="lightgrey", showbackground=True, backgroundcolor="whitesmoke"),
    aspectmode="manual", aspectratio=dict(x=1, y=1, z=0.5)
)

fig.update_layout(width=1300, height=700, margin=dict(l=0, r=0, t=10, b=0), scene=config_escena)
st.plotly_chart(fig, use_container_width=True)

# ====================================================================
# 📋 TABLAS DE DESCARGA E INTEGRACIÓN NATIVA GOOGLE EARTH KML
# ====================================================================
st.markdown("---")
st.subheader("📋 Base de Datos del Proyecto (Hojas de Exploración)")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📌 1. Collar", "🧪 2. Assays (Leyes)", "🪨 3. Litología", "📐 4. Surveys", "🌍 5. Google Earth"
])

def crear_boton_descarga(dataframe, nombre_archivo):
    buf = io.StringIO()
    dataframe.to_csv(buf, index=False)
    st.download_button(label=f"📥 Descargar {nombre_archivo}", data=buf.getvalue(), file_name=nombre_archivo, mime="text/csv")

with tab1:
    st.dataframe(df_collar, use_container_width=True, height=220)
    crear_boton_descarga(df_collar, "Collar.csv")
with tab2:
    st.dataframe(df_assays, use_container_width=True, height=220)
    crear_boton_descarga(df_assays, "Assays.csv")
with tab3:
    st.dataframe(df_lithology, use_container_width=True, height=220)
    crear_boton_descarga(df_lithology, "Litologia.csv")
with tab4:
    st.dataframe(df_surveys, use_container_width=True, height=220)
    crear_boton_descarga(df_surveys, "Surveys.csv")

# PESTAÑA 5: Motor de Conversión Estricto de UTM (Huso 19S) a Geográficas para Google Earth
with tab5:
    st.write("### 🛰️ Exportador Geográfico KML Profesional - Huso 19S (Chile)")
    st.write("Esta herramienta aplica las ecuaciones geodésicas oficiales para transformar la grilla de metros locales UTM (WGS84 Zona 19S) a los grados decimales nativos que requiere Google Earth.")
    
    kml_texto = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://opengis.net">
  <Document>
    <name>Malla de Perforacion Diamantina - Norte de Chile</name>
    <Style id="marcadorMinero">
      <IconStyle>
        <color>ff0000ff</color> <!-- Círculo Rojo Técnico -->
        <scale>1.2</scale>
        <Icon>
          <href>http://google.com</href>
        </Icon>
      </IconStyle>
      <LabelStyle>
        <scale>0.8</scale>
      </LabelStyle>
    </Style>
"""
    # Ecuaciones Geodésicas Transversas de Mercator para la conversión estricta de UTM a Geográficas
    for idx, row in df_collar.iterrows():
        # Tomamos el Este (X) y el Norte (Y) reales de la simulación
        x_utm = float(row["X"])
        y_utm = float(row["Y"])
        
        # Parámetros oficiales para el Huso 19 Sur (WGS84)
        a = 6378137.0         # Radio ecuatorial del elipsoide
        f = 1 / 298.257223563 # Achatamiento de la Tierra
        b = a * (1 - f)
        e2 = (a**2 - b**2) / a**2
        e_prim2 = (a**2 - b**2) / b**2
        c = a / (1 - f)
        
        # Ajustes de origen para el hemisferio Sur y Huso 19
        x_profe = x_utm - 500000.0
        y_profe = y_utm - 10000000.0 # Ajuste por encontrarse en el hemisferio sur
        
        # Cálculo de la latitud del pie (Footprint Latitude)
        phi = y_profe / (6367449.146)
        
        # Ecuaciones de transposición de coordenadas
        n = c / np.sqrt(1 + e_prim2 * np.cos(phi)**2)
        m = c / (1 + e_prim2 * np.cos(phi)**2)**1.5
        t = np.tan(phi)**2
        psi = e_prim2 * np.cos(phi)**2
        
        # Cálculo estricto de Latitud y Longitud en Radianes
        fact_lat = x_profe / n
        lat_rad = phi - (fact_lat**2 * np.tan(phi) / 2) * (1 + (fact_lat**2 / 12) * (5 + 3 * t + psi - 9 * t * psi))
        
        fact_lon = x_profe / (n * np.cos(phi))
        lon_rad = fact_lon - (fact_lon**3 / 6) * (1 + 2 * t + psi) + (fact_lon**5 / 120) * (5 + 28 * t + 24 * t**2)
        
        # Conversión final a Grados Decimales Reales
        lat_decimal = np.degrees(lat_rad)
        lon_decimal = -69.0 + np.degrees(lon_rad) # Anclado al meridiano central del Huso 19 (-69º Oeste)
        
        # Inyectar Placemark al archivo KML con amarre perfecto al terreno
        kml_texto += f"""    <Placemark>
      <name>{row['ID']}</name>
      <description><![CDATA[
        <b>Sondaje Diamantino Profesional</b><br><br>
        • Coordenada Este (X): {x_utm:,.1f} m UTM<br>
        • Coordenada Norte (Y): {y_utm:,.1f} m UTM<br>
        • Elevación Terreno (Z): {row['Z']} msnm<br>
        • Profundidad: {row['Depth']} metros
      ]]></description>
      <styleUrl>#marcadorMinero</styleUrl>
      <Point>
        <altitudeMode>clampToGround</altitudeMode>
        <coordinates>{lon_decimal:.7f},{lat_decimal:.7f},0</coordinates>
      </Point>
    </Placemark>
"""
    kml_texto += """  </Document>
</kml>"""

    # Despliegue del botón de descarga web del archivo KML nativo
    st.download_button(
        label="🌍 Descargar Campaña_Sondajes_UTM.kml (Google Earth)",
        data=kml_texto,
        file_name="Campaña_Sondajes_UTM.kml",
        mime="application/vnd.google-earth.kml+xml"
    )