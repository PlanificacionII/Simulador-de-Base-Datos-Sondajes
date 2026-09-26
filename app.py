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

# PANEL LATERAL DE CONTROL (UserForm Web de Excel)
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
    sobrecarga = int(60 + np.random.rand() * 60) # Rango controlado entre 60m y 120m máximo
    
    if tipo_yacimiento == "Veta Estructural (Tabular)":
        azimuth = int(90 + np.random.normal(0, 10))
        dip = int(-50 - np.random.rand() * 15)
    else:
        azimuth = int(np.random.rand() * 360)
        dip = -90 if i % 3 == 0 else int(-60 - np.random.rand() * 15)
        
    # INTEGRACIÓN: Armamos la estructura de columnas idéntica a tu imagen de Excel
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
        
        # 1. CONTROL DE CAPA ESTÉRIL DE SOBRECARGA (0.0 a 120m Máximo)
        if from_m < sobrecarga:
            cu, au, lit = 0.0, 0.0, "Overburden"
        else:
            # Distancia horizontal al centro del depósito
            dist_h = np.sqrt((int_x - centro_x)**2 + (int_y - centro_y)**2)
            
            # COBERTURA AMPLIA: Radio de mineralización útil a 650 metros
            if dist_h < 650:
                # Forzamos las leyes gaussianas puras requeridas en la zona del depósito
                cu = np.clip(normal_random(1.2, 0.45), 0.3, 2.5)
                au = np.clip(normal_random(6.0, 2.2), 0.9, 12.0)
                
                if dist_h < 300:
                    lit = "Quartz_Vein_Core" if "Tabular" in tipo_yacimiento else "Massive_Body_Core"
                else:
                    lit = "Stockwork_Halo" if "Tabular" in tipo_yacimiento else "Mineralized_Breccia"
            else:
                # Esquinas ultra lejanas (fuera de los 650m de radio) entran en Roca Caja menor
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
# 🗂️ DISTRIBUCIÓN VISUAL EN LA PÁGINA WEB (Gran Pantalla Completa)
# ====================================================================
st.subheader("🛰️ Visualizador Espacial 3D Ampliado: Trazas de Pozos y Rangos de Ley")
st.caption("🖱️ CONTROL DE MOVIMIENTO: Haz clic izquierdo y arrastra para ROTAR. Usa la rueda del mouse para hacer ZOOM. Haz clic derecho y arrastra para DESPLAZAR (Pan).")

fig = go.Figure()

# 1. GENERAR ALAMBRE TOPOGRÁFICO 3D (Líneas finas de relieve)
min_x = float(df_collar["UTM Este"].min() - espaciamiento)
max_x = float(df_collar["UTM Este"].max() + espaciamiento)
min_y = float(df_collar["UTM Norte"].min() - espaciamiento)
max_y = float(df_collar["UTM Norte"].max() + espaciamiento)
rango_y = max_y - min_y

