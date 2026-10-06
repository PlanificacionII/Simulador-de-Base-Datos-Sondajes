import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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

# PANEL LATERAL DE CONTROL
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
# ⚙️ MOTOR DE CÁLCULO TRIDIMENSIONAL RELACIONAL (SIMULACIÓN DE SONDAJES)
# ====================================================================

collars = []
assays = []
lithologies = []
surveys = []

# Dimensión de la malla de perforación
dimension_malla = espaciamiento * 20
centro_x = b_este + (dimension_malla / 2)
centro_y = b_norte + (dimension_malla / 2)
centro_z = b_cota - 250

# ====================================================================
# 🔩 GENERACIÓN DE SONDAJES SIMULADOS
# ====================================================================
for i in range(1, cant_sondajes + 1):
    pozo_id = f"DDH-{i:03d}"

    # Geometría de la malla
    if tipo_malla == "Malla Regular (Grilla)":
        x = b_este + ((i - 1) % 20) * espaciamiento
        y = b_norte + ((i - 1) // 20) * espaciamiento
    else:
        x = b_este + np.random.rand() * dimension_malla
        y = b_norte + np.random.rand() * dimension_malla

    # Topografía simulada
    pendiente_x = (x - b_este) * 0.03
    pendiente_y = (y - b_norte) * 0.02
    elev = np.round(b_cota + pendiente_x + pendiente_y + np.random.normal(0, var_cota / 2), 1)

    # Profundidad del pozo según tipo de yacimiento
    depth = (
        int(250 + np.random.rand() * 150)
        if tipo_yacimiento == "Veta Estructural (Tabular)"
        else int(400 + np.random.rand() * 200)
    )

    # Sobrecarga (capa estéril superficial)
    sobrecarga = int(60 + np.random.rand() * 60)

    # Orientación del pozo
    if tipo_yacimiento == "Veta Estructural (Tabular)":
        azimuth = int(90 + np.random.normal(0, 10))
        dip = int(-50 - np.random.rand() * 15)
    else:
        azimuth = int(np.random.rand() * 360)
        dip = -90 if i % 3 == 0 else int(-60 - np.random.rand() * 15)

    # Registrar COLLAR
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

    # Registrar SURVEY
    surveys.append({"ID": pozo_id, "Depth": depth, "Azimuth": azimuth, "Dip": dip})

    # Convertir ángulos a radianes
    rad_azimuth = np.radians(azimuth)
    rad_dip = np.radians(dip)

    # ====================================================================
    # 🔬 GENERACIÓN DE ENSAYOS (ASSAYS) Y LITOLOGÍA POR TRAMOS DE 10m
    # ====================================================================
    for j in range(depth // 10):
        from_m = j * 10
        to_m = from_m + 10
        p_medio = from_m + 5

        # Coordenadas del tramo
        int_x = x + (p_medio * np.cos(rad_dip) * np.sin(rad_azimuth))
        int_y = y + (p_medio * np.cos(rad_dip) * np.cos(rad_azimuth))
        int_z = elev + (p_medio * np.sin(rad_dip))

        # Capa estéril superficial
        if from_m < sobrecarga:
            cu, au, lit = 0.0, 0.0, "Overburden"
        else:
            # Distancia horizontal al centro del depósito
            dist_h = np.sqrt((int_x - centro_x)**2 + (int_y - centro_y)**2)

            # Zona mineralizada
            if dist_h < 650:
                cu = np.clip(normal_random(1.2, 0.45), 0.3, 2.5)
                au = np.clip(normal_random(6.0, 2.2), 0.9, 12.0)

                if dist_h < 300:
                    lit = "Quartz_Vein_Core" if "Tabular" in tipo_yacimiento else "Massive_Body_Core"
                else:
                    lit = "Stockwork_Halo" if "Tabular" in tipo_yacimiento else "Mineralized_Breccia"
            else:
                # Roca caja
                lit = "Country_Rock"
                cu = np.clip(normal_random(0.45, 0.1), 0.3, 0.8)
                au = np.clip(normal_random(2.1, 0.5), 0.9, 3.2)

        # Redondeo final
        cu = np.round(max(0.0, cu), 2)
        au = np.round(max(0.0, au), 2)

        # Registrar litología
        lithologies.append({
            "ID": pozo_id,
            "From": from_m,
            "To": to_m,
            "Lithology": lit
        })

        # Registrar ensayos
        assays.append({
            "ID": pozo_id,
            "From": from_m,
            "To": to_m,
            "Cu_pct": cu,
            "Au_gpt": au
        })

# Convertir a DataFrames
df_collar = pd.DataFrame(collars)
df_assays = pd.DataFrame(assays)
df_lithology = pd.DataFrame(lithologies)
df_surveys = pd.DataFrame(surveys)
# ====================================================================
# 🛰️ VISUALIZADOR 3D DE SONDAJES
# ====================================================================

st.subheader("🛰️ Visualizador Espacial 3D Ampliado: Trazas de Pozos y Rangos de Ley")
st.caption("🖱️ CONTROL DE MOVIMIENTO: clic izquierdo para rotar, rueda para zoom, clic derecho para pan.")

fig = go.Figure()

# Rango espacial para topografía
min_x = float(df_collar["UTM Este"].min() - espaciamiento)
max_x = float(df_collar["UTM Este"].max() + espaciamiento)
min_y = float(df_collar["UTM Norte"].min() - espaciamiento)
max_y = float(df_collar["UTM Norte"].max() + espaciamiento)
rango_y = max_y - min_y

# ====================================================================
# 1. ALAMBRE TOPOGRÁFICO 3D
# ====================================================================
num_curvas = 10
for c in range(1, num_curvas + 1):
    x_linea = np.linspace(min_x, max_x, 30)
    y_base = min_y + espaciamiento + (rango_y * (c / (num_curvas + 1)))
    y_linea = y_base + (espaciamiento * 0.35) * np.sin((x_linea - min_x) / (espaciamiento * 1.8))
    z_linea = round(
        float(df_collar["Z_Cota"].min()) +
        ((float(df_collar["Z_Cota"].max()) - float(df_collar["Z_Cota"].min())) * (c / (num_curvas + 1))),
        1
    )
    z_array = np.full_like(x_linea, z_linea)

    fig.add_trace(go.Scatter3d(
        x=x_linea, y=y_linea, z=z_array, mode='lines',
        line=dict(color='rgba(150, 150, 150, 0.3)', width=1.5),
        showlegend=False, hoverinfo='none'
    ))

# ====================================================================
# 2. TRAZAS DE SONDAJES CON COLOREO POR LEY
# ====================================================================
columna_ley = "Cu_pct" if elemento_render == "Cobre (Cu %)" else "Au_gpt"
unidad_ley = "%" if elemento_render == "Cobre (Cu %)" else "g/t"

x_total, y_total, z_total = [], [], []
codigos_color_total, textos_total = [], []

for idx, row in df_collar.iterrows():
    p_id = row["Nombre"]
    ensayos_pozo = df_assays[df_assays["ID"] == p_id]
    srv = df_surveys[df_surveys["ID"] == p_id].iloc[0]

    az = np.radians(srv["Azimuth"])
    dp = np.radians(srv["Dip"])

    # Collar
    x_total.append(float(row["UTM Este"]))
    y_total.append(float(row["UTM Norte"]))
    z_total.append(float(row["Z_Cota"]))
    codigos_color_total.append(0.0)
    textos_total.append(f"<b>{p_id} (Collar)</b><br>Z: {row['Z_Cota']}m")

    # Tramos
    for _, ens in ensayos_pozo.iterrows():
        p_m = ens["From"] + 5
        int_x = float(row["UTM Este"]) + (p_m * np.cos(dp) * np.sin(az))
        int_y = float(row["UTM Norte"]) + (p_m * np.cos(dp) * np.cos(az))
        int_z = float(row["Z_Cota"]) + (p_m * np.sin(dp))

        val_ley = float(ens[columna_ley])

        # Clasificación por rangos
        if columna_ley == "Cu_pct":
            if val_ley < 0.30: codigo = 0.0
            elif val_ley < 1.00: codigo = 1.0
            elif val_ley < 1.80: codigo = 2.0
            else: codigo = 3.0
        else:
            if val_ley < 0.90: codigo = 0.0
            elif val_ley < 4.00: codigo = 1.0
            elif val_ley < 8.00: codigo = 2.0
            else: codigo = 3.0

        x_total.append(int_x)
        y_total.append(int_y)
        z_total.append(int_z)
        codigos_color_total.append(codigo)

        lit = df_lithology[
            (df_lithology["ID"] == p_id) &
            (df_lithology["From"] == ens["From"])
        ]["Lithology"].values[0]

        textos_total.append(
            f"<b>{p_id}</b><br>"
            f"Tramo: {ens['From']}-{ens['To']}m<br>"
            f"Lit: {lit}<br>"
            f"Ley: {val_ley:,.2f} {unidad_ley}"
        )

    # Separador visual entre pozos
    x_total.append(np.nan)
    y_total.append(np.nan)
    z_total.append(np.nan)
    codigos_color_total.append(0.0)
    textos_total.append("")

# Paleta discreta
paleta_discreta = [
    [0.0, "green"], [0.25, "green"],
    [0.25, "yellow"], [0.5, "yellow"],
    [0.5, "orange"], [0.75, "orange"],
    [0.75, "red"], [1.0, "red"]
]

fig.add_trace(go.Scatter3d(
    x=x_total, y=y_total, z=z_total,
    mode='lines+markers',
    line=dict(
        color=codigos_color_total,
        colorscale=paleta_discreta,
        width=6,
        cmin=0.0, cmax=3.0,
        colorbar=dict(
            title=f"Rangos ({unidad_ley})",
            thickness=20,
            x=0.98,
            tickvals=[0.375, 1.125, 1.875, 2.625],
            ticktext=[
                "Estéril (<0.30%)" if columna_ley=="Cu_pct" else "Estéril (<0.9 g/t)",
                "Baja-Media (0.30-1.0%)" if columna_ley=="Cu_pct" else "Baja (0.9-4.0 g/t)",
                "Alta Ley (1.0-1.8%)" if columna_ley=="Cu_pct" else "Alta Ley (4.0-8.0 g/t)",
                "Excelente (>1.80%)" if columna_ley=="Cu_pct" else "Excelente (>8.0 g/t)"
            ]
        )
    ),
    marker=dict(
        size=2.5,
        color=codigos_color_total,
        colorscale=paleta_discreta,
        cmin=0.0, cmax=3.0,
        opacity=0.9
    ),
    text=textos_total,
    hoverinfo='text',
    showlegend=False
))

# Configuración de escena 3D
fig.update_layout(
    width=1300,
    height=700,
    margin=dict(l=0, r=0, t=10, b=0),
    scene=dict(
        xaxis=dict(title="Este (X)", gridcolor="lightgrey", backgroundcolor="whitesmoke"),
        yaxis=dict(title="Norte (Y)", gridcolor="lightgrey", backgroundcolor="whitesmoke"),
        zaxis=dict(title="Cota (Z)", gridcolor="lightgrey", backgroundcolor="whitesmoke"),
        aspectmode="manual",
        aspectratio=dict(x=1, y=1, z=0.5)
    )
)

st.plotly_chart(fig, use_container_width=True, key="visor_grafico_3d_unico")
# ====================================================================
# 📋 SECCIÓN DE PESTAÑAS PRINCIPALES DEL PROYECTO
# ====================================================================

st.markdown("---")
st.subheader("📋 Base de Datos del Proyecto (Hojas de Exploración)")

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
    "📌 1. Collar",
    "🧪 2. Assays (Leyes)",
    "🪨 3. Litología",
    "📐 4. Surveys",
    "🌍 5. Convertidor Google Earth",
    "📊 6. Estadísticas de Leyes",
    "📐 7. Compositaje de Pozos",
    "📉 8. Variografía e Isotropía",
    "🧊 9. Modelo de Bloques (Kriging)",
    "📈 10. Curvas Ley–Tonelaje"
])

