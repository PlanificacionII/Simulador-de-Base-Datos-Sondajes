import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io

# Configuración original de la plataforma
st.set_page_config(page_title="Simulador de Base de Datos y Sondajes", layout="wide")

# Inicialización de la memoria interna original
if "df_collar" not in st.session_state:
    st.session_state["df_collar"] = pd.DataFrame()
if "df_assays" not in st.session_state:
    st.session_state["df_assays"] = pd.DataFrame()
if "surveys" not in st.session_state:
    st.session_state["surveys"] = []

# Función de descarga original a Excel
def crear_boton_excel(df, nombre_archivo):
    towrite = io.BytesIO()
    with pd.ExcelWriter(towrite, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos')
    st.download_button(
        label="📥 Exportar Tabla a Excel",
        data=towrite.getvalue(),
        file_name=f"{nombre_archivo}.xlsx",
        mime="application/vnd.ms-excel"
    )

st.title("🎛️ Suite Analítica y Simulador de Base de Datos de Sondajes Geológicos")
st.write("Plataforma interactiva de cátedra para la gestión de sondajes, regularización de muestras y estimación de recursos.")

# Las 8 pestañas originales de su cátedra, sin traducciones raras
tabs = st.tabs([
    "1. Collar", 
    "2. Survey", 
    "3. Assays", 
    "4. Validación", 
    "5. Litologías", 
    "6. Análisis Visual", 
    "7. Compositaje de Pozos", 
    "8. Modelo de Bloques"
])

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = tabs

# --- PESTAÑA 1: COLLAR ---
with tab1:
    st.write("### 📍 Base de Datos de Collar (Coordenadas de Pozos)")
    df_collar_ejemplo = pd.DataFrame({
        "Nombre": ["S001", "S002", "S003"],
        "UTM Este": [450000.0, 450100.0, 450200.0],
        "UTM Norte": [7100000.0, 7100100.0, 7100200.0],
        "Z_Cota": [2500.0, 2480.0, 2465.0],
        "Profundidad Total (m)": [150.0, 200.0, 180.0]
    })
    st.write("Formato requerido de carga:")
    st.dataframe(df_collar_ejemplo, use_container_width=True, hide_index=True)
    
    archivo_collar = st.file_uploader("Cargar Archivo Collar (Excel o CSV):", key="collar_file")
    if archivo_collar:
        if archivo_collar.name.endswith('.csv'):
            st.session_state["df_collar"] = pd.read_csv(archivo_collar)
        else:
            st.session_state["df_collar"] = pd.read_excel(archivo_collar)
        st.success("🎉 ¡Base de datos de Collar cargada con éxito!")
    
    df_collar = st.session_state["df_collar"]
    if not df_collar.empty:
        st.dataframe(df_collar, use_container_width=True, hide_index=True)

# --- PESTAÑA 2: SURVEY ---
with tab2:
    st.write("### 🧭 Base de Datos de Survey (Trayectoria y Desviación)")
    if df_collar.empty:
        st.warning("⚠️ Por favor, cargue primero la base de datos de Collar en la Pestaña 1.")
    else:
        st.write("Ingresa los parámetros de inclinación y rumbo para cada pozo activo:")
        surveys_lista = []
        for p in df_collar["Nombre"].unique():
            st.write(f"**Sondaje: {p}**")
            c1, c2 = st.columns(2)
            with c1:
                az = st.number_input(f"Azimuth / Rumbo (0-360°) para {p}:", min_value=0.0, max_value=360.0, value=0.0, step=10.0, key=f"az_{p}")
            with c2:
                dp = st.number_input(f"Dip / Inclinación (-90° a 0°) para {p}:", min_value=-90.0, max_value=0.0, value=-60.0, step=5.0, key=f"dp_{p}")
            surveys_lista.append({"ID": p, "Azimuth": az, "Dip": dp})
        st.session_state["surveys"] = surveys_lista
        st.success("🧭 Trayectorias de Survey almacenadas correctamente.")

surveys = st.session_state["surveys"]

# --- PESTAÑA 3: ASSAYS ---
with tab3:
    st.write("### 🧪 Base de Datos de Assays (Leyes de Muestreo)")
    df_assays_ejemplo = pd.DataFrame({
        "ID": ["S001", "S001", "S002"],
        "From": [0.0, 5.0, 0.0],
        "To": [5.0, 12.0, 6.5],
        "Cu_pct": [0.45, 1.20, 0.15],
        "Au_gpt": [0.10, 0.55, 0.02]
    })
    st.write("Formato requerido de carga:")
    st.dataframe(df_assays_ejemplo, use_container_width=True, hide_index=True)
    
    archivo_assays = st.file_uploader("Cargar Archivo Assays (Excel o CSV):", key="assays_file")
    if archivo_assays:
        if archivo_assays.name.endswith('.csv'):
            st.session_state["df_assays"] = pd.read_csv(archivo_assays)
        else:
            st.session_state["df_assays"] = pd.read_excel(archivo_assays)
        st.success("🎉 ¡Leyes de muestreo (Assays) cargadas con éxito!")
    
    df_assays = st.session_state["df_assays"]
    if not df_assays.empty:
        st.dataframe(df_assays, use_container_width=True, hide_index=True)

# --- PESTAÑA 4: VALIDACIÓN ---
with tab4:
    st.write("### 🔍 Módulo de Validación de QA/QC de Overlaps y Profundidades")
    if df_collar.empty or df_assays.empty:
        st.warning("⚠️ Se requieren las bases de datos de Collar y Assays activas para ejecutar el control de calidad.")
    else:
        errores_encontrados = []
        for p in df_collar["Nombre"].unique():
            prof_max_c = float(df_collar[df_collar["Nombre"] == p]["Profundidad Total (m)"].values)
            ensayos_p = df_assays[df_assays["ID"] == p].sort_values(by="From")
            
            if ensayos_p.empty: continue
            
            if ensayos_p["To"].max() > prof_max_c:
                errores_encontrados.append(f"❌ Pozo {p}: Las muestras exceden la profundidad máxima de collar ({prof_max_c}m).")
                
            for idx_e in range(len(ensayos_p)-1):
                r1 = ensayos_p.iloc[idx_e]
                r2 = ensayos_p.iloc[idx_e+1]
                if r1["To"] > r2["From"]:
                    errores_encontrados.append(f"❌ Pozo {p}: Superposición de muestras detectada (Overlap) en el tramo {r1['To']}m - {r2['From']}m.")
                    
        if errores_encontrados:
            st.error(f"Se detectaron {len(errores_encontrados)} alertas críticas de consistencia en la base de datos:")
            for err in errores_encontrados:
                st.write(err)
        else:
            st.success("🎉 ¡Base de datos validada al 100%! Cero overlaps detectados y profundidades en perfecta coherencia.")
# --- PESTAÑA 5: LITOLOGÍAS ---
with tab5:
    st.write("### 🪨 Módulo de Modelamiento de Unidades Litológicas")
    if df_assays.empty:
        st.warning("⚠️ Requiere base de datos de muestras activa.")
    else:
        st.write("Asignación de Dominios Litológicos en función de rangos de leyes estimados:")
        elemento_render = st.selectbox("Seleccione Elemento Guía para el Mapeo:", ["Cobre (Cu %)", "Oro (Au g/t)"], key="elem_lito_key")
        
        col_busqueda = "Cu_pct" if elemento_render == "Cobre (Cu %)" else "Au_gpt"
        u_med = "%" if col_busqueda == "Cu_pct" else "g/t"
        
        litos_calculadas = []
        for idx, row in df_assays.iterrows():
            val_ley = float(row[col_busqueda])
            if col_busqueda == "Cu_pct":
                tipo_lito = "Óxidos de Cobre" if val_ley < 0.5 else ("Sulfuros Secundarios" if val_ley < 1.2 else "Sulfuros Primarios (Alta Ley)")
            else:
                tipo_lito = "Zona Lixiviada (Estéril)" if val_ley < 0.3 else ("Beta de Cuarzo-Oro" if val_ley < 2.0 else "Núcleo de Alta Ley Sulfurada")
            litos_calculadas.append(tipo_lito)
            
        df_lito = df_assays.copy()
        df_lito["Unidad Litológica"] = litos_calculadas
        st.dataframe(df_lito[["ID", "From", "To", col_busqueda, "Unidad Litológica"]], use_container_width=True, hide_index=True, height=250)
        crear_boton_excel(df_lito, "Modelo_Litologico_Mapeado")

# --- PESTAÑA 6: ANÁLISIS VISUAL ---
with tab6:
    st.write("### 🛰️ Visualizador Gráfico de Trayectorias y Leyes de Pozos en 3D")
    if df_collar.empty or df_assays.empty or not surveys:
        st.warning("⚠️ Se requieren bases de datos completas y trayectorias definidas para dibujar el modelo.")
    else:
        # Recuperamos la selección de metal de la pestaña 5 de forma segura
        col_render = "Cu_pct" if elemento_render == "Cobre (Cu %)" else "Au_gpt"
        u_graf = "%" if col_render == "Cu_pct" else "g/t"
        
        fig_pozos = go.Figure()
        for idx, row in df_collar.iterrows():
            p_name = row["Nombre"]
            x0, y0, z0 = float(row["UTM Este"]), float(row["UTM Norte"]), float(row["Z_Cota"])
            
            srv_p = next((s for s in surveys if s["ID"] == p_name), None)
            if not srv_p: continue
            
            az_r = np.radians(srv_p["Azimuth"])
            dp_r = np.radians(srv_p["Dip"])
            
            muestras_p = df_assays[df_assays["ID"] == p_name].sort_values(by="From")
            for _, m in muestras_p.iterrows():
                f, t = float(m["From"]), float(m["To"])
                val_l = float(m[col_render])
                
                x_f = x0 + (f * np.cos(dp_r) * np.sin(az_r))
                y_f = y0 + (f * np.cos(dp_r) * np.cos(az_r))
                z_f = z0 + (f * np.sin(dp_r))
                
                x_t = x0 + (t * np.cos(dp_r) * np.sin(az_r))
                y_t = y0 + (t * np.cos(dp_r) * np.cos(az_r))
                z_t = z0 + (t * np.sin(dp_r))
                
                if col_render == "Cu_pct":
                    clr = "green" if val_l < 0.4 else ("orange" if val_l < 1.0 else "red")
                else:
                    clr = "blue" if val_l < 0.5 else ("purple" if val_l < 3.0 else "gold")
                    
                fig_pozos.add_trace(go.Scatter3d(
                    x=[x_f, x_t], y=[y_f, y_t], z=[z_f, z_t],
                    mode='lines+markers',
                    line=dict(color=clr, width=6),
                    marker=dict(size=3, color=clr),
                    name=f"{p_name} ({val_l:.2f} {u_graf})",
                    hoverinfo='text',
                    text=f"Pozo: {p_name}<br>Tramo: {f}-{t}m<br>Ley: {val_l:.2f} {u_graf}"
                ))
                
        config_escena = dict(xaxis=dict(title="Este (X)"), yaxis=dict(title="Norte (Y)"), zaxis=dict(title="Cota (Z)"))
        fig_pozos.update_layout(width=1300, height=650, margin=dict(l=0, r=0, t=10, b=0), scene=config_escena, showlegend=False)
        st.plotly_chart(fig_pozos, use_container_width=True, key="grafico_pozos_3d_key")
# --- PESTAÑA 7: COMPOSITAJE DE POZOS ---
with tab7:
    st.write("### 📐 Módulo de Compositaje de Pozos (Regularización de Soporte)")
    st.write("El compositaje estandariza la longitud de las muestras para eliminar sesgos geométricos antes de la estimación de recursos.")
    
    c_comp1, c_comp2 = st.columns(2)
    with c_comp1:
        tipo_composito = st.selectbox("Selecciona el Método de Compositaje:", ["Longitud Fija (Desde Collar)"], key="metodo_comp_key")
    with c_comp2:
        largo_composito = st.number_input("Longitud del Composito (m):", min_value=5, max_value=30, value=10, step=5, key="largo_comp_key")
        
    st.markdown("---")
    compositos_long = []
    col_comp_elem = "Cu_pct" if elemento_render == "Cobre (Cu %)" else "Au_gpt"
    u_comp_elem = "%" if col_comp_elem == "Cu_pct" else "g/t"
    
    if not df_collar.empty and not df_assays.empty:
        for idx, row in df_collar.iterrows():
            p_id = row["Nombre"]
            ensayos_pozo = df_assays[df_assays["ID"] == p_id].sort_values(by="From")
            srv = next((s for s in surveys if s["ID"] == p_id), None)
            if ensayos_pozo.empty or not srv: continue
            
            prof_max = float(ensayos_pozo["To"].max())
            n_compositos = int(np.ceil(prof_max / largo_composito))
            
            for k in range(n_compositos):
                c_from = k * largo_composito
                c_to = min(c_from + largo_composito, prof_max)
                c_largo = c_to - c_from
                if c_largo <= 0: continue
                
                suma_ley_long, suma_interseccion = 0.0, 0.0
                for _, ensay in ensayos_pozo.iterrows():
                    overlap_from = max(c_from, float(ensay["From"]))
                    overlap_to = min(c_to, float(ensay["To"]))
                    interseccion = overlap_to - overlap_from
                    if interseccion > 0:
                        suma_ley_long += float(ensay[col_comp_elem]) * interseccion
                        suma_interseccion += interseccion
                
                ley_composito = (suma_ley_long / suma_interseccion) if suma_interseccion > 0 else 0.0
                compositos_long.append({
                    "Sondaje ID": p_id, "Desde (m)": round(c_from, 1), "Hasta (m)": round(c_to, 1),
                    "Largo (m)": round(c_largo, 1), f"Ley Comp. ({u_comp_elem})": round(ley_composito, 2)
                })
                
        df_comp_final = pd.DataFrame(compositos_long)
        st.session_state["df_comp_final"] = df_comp_final
        st.dataframe(df_comp_final, use_container_width=True, hide_index=True, height=200)
        crear_boton_excel(df_comp_final, f"Compositos_Longitud_{largo_composito}m")

# --- PESTAÑA 8: MODELO DE BLOQUES ---
with tab8:
    st.write("### 🧱 Módulo de Modelamiento de Bloques y Envolvente Geológica")
    st.caption("Este módulo interpola las leyes de los compositos en una grilla tridimensional utilizando matrices nativas de NumPy.")
    
    st.write("#### 🛠️ Parámetros del Modelo y Ley de Corte (Cut-off)")
    c_bl1, c_bl2, c_bl3 = st.columns(3)
    with c_bl1:
        tamano_bloque = st.number_input("Tamaño del Bloque Cúbico (m):", min_value=5, max_value=20, value=10, step=5, key="size_bloque_key")
    with c_bl2:
        ley_corte = st.number_input(f"Ley de Corte / Cut-off ({u_comp_elem}):", min_value=0.0, max_value=15.0, value=0.40 if col_comp_elem=="Cu_pct" else 2.50, step=0.1, key="cutoff_bloque_key")
    with c_bl3:
        radio_busqueda = st.number_input("Radio de Búsqueda de Compositos (m):", min_value=50, max_value=300, value=120, step=25, key="radio_search_key")
        
    st.markdown("---")
    df_c_origen = st.session_state.get('df_comp_final', pd.DataFrame())
    
    if df_c_origen.empty:
        st.warning("⚠️ Primero debes ingresar a la pestaña '7. Compositaje de Pozos' para inicializar la base de datos de soporte.")
    else:
        xyz_comp = []
        df_m = df_c_origen.merge(df_collar, left_on="Sondaje ID", right_on="Nombre", how="inner")
        if not df_m.empty and "Desde (m)" in df_m.columns:
            srv_df = pd.DataFrame(surveys)
            df_m = df_m.merge(srv_df, left_on="Sondaje ID", right_on="ID", how="inner")
            az_r = np.radians(df_m["Azimuth"].values)
            dp_r = np.radians(df_m["Dip"].values)
            pm = df_m["Desde (m)"].values + ((df_m["Hasta (m)"].values - df_m["Desde (m)"].values) / 2)
            xc = df_m["UTM Este"].values + (pm * np.cos(dp_r) * np.sin(az_r))
            yc = df_m["UTM Norte"].values + (pm * np.cos(dp_r) * np.cos(az_r))
            zc = df_m["Z_Cota"].values + (pm * np.sin(dp_r))
            vl = df_m[f"Ley Comp. ({u_comp_elem})"].values
            xyz_comp = np.column_stack((xc, yc, zc, vl))

        if len(xyz_comp) == 0:
            st.error("❌ No se encontraron compositos estructurados espacialmente en la memoria activa.")
        else:
            if st.button("🚀 CONSTRUIR MODELO DE BLOQUES Y ENVOLVENTE", key="construir_bloques_btn"):
                with st.spinner("Interpolando bloques mediante matriz de distancias..."):
                    min_x, max_x = xyz_comp[:,0].min() - 40, xyz_comp[:,0].max() + 40
                    min_y, max_y = xyz_comp[:,1].min() - 40, xyz_comp[:,1].max() + 40
                    min_z, max_z = xyz_comp[:,2].min() - 50, xyz_comp[:,2].max() + 20
                    grid_x = np.arange(min_x, max_x, tamano_bloque)
                    grid_y = np.arange(min_y, max_y, tamano_bloque)
                    grid_z = np.arange(min_z, max_z, tamano_bloque)
                    mesh_x, mesh_y, mesh_z = np.meshgrid(grid_x, grid_y, grid_z)
                    bx_flat, by_flat, bz_flat = mesh_x.flatten(), mesh_y.flatten(), mesh_z.flatten()
                    
                    bloques_estimados = []
                    for idx_b in range(len(bx_flat)):
                        bx, by, bz = bx_flat[idx_b], by_flat[idx_b], bz_flat[idx_b]
                        distancias = np.sqrt((xyz_comp[:,0] - bx)**2 + (xyz_comp[:,1] - by)**2 + (xyz_comp[:,2] - bz)**2)
                        filtro = distancias <= radio_busqueda
                        d_f, l_f = distancias[filtro], xyz_comp[:,3][filtro]
                        if len(d_f) > 0:
                            d_f = np.where(d_f == 0, 0.001, d_f)
                            pesos = 1.0 / (d_f**2)
                            ley_est = np.sum(l_f * pesos) / np.sum(pesos)
                            cat = "Envolvente Mineralizada (Mena)" if ley_est >= ley_corte else "Roca Caja (Estéril)"
                            bloques_estimados.append({
                                "Centro X (Este)": int(bx), "Centro Y (Norte)": int(by), "Centro Z (Cota)": int(bz),
                                f"Ley Estimada ({u_comp_elem})": round(float(ley_est), 2), "Categoría": cat
                            })
                    df_bloques = pd.DataFrame(bloques_estimados)
                    st.session_state["db_bloques_activa"] = df_bloques
                    st.success(f"🎉 ¡Modelo de bloques construido con éxito! Se cubicaron un total de {len(df_bloques)} bloques.")

            if st.session_state.get("db_bloques_activa") is not None:
                df_b = st.session_state["db_bloques_activa"]
                st.markdown("---")
                st.write("#### 📊 Reporte Analítico de Estimación de Recursos")
                df_mena = df_b[df_b["Categoría"] == "Envolvente Mineralizada (Mena)"]
                n_mena = len(df_mena)
                ley_prom_mena = df_mena[f"Ley Estimada ({u_comp_elem})"].mean() if n_mena > 0 else 0.0
                vol_bloque = tamano_bloque ** 3
                tonelaje_mena = n_mena * vol_bloque * 2.7
                st.metric(label="Masa de Mineral Cubicada", value=f"{tonelaje_mena:,.0f} Ton")
                crear_boton_excel(df_b, f"Modelo_Bloques_Estimado_{tamano_bloque}m")