num_curvas = 10
for c in range(1, num_curvas + 1):
    x_linea = np.linspace(min_x, max_x, 30)
    y_base = min_y + espaciamiento + (rango_y * (c / (num_curvas + 1)))
    y_linea = y_base + (espaciamiento * 0.35) * np.sin((x_linea - min_x) / (espaciamiento * 1.8))
    z_linea = round(float(df_collar["Z_Cota"].min()) + ((float(df_collar["Z_Cota"].max()) - float(df_collar["Z_Cota"].min())) * (c / (num_curvas + 1))), 1)
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
    p_id = row["Nombre"]
    ensayos_pozo = [a for a in assays if a["ID"] == p_id]
    srv = next((s for s in surveys if s["ID"] == p_id), None)
    if not srv or not ensayos_pozo: continue
    
    az = np.radians(srv["Azimuth"])
    dp = np.radians(srv["Dip"])
    
    x_total.append(float(row["UTM Este"]))
    y_total.append(float(row["UTM Norte"]))
    z_total.append(float(row["Z_Cota"]))
    codigos_color_total.append(0.0)
    textos_total.append(f"<b>{p_id} (Collar)</b><br>Z: {row['Z_Cota']}m")
    
    for ens in ensayos_pozo:
        p_m = ens["From"] + 5
        int_x = float(row["UTM Este"]) + (p_m * np.cos(dp) * np.sin(az))
        int_y = float(row["UTM Norte"]) + (p_m * np.cos(dp) * np.cos(az))
        int_z = float(row["Z_Cota"]) + (p_m * np.sin(dp))
        
        val_ley = float(ens[columna_ley])
        
        if columna_ley == "Cu_pct":
            if val_ley < 0.30: codigo = 0.0
            elif 0.30 <= val_ley < 1.00: codigo = 1.0
            elif 1.00 <= val_ley < 1.80: codigo = 2.0
            else: codigo = 3.0
        else:
            if val_ley < 0.90: codigo = 0.0
            elif 0.90 <= val_ley < 4.00: codigo = 1.0
            elif 4.00 <= val_ley < 8.00: codigo = 2.0
            else: codigo = 3.0

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
# 🗂️ DISTRIBUCIÓN VISUAL EN LA PÁGINA WEB (Gran Pantalla Completa)
# ====================================================================
st.subheader("🛰️ Visualizador Espacial 3D Ampliado: Trazas de Pozos y Rangos de Ley")
st.caption("🖱️ CONTROL DE MOVIMIENTO: Haz clic izquierdo y arrastra para ROTAR. Usa la rueda del mouse para hacer ZOOM. Haz clic derecho y arrastra para DESPLAZAR (Pan).")

fig = go.Figure()

# 1. GENERAR ALAMBRE TOPOGRÁFICO 3D (Líneas finas de relieve)
min_x = float(df_collar["UTM Este"].min() - espaciamiento)
max_x = float(df_collar["UTM Este"].max() + espaciamiento)
min_y = float(df_collar["UTM Norte"].min() - espaciamiento)
max_y = float(df_collar["UTM Norte"].max() + espaciamiento)
rango_y = max_y - min_y