# ====================================================================
# 📤 FUNCIÓN PROFESIONAL PARA EXPORTAR A EXCEL
# ====================================================================

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
# ====================================================================
# 📌 PESTAÑA 1 — COLLAR
# ====================================================================
with tab1:
    st.write("### 📌 Base de Datos de Collares de Sondajes")
    st.caption("Coordenadas UTM, cota topográfica y metadatos de cada pozo diamantado.")

    st.dataframe(
        df_collar.drop(columns=["Z_Cota", "Profundidad"]),
        use_container_width=True,
        height=260
    )

    crear_boton_excel(
        df_collar,
        "Collar_Sondajes",
        ocultar_columnas=["Z_Cota", "Profundidad"]
    )
# ====================================================================
# 🧪 PESTAÑA 2 — ASSAYS (Leyes Metalúrgicas)
# ====================================================================
with tab2:
    st.write("### 🧪 Ensayos Metalúrgicos (Assays)")
    st.caption("Leyes de Cobre y Oro por intervalos de perforación.")

    st.dataframe(
        df_assays,
        use_container_width=True,
        height=260
    )

    crear_boton_excel(df_assays, "Assays_Leyes")
# ====================================================================
# 🪨 PESTAÑA 3 — LITOLOGÍA
# ====================================================================
with tab3:
    st.write("### 🪨 Litología de Tramos")
    st.caption("Clasificación geológica de cada intervalo perforado.")

    st.dataframe(
        df_lithology,
        use_container_width=True,
        height=260
    )

    crear_boton_excel(df_lithology, "Litologia_Sondajes")
