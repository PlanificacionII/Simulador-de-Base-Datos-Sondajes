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
    sobrecarga = int(60 + np.random.rand() * 60)

    if tipo_yacimiento == "Veta Estructural (Tabular)":
        azimuth = int(90 + np.random.normal(0, 10))
        dip = int(-50 - np.random.rand() * 15)
    else:
        azimuth = int(np.random.rand() * 360)
        dip = -90 if i % 3 == 0 else int(-60 - np.random.rand() * 15)

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
            dist_h = np.sqrt((int_x - centro_x) ** 2 + (int_y - centro_y) ** 2)

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
# 🛰️ VISUALIZADOR 3D DE SONDAGES
# ====================================================================
st.subheader("🛰️ Visualizador Espacial 3D Ampliado: Trazas de Pozos y Rangos de Ley")
st.caption("🖱️ CONTROL DE MOVIMIENTO: clic izquierdo para rotar, rueda para zoom, clic derecho para pan.")

fig = go.Figure()

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
    z_linea = round(float(df_collar["Z_Cota"].min()) +
                    ((float(df_collar["Z_Cota"].max()) - float(df_collar["Z_Cota"].min())) * (c / (num_curvas + 1))), 1)
    z_array = np.full_like(x_linea, z_linea)

    fig.add_trace(go.Scatter3d(
        x=x_linea, y=y_linea, z=z_array, mode='lines',
        line=dict(color='rgba(150, 150, 150, 0.3)', width=1.5),
        showlegend=False, hoverinfo='none'
    ))

columna_ley = "Cu_pct" if elemento_render == "Cobre (Cu %)" else "Au_gpt"
unidad_ley = "%" if elemento_render == "Cobre (Cu %)" else "g/t"

x_total, y_total, z_total, codigos_color_total, textos_total = [], [], [], [], []

for idx, row in df_collar.iterrows():
    p_id = row["Nombre"]
    ensayos_pozo = [a for a in assays if a["ID"] == p_id]
    srv = next((s for s in surveys if s["ID"] == p_id), None)
    if not srv or not ensayos_pozo:
        continue

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

        x_total.append(int_x)
        y_total.append(int_y)
        z_total.append(int_z)
        codigos_color_total.append(codigo)

        lit = next((l["Lithology"] for l in lithologies if l["ID"] == p_id and l["From"] == ens["From"]), "Unknown")
        textos_total.append(f"<b>{p_id}</b><br>Tramo: {ens['From']}-{ens['To']}m<br>Lit: {lit}<br>Ley: {val_ley:,.2f} {unidad_ley}")

    x_total.append(np.nan)
    y_total.append(np.nan)
    z_total.append(np.nan)
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
            ticktext=[
                "Estéril (<0.30%)" if columna_ley == "Cu_pct" else "Estéril (<0.9 g/t)",
                "Baja-Media (0.30-1.0%)" if columna_ley == "Cu_pct" else "Baja (0.9-4.0 g/t)",
                "Alta Ley (1.0-1.8%)" if columna_ley == "Cu_pct" else "Alta Ley (4.0-8.0 g/t)",
                "Excelente (>1.80%)" if columna_ley == "Cu_pct" else "Excelente (>8.0 g/t)"
            ]
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

st.plotly_chart(fig, use_container_width=True, key="visor_grafico_3d_unico")

st.markdown("---")
st.subheader("📋 Base de Datos del Proyecto (Hojas de Exploración)")

# ====================================================================
# PESTAÑAS PRINCIPALES
# ====================================================================
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
# PESTAÑA 1: COLLAR
# ====================================================================
with tab1:
    st.dataframe(df_collar.drop(columns=["Z_Cota", "Profundidad"]), use_container_width=True, height=220)
    crear_boton_excel(df_collar, "Collar_Sondajes", ocultar_columnas=["Z_Cota", "Profundidad"])

# ====================================================================
# PESTAÑA 2: ASSAYS
# ====================================================================
with tab2:
    st.dataframe(df_assays, use_container_width=True, height=220)
    crear_boton_excel(df_assays, "Assays_Leyes")

# ====================================================================
# PESTAÑA 3: LITOLOGÍA
# ====================================================================
with tab3:
    st.dataframe(df_lithology, use_container_width=True, height=220)
    crear_boton_excel(df_lithology, "Litologia_Sondajes")

# ====================================================================
# PESTAÑA 4: SURVEYS
# ====================================================================
with tab4:
    st.dataframe(df_surveys, use_container_width=True, height=220)
    crear_boton_excel(df_surveys, "Surveys_Trayectorias")

