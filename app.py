import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import io

# ====================================================================
# 🧮 FUNCIONES MATEMÁTICAS Y GEOLÓGICAS (Traducción de Módulos VBA)
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
st.set_page_config(page_title="Simulador Geológico Online", layout="wide")

st.title("⚒️ Software de Simulación Geológica y Campañas de Perforación")
st.markdown("---")

# PANEL LATERAL DE CONTROL
st.sidebar.header("⚙️ Parámetros del Proyecto")

b_este = st.sidebar.number_input("Coordenada ESTE Base (X):", value=369957)
b_norte = st.sidebar.number_input("Coordenada NORTE Base (Y):", value=6986970)
b_cota = st.sidebar.number_input("ELEVACIÓN / Cota Terreno (Z):", value=2200)
var_cota = st.sidebar.number_input("Rugosidad de Topografía (+/- m):", value=15)
espaciamiento = st.sidebar.number_input("Espaciamiento de Malla (m):", value=40)
cant_sondajes = st.sidebar.number_input("Cantidad Total de Pozos:", value=200, step=10)

tipo_yacimiento = st.sidebar.selectbox(
    "Geometría del Depósito:",
    ["Pórfido Cuprífero (Cilíndrico)", "Cuerpo Masivo / Skarn (Botín)", "Veta Estructural (Tabular)"]
)

tipo_malla = st.sidebar.selectbox(
    "Configuración Geométrica:",
    ["Malla Regular (Grilla)", "Malla Dispersa (Scout Drilling)"]
)
# ====================================================================
# ⚙️ MOTOR DE CÁLCULO TRIDIMENSIONAL (Simulación Completa Relacional)
# ====================================================================

collars = []
assays = []
lithologies = []
surveys = []

dimension_malla = espaciamiento * 20
centro_x = b_este + (dimension_malla / 2)
centro_y = b_norte + (dimension_malla / 2)
centro_z = b_cota - 250
radio_porfido = 250

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
    sobrecarga = int(40 + np.random.rand() * 25)
    
    if tipo_yacimiento == "Veta Estructural (Tabular)":
        azimuth = int(90 + np.random.normal(0, 10))
        dip = int(-50 - np.random.rand() * 15)
    else:
        azimuth = int(np.random.rand() * 360)
        dip = -90 if i % 3 == 0 else int(-60 - np.random.rand() * 15)
        
    collars.append({"ID": pozo_id, "X": x, "Y": y, "Z": elev, "Depth": depth, "Type": "Vertical" if dip == -90 else "Inclinado"})
    
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
            plano_falla_z = (b_cota - 200) + 0.5 * (int_x - centro_x) - 0.3 * (int_y - centro_y)
            
            if "Tabular" not in tipo_yacimiento and abs(int_z - plano_falla_z) < 15:
                lit = "Fault_Breccia"
                cu = np.round(max(0.01, normal_random(0.04, 0.01)), 2)
                au = np.round(max(0.005, normal_random(0.02, 0.005)), 2)
            else:
                factor_forma = 0.0
                
                if "Pórfido" in tipo_yacimiento:
                    dist_h = np.sqrt((int_x - centro_x)**2 + (int_y - centro_y)**2)
                    dist_z = abs(int_z - centro_z)
                    factor_forma = np.exp(-(dist_h / 250)**2 - (dist_z / 150)**2)
                    
                elif "Botín" in tipo_yacimiento:
                    dx, dy, dz = int_x - centro_x, int_y - centro_y, int_z - centro_z
                    f_cana = np.exp(-(dx / 130)**2 - (dy / 130)**2 - (dz / 200)**2)
                    if dz < -50: f_cana = 0
                    f_puntera = np.exp(-(dx / 150)**2 - ((dy - 180) / 300)**2 - ((dz + 120) / 80)**2)
                    factor_forma = max(f_cana, f_puntera)
                    
                elif "Tabular" in tipo_yacimiento:
                    dist_plano = abs((int_x - centro_x) - (int_z - centro_z) * np.tan(np.radians(10)))
                    factor_forma = np.exp(-(dist_plano / 15)**2)
                
                dist_superficie = elev - int_z
                es_enriquecido = ("Tabular" not in tipo_yacimiento) and (sobrecarga <= dist_superficie <= sobrecarga + 45)
                
                if factor_forma > 0.45:
                    if es_enriquecido:
                        lit, cu, au = "Supergene_Chalcocite", normal_random(2.5, 0.3), log_normal_from_mean_sd(0.5, 0.1)
                    else:
                        lit = "Quartz_Vein_Core" if "Tabular" in tipo_yacimiento else "Massive_Body_Core"
                        cu = normal_random(1.2, 0.15) * (factor_forma + 0.2)
                        au = log_normal_from_mean_sd(0.6, 0.1) * (factor_forma + 0.2)
                elif factor_forma > 0.12:
                    if es_enriquecido:
                        lit, cu, au = "Enriched_Halo", normal_random(0.9, 0.15), log_normal_from_mean_sd(0.15, 0.04)
                    else:
                        lit = "Stockwork_Halo" if "Tabular" in tipo_yacimiento else "Mineralized_Breccia"
                        cu = normal_random(0.4, 0.1) * (factor_forma + 0.1)
                        au = log_normal_from_mean_sd(0.15, 0.05) * (factor_forma + 0.1)
                else:
                    lit, cu, au = "Country_Rock", np.random.rand() * 0.05, np.random.rand() * 0.02
                    
                cu = np.round(max(0.01, cu), 2)
                au = np.round(max(0.005, au), 2)
                
        lithologies.append({"ID": pozo_id, "From": from_m, "To": to_m, "Lithology": lit})
        assays.append({"ID": pozo_id, "From": from_m, "To": to_m, "Cu_pct": cu, "Au_gpt": au})
        surveys.append({"ID": pozo_id, "Depth": to_m, "Azimuth": azimuth, "Dip": dip})