# ====================================================================
# 📐 PESTAÑA 4 — SURVEYS (Trayectorias)
# ====================================================================
with tab4:
    st.write("### 📐 Trayectorias de Sondajes (Surveys)")
    st.caption("Azimuth, buzamiento y profundidad total de cada pozo.")

    st.dataframe(
        df_surveys,
        use_container_width=True,
        height=260
    )

    crear_boton_excel(df_surveys, "Surveys_Trayectorias")
# ====================================================================
# 🌍 PESTAÑA 5 — CONVERSIÓN GOOGLE EARTH (EKmlz)
# ====================================================================
with tab5:
    st.write("### 🛰️ Módulo de Conversión Geodésica 'EKmlz' Integrado")
    st.caption("Convierte automáticamente tus collares a un archivo KML compatible con Google Earth.")

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
                st.error("❌ El archivo cargado no contiene las columnas oficiales (Nombre, UTM Este, UTM Norte, Zona, Hemisferio).")
            else:
                st.success("📊 Archivo válido detectado. Presiona el botón para convertir a KML.")

                if st.button("🚀 INICIAR CONVERSIÓN GEODÉSICA"):
                    with st.spinner("Procesando conversión UTM → WGS84..."):

                        kml_objeto = simplekml.Kml(name="Malla de Perforación Diamantina - Norte de Chile")

                        # Parámetros del elipsoide WGS84
                        a = 6378137.0
                        f = 1 / 298.257223563
                        b = a * (1 - f)
                        e2 = (a**2 - b**2) / (a**2)
                        e_prim2 = (a**2 - b**2) / (b**2)

                        for idx, row in df_excel_alumno.iterrows():
                            x_utm = float(row["UTM Este"])
                            y_utm = float(row["UTM Norte"])
                            p_nombre = str(row["Nombre"])
                            p_desc = str(row["Descripcion"]) if "Descripcion" in df_excel_alumno.columns else "sondajes"

                            # Ajuste UTM → coordenadas planas
                            x_profe = x_utm - 500000.0
                            y_profe = y_utm - 10000000.0

                            # Cálculo de latitud geodésica
                            mu = y_profe / 6367449.146
                            phi = mu

                            for _ in range(5):
                                phi = (
                                    mu
                                    + (3*e2/2 - 27*e2**2/32) * np.sin(2*phi)
                                    + (21*e2**2/16 - 55*e2**3/32) * np.sin(4*phi)
                                    + (151*e2**3/96) * np.sin(6*phi)
                                )

                            n = a / np.sqrt(1 - e2 * np.sin(phi)**2)
                            t = np.tan(phi)**2
                            psi = e_prim2 * np.cos(phi)**2

                            fact_lat = x_profe / n
                            lat_rad = phi - (fact_lat**2 * np.tan(phi) / 2) * (
                                1 - (fact_lat**2 / 12) * (5 + 3*t + psi - 9*t*psi)
                            )

                            fact_lon = x_profe / (n * np.cos(phi))
                            lon_rad = fact_lon - (fact_lon**3 / 6) * (1 + 2*t + psi) + (
                                fact_lon**5 / 120
                            ) * (5 + 28*t + 24*t**2)

                            lat_decimal = -abs(np.degrees(lat_rad))
                            lon_decimal = -abs(-69.0 + np.degrees(lon_rad))

                            # Crear punto KML
                            pnt = kml_objeto.newpoint(name=p_nombre)
                            pnt.coords = [(lon_decimal, lat_decimal)]
                            pnt.altitudemode = simplekml.AltitudeMode.clamptoground
                            pnt.description = (
                                f"Sondaje Diamantino\n"
                                f"• Este (X): {x_utm:,.1f} m\n"
                                f"• Norte (Y): {y_utm:,.1f} m\n"
                                f"• Tipo: {p_desc}"
                            )

                            pnt.style.iconstyle.icon.href = 'http://google.com'
                            pnt.style.iconstyle.color = 'ff0000ff'
                            pnt.style.iconstyle.scale = 1.2
                            pnt.style.labelstyle.scale = 0.8

                        # Guardar en memoria
                        st.session_state["kml_bytes_nuevos"] = kml_objeto.kml().encode("utf-8")
                        st.balloons()

                # Botón de descarga
                if "kml_bytes_nuevos" in st.session_state:
                    st.markdown("---")
                    st.success("🎉 Conversión finalizada con éxito.")
                    st.download_button(
                        label="📥 Descargar Malla_Sondajes_Chile.kml",
                        data=st.session_state["kml_bytes_nuevos"],
                        file_name="Malla_Sondajes_Chile.kml",
                        mime="application/vnd.google-earth.kml+xml"
                    )

        except Exception as e:
            st.error(f"❌ Error al procesar la conversión del KML. Detalle técnico: {e}")
