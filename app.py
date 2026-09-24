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
# ⚙️ MOTOR DE CÁLCULO TRIDIMENSIONAL RELACIONAL
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
    sobrecarga = int(40 + np.random.rand() * 25)
    
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

df_collar = pd.DataFrame(collars)
df_assays = pd.DataFrame(assays)
df_lithology = pd.DataFrame(lithologies)
df_surveys = pd.DataFrame(surveys)
# ====================================================================
# 🗂️ DISTRIBUCIÓN VISUAL EN LA PÁGINA WEB (Corrección st.columns(3))
# ====================================================================
col_izq, col_grafico, col_der = st.columns(3) # NUEVO: Se definió explícitamente el número 3

with col_grafico:
    st.subheader("🛰️ Visualizador Espacial 3D: Trazas de Pozos y Leyes")
    st.caption("🖱️ CONTROL DE MOVIMIENTO: Haz clic izquierdo y arrastra para ROTAR. Usa la rueda del mouse para hacer ZOOM. Haz clic derecho y arrastra para DESPLAZAR (Pan).")
    
    fig = go.Figure()
    
    # 1. GENERAR ALAMBRE TOPOGRÁFICO 3D
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
            line=dict(color='rgba(160, 160, 160, 0.3)', width=1.5),
            showlegend=False, hoverinfo='none'
        ))

    # 2. CONSTRUCCIÓN DE MATRIZ UNIFICADA PURE-NUMERIC DE ALTO CONTRASTE
    columna_ley = "Cu_pct" if elemento_render == "Cobre (Cu %)" else "Au_gpt"
    unidad_ley = "%" if elemento_render == "Cobre (Cu %)" else "g/t"
    
    escala_colores = "Jet" # Paleta térmica clásica minera
    val_max_barra = 1.6 if columna_ley == "Cu_pct" else 0.8 # Calibración del techo visual
    
    x_total, y_total, z_total, leyes_total, textos_total = [], [], [], [], []
    
    for idx, row in df_collar.iterrows():
        p_id = row["ID"]
        ensayos_pozo = [a for a in assays if a["ID"] == p_id]
        srv = next((s for s in surveys if s["ID"] == p_id), None)
        if not srv or not ensayos_pozo: continue
        
        az = np.radians(srv["Azimuth"])
        dp = np.radians(srv["Dip"])
        
        # Inyectar punto inicial (Collar)
        x_total.append(row["X"]); y_total.append(row["Y"]); z_total.append(row["Z"])
        leyes_total.append(0.0)
        textos_total.append(f"<b>{p_id} (Collar)</b><br>Z: {row['Z']}m")
        
        for ens in ensayos_pozo:
            p_m = ens["From"] + 5
            int_x = row["X"] + (p_m * np.cos(dp) * np.sin(az))
            int_y = row["Y"] + (p_m * np.cos(dp) * np.cos(az))
            int_z = row["Z"] + (p_m * np.sin(dp))
            
            x_total.append(int_x); y_total.append(int_y); z_total.append(int_z)
            leyes_total.append(float(ens[columna_ley]))
            
            lit = next((l["Lithology"] for l in lithologies if l["ID"] == p_id and l["From"] == ens["From"]), "Unknown")
            textos_total.append(f"<b>{p_id}</b><br>Tramo: {ens['From']}-{ens['To']}m<br>Lit: {lit}<br>Ley: {ens[columna_ley]:,.2f} {unidad_ley}")
            
        x_total.append(np.nan); y_total.append(np.nan); z_total.append(np.nan)
        leyes_total.append(0.0)
        textos_total.append("")

    # Añadir la traza gigante unificada con espesor grueso para máxima claridad de tramos
    fig.add_trace(go.Scatter3d(
        x=x_total, y=y_total, z=z_total, mode='lines+markers',
        line=dict(
            color=leyes_total, 
            colorscale=escala_colores, 
            width=6, # Traza más gruesa y clara
            cmin=0.0,
            cmax=val_max_barra,
            colorbar=dict(title=f"Leyes ({unidad_ley})", thickness=15, x=0.95)
        ),
        marker=dict(
            size=2.5, 
            color=leyes_total, 
            colorscale=escala_colores,
            cmin=0.0,
            cmax=val_max_barra,
            opacity=0.9
        ),
        text=textos_total, hoverinfo='text', showlegend=False
    ))

    # Ajustes estructurales de la ventana tridimensional
    config_escena = dict(
        xaxis=dict(title="Este (X)", gridcolor="lightgrey", showbackground=True, backgroundcolor="whitesmoke"),
        yaxis=dict(title="Norte (Y)", gridcolor="lightgrey", showbackground=True, backgroundcolor="whitesmoke"),
        zaxis=dict(title="Cota (Z)", gridcolor="lightgrey", showbackground=True, backgroundcolor="whitesmoke"),
        aspectmode="manual",
        aspectratio=dict(x=1, y=1, z=0.5)
    )

    fig.update_layout(
        width=950,
        height=650,
        margin=dict(l=0, r=0, t=10, b=0),
        scene=config_escena
    )
    st.plotly_chart(fig, use_container_width=True)

# TABLAS DE DESCARGA INFERIORES
st.markdown("---")
st.subheader("📋 Base de Datos del Proyecto (Hojas de Exploración)")
tab1, tab2, tab3, tab4 = st.tabs(["📌 1. Collar", "🧪 2. Assays (Leyes)", "🪨 3. Litología", "📐 4. Surveys"])

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