# Construir los 4 dataframes relacionales
df_collar = pd.DataFrame(collars)
df_assays = pd.DataFrame(assays)
df_lithology = pd.DataFrame(lithologies)
df_surveys = pd.DataFrame(surveys)
# ====================================================================
# 🗂️ DISTRIBUCIÓN VISUAL EN LA PÁGINA WEB (Sección Superior)
# ====================================================================
col_vacia, col_grafico, col_vacia2 = st.columns([1, 4, 1])

with col_grafico:
    st.subheader("🗺️ Plano Técnico: Topografía y Malla de Pozos")
    
    fig = go.Figure()
    min_x, max_x = float(df_collar["X"].min() - espaciamiento), float(df_collar["X"].max() + espaciamiento)
    min_y, max_y = float(df_collar["Y"].min() - espaciamiento), float(df_collar["Y"].max() + espaciamiento)
    rango_y = max_y - min_y
    
    num_curvas = 12
    for c in range(1, num_curvas + 1):
        cota_curva = round(float(df_collar["Z"].min()) + ((float(df_collar["Z"].max()) - float(df_collar["Z"].min())) * (c / (num_curvas + 1))), 0)
        x_linea = np.linspace(min_x, max_x, 40)
        y_base = min_y + espaciamiento + (rango_y * (c / (num_curvas + 1)))
        y_linea = y_base + (espaciamiento * 0.35) * np.sin((x_linea - min_x) / (espaciamiento * 1.8))
        
        fig.add_trace(go.Scatter(
            x=x_linea, y=y_linea, mode='lines',
            line=dict(color='rgba(150, 150, 150, 0.6)', width=1),
            hoverinfo='none', showlegend=False
        ))
        
        fig.add_trace(go.Scatter(
            x=[x_linea[-1]], y=[y_linea[-1]], mode='text',
            text=[f"{int(cota_curva)}m"],
            textposition="middle right",
            textfont=dict(size=9, color="gray"),
            showlegend=False, hoverinfo='none'
        ))
        
    fig.add_trace(go.Scatter(
        x=df_collar["X"], y=df_collar["Y"], mode='markers',
        name='Sondajes',
        marker=dict(color='red', size=6, symbol='circle'),
        text=df_collar["ID"] + "<br>Cota: " + df_collar["Z"].astype(str) + "m",
        hoverinfo='text+x+y', showlegend=False
    ))
    
    fig.update_layout(
        xaxis_title="Coordenada Este (X)", yaxis_title="Coordenada Norte (Y)",
        plot_bgcolor='white', margin=dict(l=40, r=60, t=10, b=40), height=460,
        xaxis=dict(gridcolor='whitesmoke', range=[min_x, max_x + (espaciamiento * 2)]),
        yaxis=dict(gridcolor='whitesmoke', range=[min_y, max_y])
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.subheader("📋 Base de Datos del Proyecto (Hojas de Exploración)")

# NUEVO: Sistema de 4 Pestañas para ver y descargar cada base de datos de forma independiente
tab1, tab2, tab3, tab4 = st.tabs(["📌 1. Collar", "🧪 2. Assays (Leyes)", "🪨 3. Litología", "📐 4. Surveys (Trayectorias)"])

# Función auxiliar técnica para procesar descargas en memoria web
def crear_boton_descarga(dataframe, nombre_archivo):
    buf = io.StringIO()
    dataframe.to_csv(buf, index=False)
    st.download_button(
        label=f"📥 Descargar {nombre_archivo}",
        data=buf.getvalue(),
        file_name=nombre_archivo,
        mime="text/csv"
    )

with tab1:
    st.dataframe(df_collar, use_container_width=True, height=300)
    crear_boton_descarga(df_collar, "Collar.csv")

with tab2:
    st.dataframe(df_assays, use_container_width=True, height=300)
    crear_boton_descarga(df_assays, "Assays.csv")

with tab3:
    st.dataframe(df_lithology, use_container_width=True, height=300)
    crear_boton_descarga(df_lithology, "Litologia.csv")

with tab4:
    st.dataframe(df_surveys, use_container_width=True, height=300)
    crear_boton_descarga(df_surveys, "Surveys.csv")