# ====================================================================
# 📊 PESTAÑA 6 — ESTADÍSTICAS DE LEYES (CORREGIDO Y PROFESIONAL)
# ====================================================================
with tab6:
    st.write(f"### 📊 Reporte Estadístico y Test de Ajuste de Leyes: **{elemento_render}**")
    st.caption("Evaluación estadística completa de las leyes simuladas, incluyendo prueba K‑S y análisis descriptivo.")

    # Selección de columna según metal
    col_seleccionada = "Cu_pct" if elemento_render == "Cobre (Cu %)" else "Au_gpt"
    unidad = "%" if col_seleccionada == "Cu_pct" else "g/t"

    # Filtrar solo tramos mineralizados
    leyes_utiles = df_assays[df_assays[col_seleccionada] > 0.0][col_seleccionada].values

    if len(leyes_utiles) == 0:
        st.warning("⚠️ No hay tramos mineralizados disponibles en la simulación actual.")
    else:

        # ====================================================================
        # 🔬 1. PRUEBA DE BONDAD DE AJUSTE (K-S)
        # ====================================================================
        st.write("#### 📝 Laboratorio de Inferencia: Prueba de Bondad de Ajuste (K‑S)")
        st.info("Selecciona el modelo teórico y ejecuta la prueba de Kolmogorov‑Smirnov para validar tu hipótesis.")

        hipotesis_alumno = st.radio(
            "Hipótesis Nula (H₀): 'Los datos de las leyes se ajustan a una función...'",
            [
                "Distribución Normal (Gaussiana)",
                "Distribución Log-Normal (2 Parámetros)",
                "Distribución Log-Normal (3 Parámetros - Con Umbral)",
                "Distribución Exponencial"
            ]
        )

        if "tipo_curva_graficar" not in st.session_state:
            st.session_state["tipo_curva_graficar"] = "Distribución Normal (Gaussiana)"

        if st.button("🧪 EVALUAR TEST DE AJUSTE"):
            from scipy import stats

            st.session_state["tipo_curva_graficar"] = hipotesis_alumno
            leyes_limpias = leyes_utiles[np.isfinite(leyes_utiles)]

            # Modelos teóricos
            if hipotesis_alumno == "Distribución Normal (Gaussiana)":
                loc, scale = stats.norm.fit(leyes_limpias)
                stat, p_valor = stats.ks_1samp(leyes_limpias, lambda x: stats.norm.cdf(x, loc, scale))
                nombre_dist = "Normal"

            elif hipotesis_alumno == "Distribución Log-Normal (2 Parámetros)":
                shape, loc, scale = stats.lognorm.fit(leyes_limpias, floc=0)
                stat, p_valor = stats.ks_1samp(leyes_limpias, lambda x: stats.lognorm.cdf(x, shape, loc, scale))
                nombre_dist = "Log-Normal de 2 Parámetros"

            elif hipotesis_alumno == "Distribución Log-Normal (3 Parámetros - Con Umbral)":
                shape, loc, scale = stats.lognorm.fit(leyes_limpias)
                stat, p_valor = stats.ks_1samp(leyes_limpias, lambda x: stats.lognorm.cdf(x, shape, loc, scale))
                nombre_dist = "Log-Normal de 3 Parámetros"

            else:
                loc, scale = stats.expon.fit(leyes_limpias)
                stat, p_valor = stats.ks_1samp(leyes_limpias, lambda x: stats.expon.cdf(x, loc, scale))
                nombre_dist = "Exponencial"

            # Mostrar resultados
            st.markdown("---")
            st.write("##### 📑 Veredicto Científico del Test:")

            alfa = 0.05
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Estadístico D", f"{stat:.4f}")
            with c2:
                st.metric("P‑Valor", f"{p_valor:.5f}")

            if p_valor >= alfa:
                st.success(
                    f"🎉 HIPÓTESIS COMPROBADA: P‑valor ({p_valor:.5f}) ≥ {alfa}. "
                    f"No se rechaza H₀. Los datos se ajustan a una distribución **{nombre_dist}**."
                )
            else:
                st.error(
                    f"❌ HIPÓTESIS RECHAZADA: P‑valor ({p_valor:.5f}) < {alfa}. "
                    f"Se rechaza H₀. Los datos **no** se ajustan a una distribución {nombre_dist}."
                )

        # ====================================================================
        # 📈 2. ESTADÍSTICAS DESCRIPTIVAS MINERAS
        # ====================================================================
        st.markdown("---")
        st.write("#### 📐 Resumen Geoestadístico Descriptivo del Yacimiento")

        n_muestras = len(leyes_utiles)
        ley_min = float(np.min(leyes_utiles))
        ley_max = float(np.max(leyes_utiles))
        ley_media = float(np.mean(leyes_utiles))
        ley_mediana = float(np.median(leyes_utiles))
        ley_varianza = float(np.var(leyes_utiles, ddof=1))
        ley_desviacion = float(np.std(leyes_utiles, ddof=1))
        coef_variacion = ley_desviacion / ley_media if ley_media > 0 else 0.0

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Total Muestras (n)", f"{n_muestras}")
            st.metric("Media Aritmética (X)", f"{ley_media:.2f} {unidad}")
        with m2:
            st.metric("Ley Mínima", f"{ley_min:.2f} {unidad}")
            st.metric("Mediana (P50)", f"{ley_mediana:.2f} {unidad}")
        with m3:
            st.metric("Ley Máxima", f"{ley_max:.2f} {unidad}")
            st.metric("Desviación Estándar", f"{ley_desviacion:.2f} {unidad}")
        with m4:
            st.metric("Varianza", f"{ley_varianza:.3f}")
            st.metric("Coef. Variación (CV)", f"{coef_variacion:.2f}")

        # ====================================================================
        # 📋 3. TABLA DE FRECUENCIAS (12 INTERVALOS)
        # ====================================================================
        st.markdown("---")
        st.write("#### 📋 Tabla de Frecuencias Metalúrgicas (12 Intervalos)")

        limites = np.linspace(ley_min, ley_max, 13)
        filas_tabla = []
        frecuencia_acumulada_pct = 0.0

        for k in range(12):
            min_int = limites[k]
            max_int = limites[k + 1]

            if k < 11:
                muestras_intervalo = leyes_utiles[(leyes_utiles >= min_int) & (leyes_utiles < max_int)]
            else:
                muestras_intervalo = leyes_utiles[leyes_utiles >= min_int]

            conteo = len(muestras_intervalo)
            ley_media_intervalo = np.mean(muestras_intervalo) if conteo > 0 else 0.0
            freq_pct = (conteo / n_muestras) * 100
            frecuencia_acumulada_pct += freq_pct

            filas_tabla.append({
                "Intervalo": f"[{min_int:.2f} - {max_int:.2f}]",
                f"Ley Media ({unidad})": round(ley_media_intervalo, 2),
                "Conteo": conteo,
                "Frecuencia (%)": round(freq_pct, 1),
                "Frecuencia Acumulada (%)": round(frecuencia_acumulada_pct, 1)
            })

        df_estadistica = pd.DataFrame(filas_tabla)
        st.dataframe(df_estadistica, use_container_width=True, hide_index=True)

        # ====================================================================
        # 📈 4. HISTOGRAMA + CURVA TEÓRICA
        # ====================================================================
        st.markdown("---")
        st.write("#### 📈 Histograma de Distribución y Curva de Densidad Seleccionada")

        import matplotlib.pyplot as plt
        from scipy import stats

        fig_hist, ax_hist = plt.subplots(figsize=(11, 5))

        conteos, bins, _ = ax_hist.hist(
            leyes_utiles,
            bins=limites,
            edgecolor="black",
            color="#3498db",
            alpha=0.6,
            rwidth=0.92
        )

        ax_hist.set_title(f"Distribución Geoestadística — {elemento_render}", fontsize=11, fontweight='bold')
        ax_hist.set_xlabel(f"Ley ({unidad})")
        ax_hist.set_ylabel("Conteo")

        ax_hist.set_xticks(limites)
        plt.xticks(rotation=45, fontsize=8)
        ax_hist.grid(axis='y', linestyle='--', alpha=0.5)

        # Etiquetas sobre barras
        for k in range(12):
            if conteos[k] > 0:
                bin_centro = (bins[k] + bins[k + 1]) / 2
                ax_hist.text(bin_centro, conteos[k] + max(conteos) * 0.02, str(int(conteos[k])),
                             ha='center', fontsize=8, fontweight='bold')

        # Curva teórica
        ax_curva = ax_hist.twinx()
        x_eje = np.linspace(ley_min, ley_max, 300)

        curva_activa = st.session_state["tipo_curva_graficar"]

        if curva_activa == "Distribución Normal (Gaussiana)":
            loc, scale = stats.norm.fit(leyes_utiles)
            y_eje = stats.norm.pdf(x_eje, loc, scale)
            label_curva = f"Normal (μ={loc:.2f}, σ={scale:.2f})"

        elif curva_activa == "Distribución Log-Normal (2 Parámetros)":
            shape, loc, scale = stats.lognorm.fit(leyes_utiles, floc=0)
            y_eje = stats.lognorm.pdf(x_eje, shape, loc, scale)
            label_curva = "Log-Normal 2P"

        elif curva_activa == "Distribución Log-Normal (3 Parámetros - Con Umbral)":
            shape, loc, scale = stats.lognorm.fit(leyes_utiles)
            y_eje = stats.lognorm.pdf(x_eje, shape, loc, scale)
            label_curva = "Log-Normal 3P"

        else:
            loc, scale = stats.expon.fit(leyes_utiles)
            y_eje = stats.expon.pdf(x_eje, loc, scale)
            label_curva = "Exponencial"

        ax_curva.plot(x_eje, y_eje, color="red", linewidth=2, label=label_curva)
        ax_curva.set_ylabel("Densidad de Probabilidad")
        ax_curva.grid(axis='y', linestyle='--', alpha=0.3)
        ax_curva.legend(loc="upper right", fontsize=8)

        st.pyplot(fig_hist)