num_curvas = 10
for c in range(1, num_curvas + 1):
    x_linea = np.linspace(min_x, max_x, 30)
    y_base = min_y + espaciamiento + (rango_y * (c / (num_curvas + 1)))
    y_linea = y_base + (espaciamiento * 0.35) * np.sin((x_linea - min_x) / (espaciamiento * 1.8))
    z_linea = round(float(df_collar["Z_Cota"].min()) + ((float(df_collar["Z_Cota"].max()) - float(df_collar["Z_Cota"].min())) * (c / (num_curvas + 1))), 1)
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
    p_id = row["Nombre"]
    ensayos_pozo = [a for a in assays if a["ID"] == p_id]
    srv = next((s for s in surveys if s["ID"] == p_id), None)
    if not srv or not ensayos_pozo: continue
    
    az = np.radians(srv["Azimuth"])
    dp = np.radians(srv["Dip"])
    
    x_total.append(float(row["UTM Este"]))
    y_total.append(float(row["UTM Norte"]))
    z_total.append(float(row["Z_Cota"]))
    codigos_color_total.append(0.0)
    textos_total.append(f"<b>{p_id} (Collar)</b><br>Z: {row['Z_Cota']}m")
    
    for ens in ensayos_pozo:
        p_m = ens["From"] + 5
        int_x = float(row["UTM Este"]) + (p_m * np.cos(dp) * np.sin(az))
        int_y = float(row["UTM Norte"]) + (p_m * np.cos(dp) * np.cos(az))
        int_z = float(row["Z_Cota"]) + (p_m * np.sin(dp))
        
        val_ley = float(ens[columna_ley])
        
        if columna_ley == "Cu_pct":
            if val_ley < 0.30: codigo = 0.0
            elif 0.30 <= val_ley < 1.00: codigo = 1.0
            elif 1.00 <= val_ley < 1.80: codigo = 2.0
            else: codigo = 3.0
        else:
            if val_ley < 0.90: codigo = 0.0
            elif 0.90 <= val_ley < 4.00: codigo = 1.0
            elif 4.00 <= val_ley < 8.00: codigo = 2.0
            else: codigo = 3.0

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
# 📋 TABLAS DE DESCARGA E INTEGRACIÓN DE EXCEL REAL NATIVO (.XLSX)
# ====================================================================
st.markdown("---")
st.subheader("📋 Base de Datos del Proyecto (Hojas de Exploración)")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📌 1. Collar", "🧪 2. Assays (Leyes)", "🪨 3. Litología", "📐 4. Surveys", "🌍 5. Convertidor Google Earth", "📊 6. Estadísticas de Leyes"
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
    st.write("### 🛰️ Módulo de Conversión Geodésica 'EKmlz' Integrado")
    st.write("Carga tu archivo de collares en formato Excel para transformarlo de manera inmediata a un archivo cartográfico KML compatible con Google Earth.")
    
    archivo_cargado = st.file_uploader(
        "📂 Arrastra aquí el archivo 'Collar_Sondajes.xlsx' descargado de la pestaña 1:",
        type=["xlsx"],
        key="kml_uploader_manual_key"
    )
    
    if archivo_cargado is not None:
        try:
            import simplekml
            df_excel_alumno = pd.read_excel(archivo_cargado)
            
            columnas_requeridas = ["Nombre", "UTM Este", "UTM Norte", "Zona", "Hemisferio"]
            if not all(col in df_excel_alumno.columns for col in columnas_requeridas):
                st.error("❌ El archivo cargado no contiene las columnas oficiales de la plantilla (Nombre, UTM Este, UTM Norte, Zona, Hemisferio).")
            else:
                st.success("📊 Base de datos nueva detectada con éxito. Presiona el botón inferior para forzar la conversión geodésica actual.")
                
                if st.button("🚀 INICIAR CONVERSIÓN GEODÉSICA"):
                    with st.spinner("Procesando tu nueva simulación..."):
                        
                        kml_objeto = simplekml.Kml(name="Malla de Perforacion Diamantina - Norte de Chile")
                        
                        for idx, row in df_excel_alumno.iterrows():
                            x_utm = float(row["UTM Este"])
                            y_utm = float(row["UTM Norte"])
                            p_nombre = str(row["Nombre"])
                            p_desc = str(row["Descripcion"]) if "Descripcion" in df_excel_alumno.columns else "sondajes"
                            
                            # Ecuaciones Geodésicas de Precisión UTM a WGS84 (Huso 19S)
                            a = 6378137.0
                            f = 1 / 298.257223563
                            b = a * (1 - f)
                            e2 = (a**2 - b**2) / (a**2)
                            e_prim2 = (a**2 - b**2) / e_prim2 if 'e_prim2' in locals() else (a**2 - b**2) / (b**2)
                            
                            x_profe = x_utm - 500000.0
                            y_profe = y_utm - 10000000.0  
                            
                            c = a / (1 - f)
                            mu = y_profe / (6367449.146)
                            phi = mu
                            
                            for _ in range(5):
                                sin_2phi = np.sin(2 * phi)
                                sin_4phi = np.sin(4 * phi)
                                sin_6phi = np.sin(6 * phi)
                                phi = mu + (3 * e2 / 2 - 27 * e2**2 / 32) * sin_2phi + (21 * e2**2 / 16 - 55 * e2**3 / 32) * sin_4phi + (151 * e2**3 / 96) * sin_6phi
                            
                            n = c / np.sqrt(1 + e_prim2 * np.cos(phi)**2)
                            m = c / (1 + e_prim2 * np.cos(phi)**2)**1.5
                            t = np.tan(phi)**2
                            psi = e_prim2 * np.cos(phi)**2
                            
                            fact_lat = x_profe / n
                            lat_rad = phi - (fact_lat**2 * np.tan(phi) / 2) * (1 - (fact_lat**2 / 12) * (5 + 3 * t + psi - 9 * t * psi))
                            
                            fact_lon = x_profe / (n * np.cos(phi))
                            lon_rad = fact_lon - (fact_lon**3 / 6) * (1 + 2 * t + psi) + (fact_lon**5 / 120) * (5 + 28 * t + 24 * t**2)
                            
                            lat_decimal = -abs(np.degrees(lat_rad))
                            lon_decimal = -abs(-69.0 + np.degrees(lon_rad))  
                            
                            pnt = kml_objeto.newpoint(name=p_nombre)
                            pnt.coords = [(lon_decimal, lat_decimal)]
                            pnt.altitudemode = simplekml.AltitudeMode.clamptoground
                            pnt.description = f"Sondaje Diamantino Profesional\n• Este (X): {x_utm:,.1f} m\n• Norte (Y): {y_utm:,.1f} m\n• Tipo Mapeo: {p_desc}"
                            
                            pnt.style.iconstyle.icon.href = 'http://google.com'
                            pnt.style.iconstyle.color = 'ff0000ff' 
                            pnt.style.iconstyle.scale = 1.2
                            pnt.style.labelstyle.scale = 0.8

                        st.session_state["kml_bytes_nuevos"] = kml_objeto.kml().encode("utf-8")
                        st.balloons()

                if "kml_bytes_nuevos" in st.session_state:
                    st.markdown("---")
                    st.success("🎉 ¡Conversión de tu Nueva Simulación Finalizada con Éxito!")
                    st.download_button(
                        label="📥 Descargar Archivo Malla_Sondajes_Chile.kml (Google Earth)",
                        data=st.session_state["kml_bytes_nuevos"],
                        file_name="Malla_Sondajes_Chile.kml",
                        mime="application/vnd.google-earth.kml+xml"
                    )
                
        except Exception as e:
            st.error(f"❌ Error al procesar la conversión del KML. Detalle técnico: {e}")
