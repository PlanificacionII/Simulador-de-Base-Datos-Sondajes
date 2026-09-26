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
# 🗂️ DISTRIBUCIÓN VISUAL: VISUALIZADOR 3D ÚNICO Y SECCIÓN DE PESTAÑAS
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

# 🔒 CONTROL ÚNICO: Se dibuja el cubo 3D una sola vez acoplándole un ID exclusivo
st.plotly_chart(fig, use_container_width=True, key="visor_grafico_3d_unico")

st.markdown("---")
st.subheader("📋 Base de Datos del Proyecto (Hojas de Exploración)")

# Inicializar las 6 pestañas reglamentarias unificadas
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
                            e_prim2 = (a**2 - b**2) / (b**2)
                            
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
with tab6:
    st.write(f"### 📊 Reporte Estadístico y Test de Ajuste de Leyes: **{elemento_render}**")
    st.write("Esta sección permite evaluar la bondad de ajuste de las leyes simuladas mediante una prueba formal de hipótesis estadísticas.")
    
    col_seleccionada = "Cu_pct" if elemento_render == "Cobre (Cu %)" else "Au_gpt"
    leyes_utiles = df_assays[df_assays[col_seleccionada] > 0.0][col_seleccionada].values
    
    if len(leyes_utiles) == 0:
        st.warning("⚠️ No hay tramos mineralizados disponibles en la simulación actual para calcular estadísticas.")
    else:
        unidad = "%" if col_seleccionada == "Cu_pct" else "g/t"
        
        # ====================================================================
        # 🔬 1. MÓDULO INTERACTIVO: TEST DE AJUSTE Y PRUEBA DE HIPÓTESIS
        # ====================================================================
        st.write("#### 📝 Laboratorio de Inferencia: Prueba de Bondad de Ajuste")
        st.info("🎯 **Instrucciones para el estudiante:** Evalúa el comportamiento de la ley en el visualizador 3D. Luego, selecciona qué función matemática crees que describe mejor la distribución de este yacimiento y presiona el botón para validar tu hipótesis.")
        
        # Componente de selección activa para el alumno
        hipotesis_alumno = st.radio(
            "Selecciona tu Hipótesis Nula (H₀): 'Los datos de las leyes se ajustan a una función...'",
            ["Distribución Normal (Gaussiana)", "Distribución Log-Normal (2 Parámetros)"]
        )
        
        if st.button("🧪 EVALUAR TEST DE AJUSTE"):
            from scipy import stats
            
            with st.spinner("Calculando estadísticos de contraste probabilísticos..."):
                # Filtro de seguridad: remover infinitos o nan por si acaso
                leyes_limpias = leyes_utiles[np.isfinite(leyes_utiles)]
                
                if hipotesis_alumno == "Distribución Normal (Gaussiana)":
                    # Prueba de Shapiro-Wilk o Kolmogorov-Smirnov dependiendo del tamaño muestral
                    if len(leyes_limpias) <= 5000:
                        stat, p_valor = stats.shapiro(leyes_limpias)
                    else:
                        stat, p_valor = stats.kstest(leyes_limpias, 'norm', args=(np.mean(leyes_limpias), np.std(leyes_limpias)))
                    
                    nombre_dist = "Normal"
                    
                else:
                    # Distribución Log-Normal de 2 parámetros (datos deben ser > 0)
                    leyes_log = leyes_limpias[leyes_limpias > 0]
                    if len(leyes_log) > 0:
                        # Transformamos a escala logarítmica para evaluar su normalidad
                        datos_transformados = np.log(leyes_log)
                        if len(datos_transformados) <= 5000:
                            stat, p_valor = stats.shapiro(datos_transformados)
                        else:
                            stat, p_valor = stats.kstest(datos_transformados, 'norm', args=(np.mean(datos_transformados), np.std(datos_transformados)))
                    else:
                        p_valor = 0.0
                    
                    nombre_dist = "Log-Normal"

                # Mostrar resultados analíticos en pantalla
                st.markdown("---")
                st.write("##### 📑 Veredicto Científico del Test:")
                
                # Nivel de significancia minera estándar (alfa = 5%)
                alfa = 0.05
                
                c1, c2 = st.columns(2)
                with c1:
                    st.metric(label="Estadístico de Contraste", value=f"{stat:.4f}")
                with c2:
                    st.metric(label="P-Valor Calculado (P-value)", value=f"{p_valor:.5f}")
                
                if p_valor >= alfa:
                    st.success(f"🎉 **¡HIPÓTESIS COMPROBADA!** El P-valor ({p_valor:.5f}) es mayor o igual a {alfa}. Por lo tanto, **NO se rechaza H₀**. Los datos acumulados **SÍ se ajustan satisfactoriamente** a una distribución **{nombre_dist}**.")
                else:
                    st.error(f"❌ **¡HIPÓTESIS RECHAZADA!** El P-valor ({p_valor:.5f}) es menor a {alfa}. Por lo tanto, **se rechaza H₀**. Los datos metalúrgicos **NO se ajustan** a una distribución {nombre_dist}. Evalúa el otro modelo teórico.")
                    
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
        # 📋 3. PROCESAMIENTO MATEMÁTICO DE LOS 12 INTERVALOS DE CLASE
        # ====================================================================
        limites = np.linspace(ley_min, ley_max, 13) # Genera 12 intervalos perfectos
        
        filas_tabla = []
        total_muestras = len(leyes_utiles)
        frecuencia_acumulada_pct = 0.0
        
        for k in range(12):
            min_int = limites[k]
            max_int = limites[k+1]
            
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
        st.write("#### 📈 Histograma de Distribución y Curva de Densidad Teórica")
        
        # ====================================================================
        # 📈 4. VISUALIZACIÓN GRÁFICA DE LAS 12 BARRAS CON CURVA DE AJUSTE
        # ====================================================================
        import matplotlib.pyplot as plt
        from scipy import stats
        
        fig_hist, ax_hist = plt.subplots(figsize=(11, 5))
        
        # Graficar el histograma normalizado en densidad para poder superponer la curva matemática
        conteos, bins, parches = ax_hist.hist(
            leyes_utiles, bins=limites, edgecolor="black", 
            color="#3498db", alpha=0.6, rwidth=0.92, density=False
        )
        
        ax_hist.set_title(f"Distribución Geoestadística del Proyecto (12 Clases) - {elemento_render}", fontsize=11, fontweight='bold')
        ax_hist.set_xlabel(f"Grado de Ley Metalúrgica ({unidad})", fontsize=10)
        ax_hist.set_ylabel("Cantidad de Muestras (Conteo)", fontsize=10)
        
        ax_hist.set_xticks(limites)
        plt.xticks(rotation=45, fontsize=8)
        ax_hist.set_xlim(ley_min, ley_max)
        ax_hist.grid(axis='y', linestyle='--', alpha=0.5)
        
        # Inyectar las etiquetas numéricas de conteo exacto sobre cada una de las 12 barritas
        for k in range(12):
            conteo = conteos[k]
            if conteo > 0:
                bin_centro = (bins[k] + bins[k+1]) / 2
                ax_hist.text(
                    bin_centro, conteo + (max(conteos) * 0.02), 
                    f"{int(conteo)}", ha='center', fontsize=8, fontweight='bold', color='#2c3e50'
                )

        # 🚀 CURVA TÉCNICA: Dibujar un segundo eje para graficar la campana ideal según el tipo de yacimiento
        ax_curva = ax_hist.twinx()
        x_eje = np.linspace(ley_min, ley_max, 200)
        
        # Si el yacimiento simula oro o cobre masivo, proyectamos la curva teórica Log-Normal
        if col_seleccionada == "Au_gpt" or "Pórfido" in tipo_yacimiento:
            shape, loc, scale = stats.lognorm.fit(leyes_utiles, floc=0)
            y_eje = stats.lognorm.pdf(x_eje, shape, loc, scale)
            label_curva = "Ajuste Teórico Log-Normal"
        else:
            loc, scale = stats.norm.fit(leyes_utiles)
            y_eje = stats.norm.pdf(x_eje, loc, scale)
            label_curva = "Ajuste Teórico Normal"
            
        ax_curva.plot(x_eje, y_eje, color="#e74c3c", linewidth=2.5, label=label_curva)
        ax_curva.set_ylabel("Densidad de Probabilidad", color="#e74c3c", fontsize=9)
        ax_curva.tick_params(axis='y', labelcolor="#e74c3c")
        
        # Unificar leyendas gráficas
        ax_hist.plot([], [], color="#e74c3c", linewidth=2.5, label=label_curva)
        ax_hist.legend(loc="upper right")

        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        st.image(buf, use_container_width=True)
        plt.close()
        
        st.write("*(Opcional) Descarga la hoja de frecuencias y estadísticas descriptivas:*")
        crear_boton_excel(df_estadistica, f"Reporte_Estadistico_{col_seleccionada}")