# ====================================================================
# 📐 PESTAÑA 7 — COMPOSITAJE DE SONDAJES (Banco / Collarín)
# ====================================================================
with tab7:

    st.markdown("## 📐 Módulo de Compositaje de Pozos")
    st.caption("Regularización del soporte minero para estimación de recursos.")

    # ============================================================
    # 1. Selección del método de compositaje
    # ============================================================
    metodo = st.radio(
        "Seleccione el método de compositaje:",
        ["Por Collarín (Longitud fija)", "Por Banco (RL / Cota)"],
        horizontal=True
    )

    # ============================================================
    # 2. Parámetros según método
    # ============================================================
    if metodo == "Por Collarín (Longitud fija)":
        largo_composito = st.number_input(
            "Longitud del composito (m):",
            min_value=1, max_value=50, value=10, step=1
        )
    else:
        banco_altura = st.number_input(
            "Altura del banco (m):",
            min_value=2, max_value=50, value=10, step=1
        )

    st.markdown("---")

    # ============================================================
    # 3. Cálculo del compositaje
    # ============================================================
    compositos = []

    for idx, row in df_collar.iterrows():

        p_id = row["Nombre"]
        x_coll = float(row["UTM Este"])
        y_coll = float(row["UTM Norte"])
        z_coll = float(row["Z_Cota"])

        ensayos_pozo = df_assays[df_assays["ID"] == p_id].sort_values(by="From")
        srv = next((s for s in surveys if s["ID"] == p_id), None)

        if ensayos_pozo.empty or not srv:
            continue

        az_rad = np.radians(srv["Azimuth"])
        dp_rad = np.radians(srv["Dip"])

        # ============================================================
        # MÉTODO 1: COLLARÍN (Longitud fija)
        # ============================================================
        if metodo == "Por Collarín (Longitud fija)":

            prof_max = float(ensayos_pozo["To"].max())
            n_comp = int(np.ceil(prof_max / largo_composito))

            for k in range(n_comp):

                c_from = k * largo_composito
                c_to = min(c_from + largo_composito, prof_max)
                c_len = c_to - c_from
                if c_len <= 0:
                    continue

                suma_ley_long = 0.0
                suma_inter = 0.0

                for _, ensay in ensayos_pozo.iterrows():
                    overlap_from = max(c_from, float(ensay["From"]))
                    overlap_to = min(c_to, float(ensay["To"]))
                    inter = overlap_to - overlap_from

                    if inter > 0:
                        suma_ley_long += float(ensay[col_seleccionada]) * inter
                        suma_inter += inter

                ley_comp = (suma_ley_long / suma_inter) if suma_inter > 0 else 0.0

                pm = c_from + (c_len / 2)
                xi = x_coll + (pm * np.cos(dp_rad) * np.sin(az_rad))
                yi = y_coll + (pm * np.cos(dp_rad) * np.cos(az_rad))
                zi = z_coll + (pm * np.sin(dp_rad))

                compositos.append({
                    "ID": p_id,
                    "X": round(xi, 2),
                    "Y": round(yi, 2),
                    "Z": round(zi, 2),
                    "Desde": round(c_from, 2),
                    "Hasta": round(c_to, 2),
                    "Ley": round(ley_comp, 4)
                })

        # ============================================================
        # MÉTODO 2: BANCO (RL / Cota)
        # ============================================================
        else:

            z_min = ensayos_pozo["Z"].min()
            z_max = ensayos_pozo["Z"].max()

            bancos = np.arange(z_min, z_max + banco_altura, banco_altura)

            for b in range(len(bancos) - 1):

                z_inf = bancos[b]
                z_sup = bancos[b + 1]

                ensayos_banco = ensayos_pozo[
                    (ensayos_pozo["Z"] >= z_inf) &
                    (ensayos_pozo["Z"] < z_sup)
                ]

                if ensayos_banco.empty:
                    continue

                suma_ley = np.sum(ensayos_banco[col_seleccionada] * ensayos_banco["Longitud"])
                suma_long = np.sum(ensayos_banco["Longitud"])

                ley_comp = suma_ley / suma_long if suma_long > 0 else 0.0

                xi = ensayos_banco["X"].mean()
                yi = ensayos_banco["Y"].mean()
                zi = ensayos_banco["Z"].mean()

                compositos.append({
                    "ID": p_id,
                    "X": round(xi, 2),
                    "Y": round(yi, 2),
                    "Z": round(zi, 2),
                    "Banco Inferior": round(z_inf, 2),
                    "Banco Superior": round(z_sup, 2),
                    "Ley": round(ley_comp, 4)
                })

    # ============================================================
    # 4. TABLA FINAL
    # ============================================================
    df_comp_final = pd.DataFrame(compositos)
    st.session_state["df_comp_final"] = df_comp_final

    st.markdown("### 📋 Tabla de Compositos")
    st.dataframe(df_comp_final, use_container_width=True, height=250)

    crear_boton_excel(df_comp_final, "Compositos")

    st.markdown("---")

    # ============================================================
    # 5. VISUALIZACIÓN 3D (SOLO EN PESTAÑA 7)
    # ============================================================
    st.markdown("### 🌐 Visualización 3D de Compositos")

    fig = go.Figure()

    fig.add_trace(go.Scatter3d(
        x=df_comp_final["X"],
        y=df_comp_final["Y"],
        z=df_comp_final["Z"],
        mode="markers",
        marker=dict(size=4, color=df_comp_final["Ley"], colorscale="Viridis"),
        text=df_comp_final["ID"],
        hoverinfo="text"
    ))

    fig.update_layout(
        height=600,
        scene=dict(aspectmode="data"),
        margin=dict(l=0, r=0, t=40, b=0)
    )

    st.plotly_chart(fig, use_container_width=True)