# ====================================================================
# PESTAÑA 5: CONVERSIÓN KML
# ====================================================================
with tab5:
    st.write("### 🛰️ Módulo de Conversión Geodésica 'EKmlz' Integrado")
    st.write("Carga tu archivo de collares en formato Excel para transformarlo a KML compatible con Google Earth.")

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
                st.success("📊 Base de datos nueva detectada. Presiona el botón para convertir a KML.")

                if st.button("🚀 INICIAR CONVERSIÓN GEODÉSICA"):
                    with st.spinner("Procesando tu nueva simulación..."):
                        kml_objeto = simplekml.Kml(name="Malla de Perforacion Diamantina - Norte de Chile")

                        for idx, row in df_excel_alumno.iterrows():
                            x_utm = float(row["UTM Este"])
                            y_utm = float(row["UTM Norte"])
                            p_nombre = str(row["Nombre"])
                            p_desc = str(row["Descripcion"]) if "Descripcion" in df_excel_alumno.columns else "sondajes"

                            a = 6378137.0
                            f = 1 / 298.257223563
                            b = a * (1 - f)
                            e2 = (a ** 2 - b ** 2) / (a ** 2)
                            e_prim2 = (a ** 2 - b ** 2) / (b ** 2)

                            x_profe = x_utm - 500000.0
                            y_profe = y_utm - 10000000.0

                            c = a / (1 - f)
                            mu = y_profe / (6367449.146)
                            phi = mu

                            for _ in range(5):
                                sin_2phi = np.sin(2 * phi)
                                sin_4phi = np.sin(4 * phi)
                                sin_6phi = np.sin(6 * phi)
                                phi = mu + (3 * e2 / 2 - 27 * e2 ** 2 / 32) * sin_2phi + \
                                      (21 * e2 ** 2 / 16 - 55 * e2 ** 3 / 32) * sin_4phi + \
                                      (151 * e2 ** 3 / 96) * sin_6phi

                            n = c / np.sqrt(1 + e_prim2 * np.cos(phi) ** 2)
                            t = np.tan(phi) ** 2
                            psi = e_prim2 * np.cos(phi) ** 2

                            fact_lat = x_profe / n
                            lat_rad = phi - (fact_lat ** 2 * np.tan(phi) / 2) * \
                                      (1 - (fact_lat ** 2 / 12) * (5 + 3 * t + psi - 9 * t * psi))

                            fact_lon = x_profe / (n * np.cos(phi))
                            lon_rad = fact_lon - (fact_lon ** 3 / 6) * (1 + 2 * t + psi) + \
                                      (fact_lon ** 5 / 120) * (5 + 28 * t + 24 * t ** 2)

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
# PESTAÑA 6: ESTADÍSTICAS DE LEYES
# ====================================================================
with tab6:
    st.write(f"### 📊 Reporte Estadístico y Test de Ajuste de Leyes: **{elemento_render}**")
    st.write("Evaluación de bondad de ajuste mediante prueba K-S y resumen geoestadístico.")

    col_seleccionada = "Cu_pct" if elemento_render == "Cobre (Cu %)" else "Au_gpt"
    leyes_utiles = df_assays[df_assays[col_seleccionada] > 0.0][col_seleccionada].values

    if len(leyes_utiles) == 0:
        st.warning("⚠️ No hay tramos mineralizados disponibles en la simulación actual.")
    else:
        unidad = "%" if col_seleccionada == "Cu_pct" else "g/t"

        st.write("#### 📝 Laboratorio de Inferencia: Prueba de Bondad de Ajuste")
        st.info("Selecciona el modelo teórico y ejecuta la prueba de Kolmogorov-Smirnov (K-S).")

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

            with st.spinner("Calculando estadísticos de contraste probabilísticos..."):
                leyes_limpias = leyes_utiles[np.isfinite(leyes_utiles)]

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

                st.markdown("---")
                st.write("##### 📑 Veredicto Científico del Test:")
                alfa = 0.05

                c1, c2 = st.columns(2)
                with c1:
                    st.metric(label="Estadístico de Contraste (D)", value=f"{stat:.4f}")
                with c2:
                    st.metric(label="P-Valor Calculado (P-value)", value=f"{p_valor:.5f}")

                if p_valor >= alfa:
                    st.success(
                        f"🎉 HIPÓTESIS COMPROBADA: P-valor ({p_valor:.5f}) ≥ {alfa}. "
                        f"No se rechaza H₀. Los datos se ajustan a una distribución {nombre_dist}."
                    )
                else:
                    st.error(
                        f"❌ HIPÓTESIS RECHAZADA: P-valor ({p_valor:.5f}) < {alfa}. "
                        f"Se rechaza H₀. Los datos no se ajustan a una distribución {nombre_dist}."
                    )

        st.markdown("---")
        # ====================================================================
        # 📈 2. CÁLCULO DE PARÁMETROS ESTADÍSTICOS DESCRIPTIVOS MINEROS
        # ====================================================================
        n_muestras = len(leyes_utiles)
        ley_min = float(np.min(leyes_utiles))
        ley_max = float(np.max(leyes_utiles))
        ley_media = float(np.mean(leyes_utiles))
        ley_mediana = float(np.median(leyes_utiles))
        ley_varianza = float(np.var(leyes_utiles, ddof=1)) if n_muestras > 1 else 0.0
        ley_desviacion = float(np.std(leyes_utiles, ddof=1)) if n_muestras > 1 else 0.0
        coef_variacion = (ley_desviacion / ley_media) if ley_media > 0 else 0.0

        st.write("#### 📐 Resumen Geoestadístico Descriptivo del Yacimiento")

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric(label="Total Muestras (n)", value=f"{n_muestras} tramos")
            st.metric(label="Media Aritmética (X)", value=f"{ley_media:.2f} {unidad}")
        with m2:
            st.metric(label="Ley Mínima Detectada", value=f"{ley_min:.2f} {unidad}")
            st.metric(label="Mediana (P50)", value=f"{ley_mediana:.2f} {unidad}")
        with m3:
            st.metric(label="Ley Máxima Detectada", value=f"{ley_max:.2f} {unidad}")
            st.metric(label="Desviación Estándar (s)", value=f"{ley_desviacion:.2f} {unidad}")
        with m4:
            st.metric(label="Varianza Poblacional (s²)", value=f"{ley_varianza:.3f}")
            st.metric(label="Coef. Variación (CV)", value=f"{coef_variacion:.2f}")

        st.markdown("---")
        # ====================================================================
        # 📋 3. TABLA DE FRECUENCIAS (12 INTERVALOS)
        # ====================================================================
        limites = np.linspace(ley_min, ley_max, 13)

        filas_tabla = []
        total_muestras = len(leyes_utiles)
        frecuencia_acumulada_pct = 0.0

        for k in range(12):
            min_int = limites[k]
            max_int = limites[k + 1]

            if k < 11:
                muestras_intervalo = leyes_utiles[(leyes_utiles >= min_int) & (leyes_utiles < max_int)]
            else:
                muestras_intervalo = leyes_utiles[leyes_utiles >= min_int]

            conteo_parcial = len(muestras_intervalo)
            ley_media_intervalo = np.mean(muestras_intervalo) if conteo_parcial > 0 else 0.0
            frecuencia_parcial_pct = (conteo_parcial / total_muestras) * 100
            frecuencia_acumulada_pct += frecuencia_parcial_pct

            rango_texto = f"[{min_int:.2f} - {max_int:.2f})" if k < 11 else f"[{min_int:.2f} - {max_int:.2f}]"

            filas_tabla.append({
                "Intervalos por Categorías": rango_texto,
                f"Ley Media ({unidad})": round(float(ley_media_intervalo), 2),
                "Conteo Parcial": int(conteo_parcial),
                "Frecuencia Parcial (%)": round(float(frecuencia_parcial_pct), 1),
                "Frecuencia Acumulada (%)": round(float(frecuencia_acumulada_pct), 1)
            })

        df_estadistica = pd.DataFrame(filas_tabla)

        st.write("#### 📋 Tabla de Frecuencias Metalúrgicas Resumida (12 Intervalos)")
        st.dataframe(df_estadistica, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.write("#### 📈 Histograma de Distribución y Curva de Densidad Seleccionada")

        import matplotlib.pyplot as plt
        from scipy import stats

        fig_hist, ax_hist = plt.subplots(figsize=(11, 5))

        conteos, bins, parches = ax_hist.hist(
            leyes_utiles, bins=limites, edgecolor="black",
            color="#3498db", alpha=0.6, rwidth=0.92
        )

        ax_hist.set_title(f"Distribución Geoestadística (12 Clases) - {elemento_render}", fontsize=11, fontweight='bold')
        ax_hist.set_xlabel(f"Grado de Ley Metalúrgica ({unidad})", fontsize=10)
        ax_hist.set_ylabel("Cantidad de Muestras (Conteo)", fontsize=10)

        ax_hist.set_xticks(limites)
        plt.xticks(rotation=45, fontsize=8)
        ax_hist.set_xlim(ley_min, ley_max)
        ax_hist.grid(axis='y', linestyle='--', alpha=0.5)

        for k in range(12):
            conteo = conteos[k]
            if conteo > 0:
                bin_centro = (bins[k] + bins[k + 1]) / 2
                ax_hist.text(
                    bin_centro, conteo + (max(conteos) * 0.02),
                    f"{int(conteo)}", ha='center', fontsize=8, fontweight='bold', color='#2c3e50'
                )

        ax_curva = ax_hist.twinx()
        x_eje = np.linspace(ley_min, ley_max, 300)

        curva_activa = st.session_state["tipo_curva_graficar"]

        if curva_activa == "Distribución Normal (Gaussiana)":
            loc, scale = stats.norm.fit(leyes_utiles)
            y_eje = stats.norm.pdf(x_eje, loc, scale)
            label_curva = f"Ajuste Normal Teórico (μ={loc:.2f}, σ={scale:.2f})"

        elif curva_activa == "Distribución Log-Normal (2 Parámetros)":
            shape, loc, scale = stats.lognorm.fit(leyes_utiles, floc=0)
            y_eje = stats.lognorm.pdf(x_eje, shape, loc, scale)
            label_curva = f"Log-Normal 2P (σ_ln={shape:.2f}, e^μ_ln={scale:.2f})"

        elif curva_activa == "Distribución Log-Normal (3 Parámetros - Con Umbral)":
            shape, loc, scale = stats.lognorm.fit(leyes_utiles)
            y_eje = stats.lognorm.pdf(x_eje, shape, loc, scale)
            label_curva = "Log-Normal 3P"

        else:
            loc, scale = stats.expon.fit(leyes_utiles)
            y_eje = stats.expon.pdf(x_eje, loc, scale)
            label_curva = "Exponencial"

        ax_curva.plot(x_eje, y_eje, color="red", linewidth=2, label=label_curva)
        ax_curva.set_ylabel("Densidad de Probabilidad", fontsize=10)
        ax_curva.grid(axis='y', linestyle='--', alpha=0.3)
        ax_curva.legend(loc="upper right", fontsize=8)

        st.pyplot(fig_hist)

# ====================================================================
# PESTAÑA 7: COMPOSITAJE DE POZOS (DOCENTE SIMPLE)
# ====================================================================
with tab7:
    st.write("### 📐 Compositaje de Pozos")
    st.caption("Se genera una base de datos compositada simple para uso en variografía y modelo de bloques.")

    col_ley_comp = "Cu_pct" if elemento_render == "Cobre (Cu %)" else "Au_gpt"
    unidad_comp = "%" if col_ley_comp == "Cu_pct" else "g/t"

    registros_comp = []

    for idx, row_c in df_collar.iterrows():
        p_id = row_c["Nombre"]
        ensayos_pozo = df_assays[df_assays["ID"] == p_id]
        srv = df_surveys[df_surveys["ID"] == p_id].iloc[0]

        az = np.radians(srv["Azimuth"])
        dp = np.radians(srv["Dip"])

        for _, ens in ensayos_pozo.iterrows():
            p_m = ens["From"] + 5
            int_x = float(row_c["UTM Este"]) + (p_m * np.cos(dp) * np.sin(az))
            int_y = float(row_c["UTM Norte"]) + (p_m * np.cos(dp) * np.cos(az))
            int_z = float(row_c["Z_Cota"]) + (p_m * np.sin(dp))

            ley_val = float(ens[col_ley_comp])

            registros_comp.append({
                "ID": p_id,
                "From": ens["From"],
                "To": ens["To"],
                "X": int_x,
                "Y": int_y,
                "Z": int_z,
                "Ley": ley_val
            })

    df_comp_final = pd.DataFrame(registros_comp)

    st.write("#### 📋 Base de Datos Compositada (Simplificada)")
    st.dataframe(df_comp_final.head(300), use_container_width=True)

    crear_boton_excel(df_comp_final, "Compositos_Simplificados")

    st.session_state["df_comp_final"] = df_comp_final
    st.success("💾 Compositos guardados en memoria para uso en variografía y modelo de bloques.")

# ====================================================================
# PESTAÑA 8: VARIOGRAFÍA AVANZADA
# ====================================================================
# ====================================================================
# 📉 PESTAÑA 8 — VARIOGRAFÍA PRO (3D + ANISOTROPÍA + ELIPSOIDES)
# ====================================================================
with tab8:

    st.write("## 📉 Variografía PRO — Geoestadística Avanzada")
    st.caption("Anisotropía 3D • Elipsoides • Cabeceo múltiple • Pares 3D • Exportación GSLib")

    df_c = st.session_state.get("df_comp_final", pd.DataFrame())
    if df_c.empty:
        st.error("⚠ No hay compositos disponibles. Genera la base en la Pestaña 7.")
        st.stop()

    coords = df_c[["X", "Y", "Z"]].values
    leyes = df_c["Ley"].values

    # ================================================================
    # LAYOUT PRO — DOS COLUMNAS
    # ================================================================
    col_left, col_right = st.columns([0.42, 0.58])

    # ================================================================
    # 🟩 PANEL IZQUIERDO — PARÁMETROS
    # ================================================================
    with col_left:
        st.markdown("### 🎛️ Parámetros del Variograma")

        # Geometría del tubo
        st.markdown("#### 🔩 Geometría del Tubo de Búsqueda")
        n_lags = st.number_input("Número de lags", 3, 30, 7)
        lag_sep = st.number_input("Lag separación (m)", 5, 200, 20)
        tol_ang = st.number_input("Tolerancia angular (°)", 5, 90, 30)
        radio_tubo = st.number_input("Radio del tubo (m)", 5, 200, 20)

        # Dirección principal
        st.markdown("#### 🧭 Dirección Principal")
        acimut = st.number_input("Acimut (°)", 0, 360, 18)
        buzamiento = st.number_input("Buzamiento (°)", -90, 90, 65)

        # Anisotropía 3D
        st.markdown("#### 🎚️ Anisotropía 3D (Rotación Completa)")
        rot_x = st.number_input("Rotación X (°)", -180, 180, 0)
        rot_y = st.number_input("Rotación Y (°)", -180, 180, 0)
        rot_z = st.number_input("Rotación Z (°)", -180, 180, 0)

        # Elipsoide de búsqueda
        st.markdown("#### 🟠 Elipsoide de Búsqueda")
        el_a = st.number_input("Eje mayor (m)", 10, 500, 200)
        el_b = st.number_input("Eje intermedio (m)", 10, 500, 120)
        el_c = st.number_input("Eje menor (m)", 10, 500, 60)

        # Cabeceo múltiple
        st.markdown("#### 🎯 Cabeceo Múltiple")
        cab_desde = st.number_input("Desde (°)", -90, 90, 0)
        cab_hasta = st.number_input("Hasta (°)", -90, 90, 180)
        cab_n = st.number_input("Nº variogramas", 1, 20, 9)
        lista_buz = np.linspace(cab_desde, cab_hasta, cab_n)

        # Botón principal
        generar = st.button("🚀 Generar Variogramas PRO")

    # ================================================================
    # 🟦 PANEL DERECHO — RESULTADOS
    # ================================================================
    with col_right:

        if generar:

            # ------------------------------------------------------------
            # FUNCIÓN: ROTACIÓN 3D
            # ------------------------------------------------------------
            def rotar_3d(vec, rx, ry, rz):
                rx, ry, rz = np.radians([rx, ry, rz])
                Rx = np.array([[1, 0, 0],
                               [0, np.cos(rx), -np.sin(rx)],
                               [0, np.sin(rx), np.cos(rx)]])
                Ry = np.array([[np.cos(ry), 0, np.sin(ry)],
                               [0, 1, 0],
                               [-np.sin(ry), 0, np.cos(ry)]])
                Rz = np.array([[np.cos(rz), -np.sin(rz), 0],
                               [np.sin(rz), np.cos(rz), 0],
                               [0, 0, 1]])
                return Rz @ (Ry @ (Rx @ vec))

            # ------------------------------------------------------------
            # FUNCIÓN: ELIPSOIDE DE BÚSQUEDA
            # ------------------------------------------------------------
            def dentro_elipsoide(vec):
                x, y, z = vec
                return (x/el_a)**2 + (y/el_b)**2 + (z/el_c)**2 <= 1

            # ------------------------------------------------------------
            # FUNCIÓN: VECTOR DIRECCIONAL
            # ------------------------------------------------------------
            def vector_direccion(az, dip):
                az_r = np.radians(az)
                dip_r = np.radians(dip)
                v = np.array([
                    np.cos(dip_r) * np.sin(az_r),
                    np.cos(dip_r) * np.cos(az_r),
                    np.sin(dip_r)
                ])
                return rotar_3d(v, rot_x, rot_y, rot_z)

            # ------------------------------------------------------------
            # CÁLCULO DE VARIOGRAMAS MÚLTIPLES
            # ------------------------------------------------------------
            fig_varios = go.Figure()
            pares_3d = []  # para visualización 3D

            for buz in lista_buz:

                v_dir = vector_direccion(acimut, buz)
                max_dist = n_lags * lag_sep

                lags_exp = [[] for _ in range(n_lags)]
                gammas_exp = [[] for _ in range(n_lags)]

                for i in range(len(coords)):
                    for j in range(i + 1, len(coords)):

                        vec = coords[i] - coords[j]
                        vec_rot = rotar_3d(vec, rot_x, rot_y, rot_z)

                        dist = np.linalg.norm(vec_rot)
                        if dist == 0 or dist > max_dist:
                            continue

                        # Elipsoide
                        if not dentro_elipsoide(vec_rot):
                            continue

                        # Ángulo
                        cosang = np.abs(np.dot(vec_rot, v_dir)) / (dist + 1e-9)
                        ang = np.degrees(np.arccos(np.clip(cosang, -1, 1)))

                        if ang <= tol_ang:
                            lag_bin = int(dist // lag_sep)
                            if lag_bin >= n_lags:
                                lag_bin = n_lags - 1

                            semivar = 0.5 * (leyes[i] - leyes[j])**2
                            lags_exp[lag_bin].append(dist)
                            gammas_exp[lag_bin].append(semivar)

                            # Guardar pares para 3D
                            pares_3d.append((coords[i], coords[j]))

                # Promedios
                lag_x = []
                lag_y = []
                for k in range(n_lags):
                    if len(lags_exp[k]) > 0:
                        lag_x.append(np.mean(lags_exp[k]))
                        lag_y.append(np.mean(gammas_exp[k]))

                fig_varios.add_trace(go.Scatter(
                    x=lag_x,
                    y=lag_y,
                    mode="lines+markers",
                    name=f"Buz {buz:.1f}°"
                ))

            # ------------------------------------------------------------
            # MOSTRAR VARIOGRAMAS
            # ------------------------------------------------------------
            fig_varios.update_layout(
                title="Variogramas PRO por Cabeceo",
                xaxis_title="Distancia h (m)",
                yaxis_title="Semivarianza γ(h)",
                height=450
            )
            st.plotly_chart(fig_varios, use_container_width=True)

            # ------------------------------------------------------------
            # VISUALIZACIÓN 3D DE PARES
            # ------------------------------------------------------------
            st.markdown("### 🛰️ Pares Usados (Visualización 3D)")

            fig3d = go.Figure()
            for p1, p2 in pares_3d:
                fig3d.add_trace(go.Scatter3d(
                    x=[p1[0], p2[0]],
                    y=[p1[1], p2[1]],
                    z=[p1[2], p2[2]],
                    mode="lines",
                    line=dict(width=3, color="orange"),
                    showlegend=False
                ))

            fig3d.update_layout(
                height=500,
                scene=dict(
                    xaxis_title="X",
                    yaxis_title="Y",
                    zaxis_title="Z",
                    aspectmode="data"
                )
            )
            st.plotly_chart(fig3d, use_container_width=True)

            # ------------------------------------------------------------
            # EXPORTACIÓN
            # ------------------------------------------------------------
            st.markdown("### 💾 Exportación")

            df_export = pd.DataFrame({
                "Lag": lag_x,
                "Gamma": lag_y
            })

            st.download_button(
                "📥 Exportar CSV",
                df_export.to_csv(index=False).encode("utf-8"),
                "variograma_pro.csv"
            )

            gslib = "Variograma_PRO\n2\nLag\nGamma\n"
            for lx, gy in zip(lag_x, lag_y):
                gslib += f"{lx} {gy}\n"

            st.download_button(
                "📥 Exportar GSLib",
                gslib.encode("utf-8"),
                "variograma_pro.dat"
            )
# ====================================================================
# 🟠 PANEL 3D — ELIPSOIDE DE BÚSQUEDA
# ====================================================================
st.markdown("### 🟠 Elipsoide de Búsqueda (3D)")

# Malla del elipsoide
u = np.linspace(0, 2*np.pi, 40)
v = np.linspace(0, np.pi, 40)

x = el_a * np.outer(np.cos(u), np.sin(v))
y = el_b * np.outer(np.sin(u), np.sin(v))
z = el_c * np.outer(np.ones_like(u), np.cos(v))

# Rotación 3D del elipsoide
def rotar_matriz(X, Y, Z, rx, ry, rz):
    pts = np.vstack([X.flatten(), Y.flatten(), Z.flatten()])
    pts_rot = rotar_3d(pts, rx, ry, rz)
    Xr = pts_rot[0].reshape(X.shape)
    Yr = pts_rot[1].reshape(Y.shape)
    Zr = pts_rot[2].reshape(Z.shape)
    return Xr, Yr, Zr

Xr, Yr, Zr = rotar_matriz(x, y, z, rot_x, rot_y, rot_z)

fig_elip = go.Figure(data=[
    go.Surface(
        x=Xr, y=Yr, z=Zr,
        colorscale="Viridis",
        opacity=0.6,
        showscale=False
    )
])

fig_elip.update_layout(
    title="Elipsoide de Búsqueda Rotado",
    height=500,
    scene=dict(
        xaxis_title="X",
        yaxis_title="Y",
        zaxis_title="Z",
        aspectmode="data"
    )
)

st.plotly_chart(fig_elip, use_container_width=True)
# ====================================================================
# 🧭 PANEL 3D — DIRECCIÓN ANISOTRÓPICA
# ====================================================================
st.markdown("### 🧭 Dirección Anisotrópica (3D)")

v_dir = vector_direccion(acimut, buzamiento)

fig_dir = go.Figure()

# Flecha desde el origen
fig_dir.add_trace(go.Scatter3d(
    x=[0, v_dir[0]*200],
    y=[0, v_dir[1]*200],
    z=[0, v_dir[2]*200],
    mode="lines+markers",
    line=dict(color="red", width=6),
    marker=dict(size=4),
    name="Dirección"
))

fig_dir.update_layout(
    title="Dirección del Variograma (Acimut + Buzamiento + Rotación 3D)",
    height=450,
    scene=dict(
        xaxis_title="X",
        yaxis_title="Y",
        zaxis_title="Z",
        aspectmode="data"
    )
)

st.plotly_chart(fig_dir, use_container_width=True)
# ====================================================================
# 📈 PANEL — VARIOGRAMA EXPERIMENTAL VS TEÓRICO
# ====================================================================
st.markdown("### 📈 Variograma Experimental vs Modelo Teórico")

modelo_teorico = st.selectbox(
    "Modelo Teórico",
    ["Esférico", "Exponencial", "Gaussiano"]
)

# Curva teórica
h = np.linspace(0, max(lag_x), 200)
if modelo_teorico == "Esférico":
    gamma_teo = [
        nugget_val + (sill_val - nugget_val)*(1.5*(d/range_val) - 0.5*(d/range_val)**3)
        if d <= range_val else sill_val
        for d in h
    ]
elif modelo_teorico == "Exponencial":
    gamma_teo = nugget_val + (sill_val - nugget_val)*(1 - np.exp(-3*h/range_val))
else:
    gamma_teo = nugget_val + (sill_val - nugget_val)*(1 - np.exp(-3*(h/range_val)**2))

fig_comp = go.Figure()

# Experimental
fig_comp.add_trace(go.Scatter(
    x=lag_x,
    y=lag_y,
    mode="markers",
    name="Experimental",
    marker=dict(size=8, color="blue")
))

# Teórico
fig_comp.add_trace(go.Scatter(
    x=h,
    y=gamma_teo,
    mode="lines",
    name=f"Modelo {modelo_teorico}",
    line=dict(color="red", width=3)
))

fig_comp.update_layout(
    title="Comparación Variograma Experimental vs Teórico",
    xaxis_title="Distancia h (m)",
    yaxis_title="Semivarianza γ(h)",
    height=450
)

st.plotly_chart(fig_comp, use_container_width=True)
# ====================================================================
# 📈 PANEL — VARIOGRAMA EXPERIMENTAL VS TEÓRICO
# ====================================================================
st.markdown("### 📈 Variograma Experimental vs Modelo Teórico")

modelo_teorico = st.selectbox(
    "Modelo Teórico",
    ["Esférico", "Exponencial", "Gaussiano"]
)

# Curva teórica
h = np.linspace(0, max(lag_x), 200)
if modelo_teorico == "Esférico":
    gamma_teo = [
        nugget_val + (sill_val - nugget_val)*(1.5*(d/range_val) - 0.5*(d/range_val)**3)
        if d <= range_val else sill_val
        for d in h
    ]
elif modelo_teorico == "Exponencial":
    gamma_teo = nugget_val + (sill_val - nugget_val)*(1 - np.exp(-3*h/range_val))
else:
    gamma_teo = nugget_val + (sill_val - nugget_val)*(1 - np.exp(-3*(h/range_val)**2))

fig_comp = go.Figure()

# Experimental
fig_comp.add_trace(go.Scatter(
    x=lag_x,
    y=lag_y,
    mode="markers",
    name="Experimental",
    marker=dict(size=8, color="blue")
))

# Teórico
fig_comp.add_trace(go.Scatter(
    x=h,
    y=gamma_teo,
    mode="lines",
    name=f"Modelo {modelo_teorico}",
    line=dict(color="red", width=3)
))

fig_comp.update_layout(
    title="Comparación Variograma Experimental vs Teórico",
    xaxis_title="Distancia h (m)",
    yaxis_title="Semivarianza γ(h)",
    height=450
)

st.plotly_chart(fig_comp, use_container_width=True)

# ====================================================================
# PESTAÑA 9: MODELO DE BLOQUES (KRIGING SIMPLIFICADO) + 3D
# ====================================================================
with tab9:
    st.write("### 🧊 Modelo de Bloques 3D (Kriging Simplificado)")
    st.caption("Se construye un modelo de bloques regular a partir de los sondajes simulados y se visualiza en 3D.")

    col1, col2, col3 = st.columns(3)
    with col1:
        bx = st.number_input("Tamaño bloque X (m):", min_value=10, max_value=100, value=40, step=10)
    with col2:
        by = st.number_input("Tamaño bloque Y (m):", min_value=10, max_value=100, value=40, step=10)
    with col3:
        bz = st.number_input("Tamaño bloque Z (m):", min_value=10, max_value=100, value=20, step=10)

    min_x_b = float(df_collar["UTM Este"].min())
    max_x_b = float(df_collar["UTM Este"].max())
    min_y_b = float(df_collar["UTM Norte"].min())
    max_y_b = float(df_collar["UTM Norte"].max())
    min_z_b = float(df_collar["Z_Cota"].min()) - 400
    max_z_b = float(df_collar["Z_Cota"].max())

    x_centros = np.arange(min_x_b, max_x_b + bx, bx)
    y_centros = np.arange(min_y_b, max_y_b + by, by)
    z_centros = np.arange(min_z_b, max_z_b, bz)

    col_ley_b = "Cu_pct" if elemento_render == "Cobre (Cu %)" else "Au_gpt"
    unidad_b = "%" if col_ley_b == "Cu_pct" else "g/t"

    coords_assay = []
    valores_assay = []

    for idx, row_c in df_collar.iterrows():
        p_id = row_c["Nombre"]
        ensayos_pozo = df_assays[df_assays["ID"] == p_id]
        srv = df_surveys[df_surveys["ID"] == p_id].iloc[0]

        az = np.radians(srv["Azimuth"])
        dp = np.radians(srv["Dip"])

        for _, ens in ensayos_pozo.iterrows():
            p_m = ens["From"] + 5
            int_x = float(row_c["UTM Este"]) + (p_m * np.cos(dp) * np.sin(az))
            int_y = float(row_c["UTM Norte"]) + (p_m * np.cos(dp) * np.cos(az))
            int_z = float(row_c["Z_Cota"]) + (p_m * np.sin(dp))

            val = float(ens[col_ley_b])
            if val > 0.0:
                coords_assay.append([int_x, int_y, int_z])
                valores_assay.append(val)

    coords_assay = np.array(coords_assay)
    valores_assay = np.array(valores_assay)

    if len(coords_assay) == 0:
        st.warning("⚠️ No hay datos mineralizados para construir el modelo de bloques.")
    else:
        st.info("🔧 Se utilizará un kriging muy simplificado (inverso de la distancia) para fines docentes.")

        bx_list, by_list, bz_list, ley_block = [], [], [], []

        alcance_default = 200
        alcance_variograma = st.session_state.get("v_parametros", {}).get("range", alcance_default)

        for x0 in x_centros:
            for y0 in y_centros:
                for z0 in z_centros:
                    centro = np.array([x0, y0, z0])
                    dist = np.linalg.norm(coords_assay - centro, axis=1)

                    dist[dist == 0] = 0.1

                    radio_inf = alcance_variograma
                    mask = dist <= radio_inf

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
            st.warning("⚠️ No se pudieron estimar bloques con la configuración actual. Ajusta el alcance o el tamaño de bloque.")
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
# 📈 PESTAÑA 10: CURVAS LEY–TONELAJE (CORREGIDO Y PROFESIONAL)
# ====================================================================
from plotly.subplots import make_subplots

with tab10:
    st.write("### 📈 Curvas Ley–Tonelaje para Planificación Minera")
    st.caption("Curvas de tonelaje acumulado y ley media ponderada en función de la ley de corte.")

    # Construcción de tabla base desde los ensayos
    df_curvas = df_assays.copy()

    # Tonelaje por tramo (densidad 2.7 t/m³)
    df_curvas["Tonelaje"] = (df_curvas["To"] - df_curvas["From"]) * 2.7

    col_ley = "Cu_pct" if elemento_render == "Cobre (Cu %)" else "Au_gpt"
    unidad = "%" if col_ley == "Cu_pct" else "g/t"
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