# PESTAÑA 6: Módulo para Estadísticas, Distribución de Frecuencias e Histograma de Leyes
with tab6:
    st.write(f"### 📊 Reporte Estadístico y Análisis de Frecuencias de Leyes: **{elemento_render}**")
    st.write("Esta sección calcula automáticamente los parámetros geoestadísticos y la distribución de intervalos metalúrgicos de la actual campaña diamantina.")
    
    # Extraer leyes de la simulación activa, ignorando tramos estériles puros de sobrecarga (0.0) para no sesgar la media
    col_seleccionada = "Cu_pct" if elemento_render == "Cobre (Cu %)" else "Au_gpt"
    leyes_utiles = df_assays[df_assays[col_seleccionada] > 0.0][col_seleccionada].values
    
    if len(leyes_utiles) == 0:
        st.warning("⚠️ No hay tramos mineralizados disponibles en la simulación actual para calcular estadísticas.")
    else:
        # 1. Definición estricta de intervalos de corte (Cut-off) según tu modelo docente
        if col_seleccionada == "Cu_pct":
            limites = [0.0, 0.30, 1.00, 1.80, 2.50]
            etiquetas = ["Baja Ley (< 0.30 %)", "Ley Media (0.30 - 1.00 %)", "Alta Ley (1.00 - 1.80 %)", "Excelente Ley (> 1.80 %)"]
            unidad = "%"
        else:
            limites = [0.0, 0.90, 4.00, 8.00, 12.00]
            etiquetas = ["Baja Ley (< 0.90 g/t)", "Ley Media (0.90 - 4.00 g/t)", "Alta Ley (4.00 - 8.00 g/t)", "Excelente Ley (> 8.00 g/t)"]
            unidad = "g/t"
            
        # 2. PROCESAMIENTO MATEMÁTICO GEOESTADÍSTICO DE LOS INTERVALOS
        filas_tabla = []
        total_muestras = len(leyes_utiles)
        frecuencia_acumulada_pct = 0.0
        
        for k in range(len(etiquetas)):
            min_int = limites[k]
            max_int = limites[k+1]
            
            # Filtrar muestras dentro del intervalo actual de forma estricta
            if k < len(etiquetas) - 1:
                muestras_intervalo = leyes_utiles[(leyes_utiles >= min_int) & (leyes_utiles < max_int)]
            else:
                muestras_intervalo = leyes_utiles[leyes_utiles >= min_int]
            
            conteo_parcial = len(muestras_intervalo)
            ley_media_intervalo = np.mean(muestras_intervalo) if conteo_parcial > 0 else 0.0
            frecuencia_parcial_pct = (conteo_parcial / total_muestras) * 100
            frecuencia_acumulada_pct += frecuencia_parcial_pct
            
            filas_tabla.append({
                "Intervalos por Categorías": etiquetas[k],
                f"Ley Media ({unidad})": round(float(ley_media_intervalo), 2),
                "Conteo Parcial": int(conteo_parcial),
                "Frecuencia Parcial (%)": round(float(frecuencia_parcial_pct), 1),
                "Frecuencia Acumulada (%)": round(float(frecuencia_acumulada_pct), 1)
            })
            
        df_estadistica = pd.DataFrame(filas_tabla)
        
        # Desplegar Tabla de Frecuencias formal en la pantalla
        st.write("#### 📋 Tabla de Frecuencias Metalúrgicas Resumida")
        st.dataframe(df_estadistica, use_container_width=True, index=False)
        
        st.markdown("---")
        st.write("#### 📈 Histograma de Distribución y Conteo de Muestras")
        
        # 3. CONSTRUCCIÓN DEL GRÁFICO HISTOGRAMA MEDIANTE MATPLOTLIB (BINARIO EN MEMORIA)
        import matplotlib.pyplot as plt
        
        fig_hist, ax_hist = plt.subplots(figsize=(10, 4.5))
        
        # Dibujar histograma de barras con los límites reales
        conteos, bins, parches = ax_hist.hist(
            leyes_utiles, bins=limites, edgecolor="black", 
            color="#3498db", alpha=0.75, rwidth=0.95
        )
        
        # Configuración estética de ejes usando mathtext estándar
        ax_hist.set_title(f"Distribucion Geoestadistica del Proyecto - {elemento_render}", fontsize=11, fontweight='bold')
        ax_hist.set_xlabel(f"Grado de Ley Metalurgica ({unidad})", fontsize=10)
        ax_hist.set_ylabel("Cantidad de Muestras (Conteo)", fontsize=10)
        ax_hist.set_xticks(limites)
        ax_hist.grid(axis='y', linestyle='--', alpha=0.5)
        
        # Inyectar etiquetas de conteo encima de cada barra para facilitar la lectura
        for conteo, bin_borde in zip(conteos, bins):
            if conteo > 0:
                ax_hist.text(
                    bin_borde + 0.15 * (bins[1] - bins[0]), conteo + (max(conteos) * 0.02), 
                    f"{int(conteo)} und", ha='left', fontsize=9, fontweight='bold', color='#2c3e50'
                )

        # Compilar el gráfico a string binario en memoria RAM para Streamlit Cloud
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        st.image(buf, use_container_width=True)
        plt.close()
        
        # Desplegar un botón para exportar esta tabla de frecuencias a un Excel analítico independiente
        st.write("*(Opcional) Si deseas adjuntar la tabla de distribución a tus reportes de cátedra, descarga la hoja de frecuencias:*")
        crear_boton_excel(df_estadistica, f"Reporte_Estadistico_{col_seleccionada}")