# ====================================================================
# 📉 PESTAÑA 8 — VARIOGRAFÍA PRO (Estilo Leapfrog Profesional)
# ====================================================================
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.spatial.distance import pdist

with tab8:
    st.markdown("## 📉 Variografía PRO — Geoestadística Avanzada")
    st.caption("Análisis direccional, ajuste teórico interactivo y visualización profesional estilo Leapfrog.")

    # ============================================================
    # 1. CARGA DE DATOS
    # ============================================================
    df_c = st.session_state.get("df_comp_final", pd.DataFrame())
    if df_c.empty:
        st.warning("⚠ No hay compositos disponibles. Genere la base en la Pestaña 7.")
        st.stop()

    coords_m = df_c[["X", "Y", "Z"]].values
    col_ley = "Ley" if "Ley" in df_c.columns else df_c.select_dtypes(include=[np.number]).columns[-1]
    leyes_m = df_c[col_ley].values
    varianza_datos = float(np.var(leyes_m)) if len(leyes_m) > 0 else 1.0

    # ============================================================
    # 2. PANEL IZQUIERDO — CONFIGURACIÓN
    # ============================================================
    col_left, col_right = st.columns([0.38, 0.62])

    with col_left:
        st.markdown("### 🎛️ Parámetros Experimentales")
        n_lags = st.number_input("Número de lags", 1, 30, 8)
        lag_dist = st.number_input("Lag separación (m)", 1.0, 200.0, 20.0)
        tolerancia_t = st.number_input("Tolerancia angular (°)", 5.0, 90.0, 30.0)
        omni_3d = st.checkbox("Omnidireccional 3D", value=False)

        st.markdown("### 🧭 Dirección Principal")
        acimut = st.number_input("Acimut (°)", 0, 360, 18)
        buzamiento = st.number_input("Buzamiento (°)", -90, 90, 65)

        btn_calcular = st.button("🚀 Calcular Variograma Experimental", use_container_width=True)

        # ============================================================
        # 3. AJUSTE TEÓRICO — SLIDERS LEAPFROG
        # ============================================================
        st.markdown("#### 🛠️ Ajuste Teórico (Estructuras)")
        modelo_tipo = st.selectbox(
            "Modelo Matemático:",
            ["spherical", "exponential", "gaussian"],
            key="v_model_type"
        )

        c_mod1, c_mod2 = st.columns(2)

        with c_mod1:
            nugget_val = st.slider(
                "Pepita (Nugget - C0):",
                min_value=0.00,
                max_value=round(varianza_datos, 2),
                value=round(varianza_datos * 0.1, 2),
                step=0.01,
                key="v_nugget"
            )

            sill_val = st.slider(
                "Meseta (Sill - C):",
                min_value=0.01,
                max_value=round(varianza_datos * 2.0, 2),
                value=round(varianza_datos, 2),
                step=0.05,
                key="v_sill"
            )

        with c_mod2:
            range_val = st.slider(
                "Alcance (Range - m):",
                min_value=10,
                max_value=int(n_lags * lag_dist),
                value=int(n_lags * lag_dist * 0.5),
                step=10,
                key="v_range"
            )

    # ============================================================
    # 3. MOTOR EXPERIMENTAL
    # ============================================================
    max_dist_estudio = float(n_lags * lag_dist)
    lags_experimentales = []
    gammas_experimentales = []

    if btn_calcular:
        with st.spinner("Calculando pares geoestadísticos..."):

            if omni_3d:
                if len(coords_m) > 500:
                    np.random.seed(42)
                    idx_m = np.random.choice(len(coords_m), 500, replace=False)
                    c_f, l_f = coords_m[idx_m], leyes_m[idx_m]
                else:
                    c_f, l_f = coords_m, leyes_m

                matriz_dist = pdist(c_f)
                n_m = len(l_f)
                idx_i, idx_j = np.triu_indices(n_m, k=1)
                matriz_semivarianza = 0.5 * ((l_f[idx_i] - l_f[idx_j]) ** 2)

                for step in range(int(n_lags)):
                    d_min = step * lag_dist
                    d_max = (step + 1) * lag_dist
                    filtro_par = (matriz_dist >= d_min) & (matriz_dist < d_max)
                    if np.sum(filtro_par) > 2:
                        lags_experimentales.append((d_min + d_max) / 2)
                        gammas_experimentales.append(np.mean(matriz_semivarianza[filtro_par]))

            else:
                az_rad = np.radians(acimut)
                dip_rad = np.radians(buzamiento)

                v_dir = np.array([
                    np.cos(dip_rad) * np.sin(az_rad),
                    np.cos(dip_rad) * np.cos(az_rad),
                    np.sin(dip_rad)
                ])

                n_muestras = len(coords_m)
                muestreo_max = 400 if n_muestras > 400 else n_muestras

                np.random.seed(42)
                indices_estudio = np.random.choice(n_muestras, muestreo_max, replace=False)

                lags_acum = {s: [] for s in range(int(n_lags))}
                gammas_acum = {s: [] for s in range(int(n_lags))}

                for i in range(len(indices_estudio)):
                    for j in range(i + 1, len(indices_estudio)):
                        idx_i = indices_estudio[i]
                        idx_j = indices_estudio[j]

                        vector_sep = coords_m[idx_i] - coords_m[idx_j]
                        dist_real = np.linalg.norm(vector_sep)

                        if 0 < dist_real <= max_dist_estudio:
                            bin_lag = int(dist_real // lag_dist)
                            if bin_lag >= n_lags:
                                bin_lag = int(n_lags - 1)

                            cos_alpha = np.abs(np.dot(vector_sep, v_dir)) / (dist_real)
                            cos_alpha = np.clip(cos_alpha, -1.0, 1.0)
                            angulo_desviacion = np.degrees(np.arccos(cos_alpha))

                            if angulo_desviacion <= tolerancia_t:
                                semivarianza_par = 0.5 * ((leyes_m[idx_i] - leyes_m[idx_j]) ** 2)
                                lags_acum[bin_lag].append(dist_real)
                                gammas_acum[bin_lag].append(semivarianza_par)

                for s in range(int(n_lags)):
                    if len(lags_acum[s]) > 2:
                        lags_experimentales.append(np.mean(lags_acum[s]))
                        gammas_experimentales.append(np.mean(gammas_acum[s]))

        st.session_state["lags_calculados"] = lags_experimentales
        st.session_state["gammas_calculados"] = gammas_experimentales

    lags_experimentales = st.session_state.get("lags_calculados", [])
    gammas_experimentales = st.session_state.get("gammas_calculados", [])

# ============================================================
# 4–5. CURVA TEÓRICA + GRÁFICO (UNIDOS PARA QUE FUNCIONE EL AJUSTE)
# ============================================================
with col_right:
    st.markdown("### 📈 Ajuste de Estructuras Geoestadísticas")

# 🔄 ACTUALIZAR VALORES DE LOS SLIDERS (ESTO RESTAURA EL NUGGET)
    nugget_val = st.session_state["v_nugget"]
    sill_val = st.session_state["v_sill"]
    range_val = st.session_state["v_range"]
    modelo_tipo = st.session_state["v_model_type"]

    # --- Cálculo teórico ---
    h_curva = np.linspace(0, max_dist_estudio, 200)
    gamma_teorico = np.zeros_like(h_curva)
    c_estructural = float(sill_val) - float(nugget_val)

    # EVITAR DIVISIÓN POR CERO: Si range_val es 0, usamos un valor mínimo casi invisible
    r_val = float(range_val) if float(range_val) > 0 else 1e-6

    if modelo_tipo == "spherical":
        for idx, h in enumerate(h_curva):
            if h <= r_val:
                gamma_teorico[idx] = float(nugget_val) + c_estructural * (
                    1.5 * (h / r_val) - 0.5 * (h / r_val)**3
                )
            else:
                gamma_teorico[idx] = float(sill_val)

    elif modelo_tipo == "exponential":
        gamma_teorico = float(nugget_val) + c_estructural * (
            1.0 - np.exp(-3.0 * h_curva / r_val)
        )

    elif modelo_tipo == "gaussian":
        gamma_teorico = float(nugget_val) + c_estructural * (
            1.0 - np.exp(-3.0 * (h_curva / r_val)**2)
        )

  # --- Gráfico Profesional Leapfrog ---
fig = go.Figure()

# Puntos experimentales
if len(lags_experimentales) > 0:
    fig.add_trace(go.Scatter(
        x=lags_experimentales,
        y=gammas_experimentales,
        mode="markers",
        name="Experimental",
        marker=dict(
            size=11,
            color="#1F77B4",
            line=dict(width=2, color="white"),
            opacity=0.95,
            symbol="circle"
        )
    ))

    fig.add_trace(go.Scatter(
        x=lags_experimentales,
        y=gammas_experimentales,
        mode="lines",
        name="Tendencia Experimental",
        line=dict(color="#1F77B4", width=2, dash="solid"),
        opacity=0.35
    ))

# Curva teórica
fig.add_trace(go.Scatter(
    x=h_curva,
    y=gamma_teorico,
    mode="lines",
    name=f"Modelo {str(modelo_tipo).capitalize()}",
    line=dict(color="#F28E2B", width=4.5)
))

# Línea de varianza global
if varianza_datos is not None:
    fig.add_shape(
        type="line",
        x0=0,
        x1=float(max_dist_estudio),
        y0=float(varianza_datos),
        y1=float(varianza_datos),
        line=dict(color="rgba(80,80,80,0.35)", width=2, dash="dash")
    )

# Layout profesional
fig.update_layout(
    title=dict(
        text="Variograma Experimental vs Teórico",
        font=dict(size=26, family="Segoe UI Semibold"),
        x=0.5,
	
    ),
    xaxis=dict(
        title=dict(text="Distancia de Separación (h) [m]", font=dict(size=16)),
        showgrid=True,
	gridcolor="rgba(180,180,180,0.55)",
       	zeroline=False,
        tickfont=dict(size=14),
    ),
    yaxis=dict(
        title=dict(text="Semivarianza γ(h)", font=dict(size=16)),
        showgrid=True,
        gridcolor="rgba(180,180,180,0.55)",   # Más visible
        zeroline=False,
        tickfont=dict(size=14),
    ),
    plot_bgcolor="rgba(250,250,250,1)",
    paper_bgcolor="white",
    height=580,
    hovermode="closest",
    margin=dict(l=65, r=35, t=70, b=60),
    legend=dict(
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor="rgba(0,0,0,0.15)",
        borderwidth=1,
        font=dict(size=14)
    )
)

fig.update_xaxes(range=[0, float(max_dist_estudio)])
if varianza_datos is not None:
    #fig.update_yaxes(range=[0, float(varianza_datos) * 1.8])
     fig.update_yaxes(range=[0, max(sill_val, varianza_datos) * 1.2])
st.plotly_chart(fig, use_container_width=True)


# ============================================================
# 6. GUARDAR PARÁMETROS
# ============================================================
st.session_state["v_parametros"] = dict(
    modelo=str(modelo_tipo),
    nugget=float(nugget_val),
    sill=float(sill_val),
    range=float(range_val)
)
# ====================================================================
# 🧊 PESTAÑA 9 — MODELO DE BLOQUES 3D (KRIGING SIMPLIFICADO)
# ====================================================================
with tab9:

    st.write("### 🧊 Modelo de Bloques 3D (Kriging Simplificado)")
    st.caption("Estimación de leyes en un modelo de bloques regular usando IDW, compatible con variografía.")

    # Parámetros del modelo de bloques
    col1, col2, col3 = st.columns(3)
    with col1:
        bx = st.number_input("Tamaño bloque X (m):", min_value=10, max_value=100, value=40, step=10)
    with col2:
        by = st.number_input("Tamaño bloque Y (m):", min_value=10, max_value=100, value=40, step=10)
    with col3:
        bz = st.number_input("Tamaño bloque Z (m):", min_value=10, max_value=100, value=20, step=10)

    # Extensión del modelo según collares
    min_x_b = float(df_collar["UTM Este"].min())
    max_x_b = float(df_collar["UTM Este"].max())
    min_y_b = float(df_collar["UTM Norte"].min())
    max_y_b = float(df_collar["UTM Norte"].max())
    min_z_b = float(df_collar["Z_Cota"].min()) - 400
    max_z_b = float(df_collar["Z_Cota"].max())

    x_centros = np.arange(min_x_b, max_x_b + bx, bx)
    y_centros = np.arange(min_y_b, max_y_b + by, by)
    z_centros = np.arange(min_z_b, max_z_b, bz)

    # Selección de ley
    col_ley_b = "Cu_pct" if elemento_render == "Cobre (Cu %)" else "Au_gpt"
    unidad_b = "%" if col_ley_b == "Cu_pct" else "g/t"

    # Recuperar compositos
    df_c = st.session_state.get("df_comp_final", pd.DataFrame())

    if df_c.empty:
        st.warning("⚠️ No hay compositos disponibles. Genera la base en la Pestaña 7.")
        st.stop()

    # Extraer coordenadas y leyes
    coords_assay = df_c[["X", "Y", "Z"]].values
    valores_assay = df_c["Ley"].values

    # 🔥 Filtrar leyes cero
    mask_ley = valores_assay > 0
    coords_assay = coords_assay[mask_ley]
    valores_assay = valores_assay[mask_ley]

    st.info("🔧 Se utilizará un kriging simplificado (IDW) para fines docentes.")

    bx_list, by_list, bz_list, ley_block = [], [], [], []

    # Alcance del variograma (si existe)
    alcance_variograma = st.session_state.get("v_parametros", {}).get("range", 200)

    # Estimación por IDW
    for x0 in x_centros:
        for y0 in y_centros:
            for z0 in z_centros:
                centro = np.array([x0, y0, z0])
                dist = np.linalg.norm(coords_assay - centro, axis=1)

                dist[dist == 0] = 0.1  # evitar división por cero

                mask = dist <= alcance_variograma

                if np.sum(mask) < 3:
                    continue

                w = 1.0 / dist[mask]
                w = w / np.sum(w)
                est_ley = np.sum(w * valores_assay[mask])

                bx_list.append(x0)
                by_list.append(y0)
                bz_list.append(z0)
                ley_block.append(est_ley)

    if len(ley_block) == 0:
        st.warning("⚠️ No se pudieron estimar bloques. Ajusta el alcance o el tamaño de bloque.")
    else:
        df_blocks = pd.DataFrame({
            "X_centro": bx_list,
            "Y_centro": by_list,
            "Z_centro": bz_list,
            f"Ley_{col_ley_b}": ley_block
        })

        st.write("#### 📋 Tabla Resumida del Modelo de Bloques")
        st.dataframe(df_blocks.head(200), use_container_width=True)

        crear_boton_excel(df_blocks, "Modelo_Bloques_Kriging_Simplificado")

        # Visualización 3D del modelo de bloques
        st.write("#### 🛰️ Visualización 3D del Modelo de Bloques")

        fig_blocks = go.Figure()

        fig_blocks.add_trace(go.Scatter3d(
            x=df_blocks["X_centro"],
            y=df_blocks["Y_centro"],
            z=df_blocks["Z_centro"],
            mode="markers",
            marker=dict(
                size=4,
                color=df_blocks[f"Ley_{col_ley_b}"],
                colorscale="Viridis",
                cmin=float(df_blocks[f"Ley_{col_ley_b}"].min()),
                cmax=float(df_blocks[f"Ley_{col_ley_b}"].max()),
                colorbar=dict(title=f"Ley {unidad_b}")
            ),
            name="Bloques Estimados"
        ))

        fig_blocks.update_layout(
            scene=dict(
                xaxis_title="X (UTM Este)",
                yaxis_title="Y (UTM Norte)",
                zaxis_title="Z (Cota)",
                aspectmode="data"
            ),
            margin=dict(l=0, r=0, t=30, b=0),
            title="Modelo de Bloques 3D – Kriging Simplificado"
        )

        st.plotly_chart(fig_blocks, use_container_width=True)
# ====================================================================
# 📈 PESTAÑA 10 — CURVAS LEY–TONELAJE (CORREGIDO Y PROFESIONAL)
# ====================================================================
with tab10:
    st.write("### 📈 Curvas Ley–Tonelaje para Planificación Minera")
    st.caption("Curvas de tonelaje acumulado y ley media ponderada en función de la ley de corte.")

    # Selección de ley
    col_ley = "Cu_pct" if elemento_render == "Cobre (Cu %)" else "Au_gpt"
    unidad = "%" if col_ley == "Cu_pct" else "g/t"

    # Construcción de tabla base desde los ensayos
    df_curvas = df_assays.copy()

    # 🔥 Filtrar bloques con ley > 0
    df_curvas = df_curvas[df_curvas[col_ley] > 0]

    # Tonelaje por tramo (densidad 2.7 t/m³)
    df_curvas["Tonelaje"] = (df_curvas["To"] - df_curvas["From"]) * 2.7

    df_curvas["Ley"] = df_curvas[col_ley]

    # Ordenar por ley descendente
    df_curvas = df_curvas.sort_values("Ley", ascending=False)
    df_curvas["Tonelaje Acumulado (Ton)"] = df_curvas["Tonelaje"].cumsum()

    df_curvas["Ley Media Ponderada Acum."] = (
        (df_curvas["Ley"] * df_curvas["Tonelaje"]).cumsum() /
        df_curvas["Tonelaje Acumulado (Ton)"]
    )

    df_curvas[f"Ley Corte / Intervalo Inferior ({unidad})"] = df_curvas["Ley"]

    df_consolidado = df_curvas[
        [
            f"Ley Corte / Intervalo Inferior ({unidad})",
            "Tonelaje Acumulado (Ton)",
            "Ley Media Ponderada Acum."
        ]
    ]

    st.write("#### 📋 Tabla Consolidada Ley–Tonelaje")
    st.dataframe(df_consolidado, use_container_width=True, hide_index=True, height=250)

    crear_boton_excel(df_consolidado, "Tabla_Consolidacion_Ley_Tonelaje")

    st.write("#### 📈 Curvas Técnicas de Planificación Minera")

    # FIGURA CORRECTA CON DOBLE EJE
    fig_curvas = make_subplots(specs=[[{"secondary_y": True}]])

    # Tonelaje acumulado (eje izquierdo)
    fig_curvas.add_trace(
        go.Scatter(
            x=df_consolidado[f"Ley Corte / Intervalo Inferior ({unidad})"],
            y=df_consolidado["Tonelaje Acumulado (Ton)"],
            name="Tonelaje Acumulado (Ton)",
            mode="lines+markers",
            line=dict(color="#1f77b4", width=3),
            marker=dict(size=6),
        ),
        secondary_y=False
    )

    # Ley media ponderada (eje derecho)
    fig_curvas.add_trace(
        go.Scatter(
            x=df_consolidado[f"Ley Corte / Intervalo Inferior ({unidad})"],
            y=df_consolidado["Ley Media Ponderada Acum."],
            name="Ley Media Ponderada",
            mode="lines+markers",
            line=dict(color="#d62728", width=3, dash="dash"),
            marker=dict(size=6),
        ),
        secondary_y=True
    )

    # Layout profesional
    fig_curvas.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", y=1.15, x=1, xanchor="right"),
        margin=dict(l=40, r=40, t=40, b=40),
        height=550
    )

    # Eje X
    fig_curvas.update_xaxes(title_text=f"Ley Corte ({unidad})")

    # Eje Y izquierdo
    fig_curvas.update_yaxes(
        title_text="Tonelaje Acumulado (Ton)",
        color="#1f77b4",
        secondary_y=False
    )

    # Eje Y derecho
    fig_curvas.update_yaxes(
        title_text=f"Ley Media Ponderada ({unidad})",
        color="#d62728",
        secondary_y=True
    )

    st.plotly_chart(fig_curvas, use_container_width=True)
