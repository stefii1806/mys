import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import heapq
from pathlib import Path

# ============================================
# CONFIGURACIÓN
# ============================================

st.set_page_config(
    page_title="Mi Bici Tu Bici - Simulador",
    page_icon="🚴",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# FORZAR TEMA CLARO
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background-color: #ffffff !important;
    }
    
    [data-testid="stHeader"] {
        background-color: #ffffff !important;
    }
    
    .main {
        background-color: #ffffff !important;
    }
    
    .stApp {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
    }
    </style>
    """, unsafe_allow_html=True)

# CSS personalizado - VERSIÓN FINAL
st.markdown("""
    <style>
    /* Fuente global */    
    html, body, [class*="css"], * {
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Roboto', sans-serif !important;
    }
    
    /* Fondo blanco */
    .stApp {
        background-color: #ffffff;
    }
    
    /* Texto general oscuro */
    .stMarkdown, p, span, div {
        color: #1a1a1a !important;
    }
    
    /* Cards de resultados */
    .resultado-box {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        padding: 25px;
        border-radius: 12px;
        border-left: 6px solid #0077b6;
        box-shadow: 0 4px 6px rgba(0,0,0,0.15);
    }
    
    .resultado-box h3 {
        color: #0d47a1 !important;
        font-weight: 600;
        margin-bottom: 10px;
    }
    
    .resultado-box h1 {
        font-weight: 700;
        margin: 10px 0;
    }
    
    .resultado-box p {
        color: #424242 !important;
        font-size: 14px;
    }
    
    /* Títulos */
    h1, h2, h3 {
        color: #0077b6 !important;
        font-family: 'Segoe UI', sans-serif !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f5f5f5;
        padding: 10px;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #e8e8e8;
        border-radius: 8px 8px 0 0;
        padding: 12px 24px;
        color: #0077b6;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #e3f2fd !important;
        color: #0d47a1 !important;
        font-weight: 600;
    }
    
    /* Fondo para el contenido de cada tab */
    .stTabs [data-baseweb="tab-panel"] {
        background-color: #f8f9fa !important;
        padding: 30px !important;
        border-radius: 0 12px 12px 12px !important;
        margin-top: -1px !important;
    }
    
    /* Tabla personalizada */
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Segoe UI', sans-serif;
        background-color: white !important;
        margin: 20px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .custom-table thead {
        background-color: #e3f2fd !important;
    }
    
    .custom-table thead tr {
        background-color: #e3f2fd !important;
    }
    
    .custom-table thead th {
        background-color: #e3f2fd !important;
        color: #0d47a1 !important;
        text-align: left;
        font-weight: 600;
        padding: 14px 16px;
        border: 1px solid #90caf9;
    }
    
    .custom-table tbody td {
        padding: 12px 16px;
        border: 1px solid #e0e0e0;
        color: #1a1a1a;
    }
    
    .custom-table tbody tr:nth-of-type(even) {
        background-color: #f9f9f9;
    }
    
    .custom-table tbody tr:nth-of-type(odd) {
        background-color: #ffffff;
    }
    
    .custom-table tbody tr:hover {
        background-color: #e8f4f8;
    }
    
    /* Botón principal */
    .stButton>button {
        background: linear-gradient(135deg, #0096c7 0%, #0077b6 100%);
        color: white !important;
        font-weight: bold;
        border: none;
        border-radius: 10px;
        padding: 14px 28px;
        font-size: 18px;
        font-family: 'Segoe UI', sans-serif;
        box-shadow: 0 4px 8px rgba(0,119,182,0.3);
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #0077b6 0%, #005f8c 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,119,182,0.4);
    }
    
    /* Métricas */
    [data-testid="stMetricValue"] {
        color: #0077b6 !important;
        font-size: 28px;
        font-weight: 700;
        font-family: 'Segoe UI', sans-serif;
    }
    
    [data-testid="stMetricLabel"] {
        color: #424242 !important;
        font-weight: 600;
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* Info boxes */
    .stAlert {
        background-color: #e3f2fd;
        border-left: 4px solid #0077b6;
    }
    
    /* Selectbox, sliders, inputs */
    .stSelectbox label, .stSlider label, .stNumberInput label {
        color: #0d47a1 !important;
        font-weight: 600;
        font-family: 'Segoe UI', sans-serif;
    }

        /* Sliders - Azul oscuro */
    .stSlider > div > div > div > div {
        background-color: #0077b6 !important;
    }
    
    .stSlider [role="slider"] {
        background-color: #0077b6 !important;
    }
    
    /* Desplegables - Fondo claro */
    .stSelectbox > div > div {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
    }
    
    .stSelectbox select {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
    }
    
    /* Dropdown menu */
    [data-baseweb="popover"] {
        background-color: #ffffff !important;
    }
    
    [data-baseweb="menu"] {
        background-color: #ffffff !important;
    }
    
    [role="option"] {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
    }
    
    [role="option"]:hover {
        background-color: #e3f2fd !important;
    }
    
    /* Number input - Fondo claro */
    .stNumberInput input {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
    }
    
    .stNumberInput button {
        background-color: #f0f0f0 !important;
        color: #1a1a1a !important;
    }

    </style>
    """, unsafe_allow_html=True)

# ============================================
# HEADER CON LOGO
# ============================================

col_logo, col_titulo = st.columns([0.5, 5])
with col_logo:
    st.image("mbtb.png", width=80)
with col_titulo:
    st.markdown("# Sistema Mi Bici, Tu Bici - Rosario")
    st.markdown("**Distrito Centro** | Simulación de eventos discretos (DES) + Montecarlo")

st.markdown("---")

# ============================================
# CARGAR DATOS
# ============================================

@st.cache_data
def cargar_datos():
    data_dir = Path("data")
    with open(data_dir / "parametros_simulacion.json", 'r') as f:
        parametros = json.load(f)
    interarribos = np.load(data_dir / "interarribos_empiricos.npy")
    duraciones = np.load(data_dir / "duraciones_empiricas.npy")
    df_resultados = pd.read_csv(data_dir / "resultados_busqueda_binaria.csv")
    df_resumen = pd.read_csv(data_dir / "resumen_ejecutivo.csv")
    with open(data_dir / "metadata_analisis.json", 'r') as f:
        metadata = json.load(f)
    return parametros, interarribos, duraciones, df_resultados, df_resumen, metadata

parametros, interarribos_emp, duraciones_emp, df_resultados, df_resumen, metadata = cargar_datos()

# ============================================
# FUNCIÓN DES
# ============================================

def simular_escenario(s0, factor_demanda, leak_pct, horizonte_dias, n_reps, 
                      interarribos, duraciones):
    tiempo_sim = horizonte_dias * 24 * 60
    leak_prob = leak_pct / 100.0
    rechazos_lista = []
    stock_prom_lista = []
    
    for rep in range(n_reps):
        np.random.seed(42 + rep)
        stock = s0
        t = 0.0
        rechazos = 0
        llegadas = 0
        historico_stock = []
        eventos = []
        inter = np.random.choice(interarribos) / factor_demanda
        heapq.heappush(eventos, (inter, 'arribo'))
        
        while eventos:
            t, tipo = heapq.heappop(eventos)
            if t > tiempo_sim:
                break
            
            if tipo == 'arribo':
                llegadas += 1
                if stock > 0:
                    stock -= 1
                    if np.random.rand() > leak_prob:
                        dur = float(np.random.choice(duraciones))
                        heapq.heappush(eventos, (t + dur, 'retorno'))
                else:
                    rechazos += 1
                inter = np.random.choice(interarribos) / factor_demanda
                prox = t + inter
                if prox < tiempo_sim:
                    heapq.heappush(eventos, (prox, 'arribo'))
            elif tipo == 'retorno':
                stock += 1
            historico_stock.append(stock)
        
        pct_rech = (rechazos / llegadas * 100) if llegadas > 0 else 0
        rechazos_lista.append(pct_rech)
        stock_prom_lista.append(np.mean(historico_stock) if historico_stock else s0)
    
    return {
        'pct_rechazos_media': float(np.mean(rechazos_lista)),
        'pct_rechazos_ic95': (float(np.percentile(rechazos_lista, 2.5)),
                              float(np.percentile(rechazos_lista, 97.5))),
        'stock_promedio': float(np.mean(stock_prom_lista)),
        'distribucion_rechazos': rechazos_lista
    }

# ============================================
# TABS
# ============================================

tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🎮 Simulador interactivo", "📈 Resultados empíricos"])

# ─────────────────────────────────────────────────────────
# TAB 1: DASHBOARD
# ─────────────────────────────────────────────────────────

with tab1:
    st.header("Resumen del sistema")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🚴 λ (arribos/h)", f"{parametros['lambda_global']:.2f}")
    with col2:
        st.metric("⏱️ Duración media", f"{parametros['duracion_media_min']:.0f} min")
    with col3:
        st.metric("🔴 Leak empírico", f"{parametros['leak_mediana']*100:.1f}%")
    with col4:
        st.metric("✅ S₀ óptimo", f"{parametros['s0_recomendado']} bicis")
    
    st.markdown("---")
    st.subheader("Comparación de escenarios analizados")
    
    # Convertir a HTML personalizado
    html_table = df_resumen.to_html(index=False, escape=False, classes='custom-table')
    
    st.markdown("""
    <style>
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Segoe UI', sans-serif;
        background-color: white;
        margin: 20px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .custom-table thead {
        background-color: #e3f2fd !important;
    }
    
    .custom-table thead tr {
        background-color: #e3f2fd !important;
    }
    
    .custom-table thead th {
        background-color: #e3f2fd !important;
        color: #0d47a1 !important;
        text-align: left;
        font-weight: 600;
        padding: 14px 16px;
        border: 1px solid #90caf9;
    }
    
    .custom-table tbody td {
        padding: 12px 16px;
        border: 1px solid #e0e0e0;
        color: #1a1a1a;
    }
    
    .custom-table tbody tr:nth-of-type(even) {
        background-color: #f9f9f9;
    }
    
    .custom-table tbody tr:nth-of-type(odd) {
        background-color: #ffffff;
    }
    
    .custom-table tbody tr:hover {
        background-color: #e8f4f8;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown(html_table, unsafe_allow_html=True)
    
    st.info("ℹ️ El sistema está **naturalmente balanceado**: las devoluciones compensan los retiros en el largo plazo. La búsqueda binaria encontró el stock óptimo en solo 15 evaluaciones.")

# ─────────────────────────────────────────────────────────
# TAB 2: SIMULADOR
# ─────────────────────────────────────────────────────────

with tab2:
    st.header("Simulador de escenarios")
    
    st.markdown("### ⚙️ Configuración del escenario")
    
    col_s0, col_demanda, col_leak = st.columns(3)
    
    with col_s0:
        s0_usuario = st.number_input(
            "📦 Stock Inicial (S₀)",
            min_value=0,
            max_value=150,
            value=67,
            step=5,
            help="Bicis disponibles al inicio"
        )
    
    with col_demanda:
        factor_demanda = st.slider(
            "📈 Factor demanda (m)",
            min_value=0.5,
            max_value=2.0,
            value=1.0,
            step=0.1,
            help="1.0 = actual, 1.5 = +50%"
        )
    
    with col_leak:
        leak_usuario = st.slider(
            "🔴 Leak (%)",
            min_value=0.0,
            max_value=20.0,
            value=0.6,
            step=0.5,
            help="% bicis que no retornan"
        )
    
    col_hz, col_reps = st.columns(2)
    
    with col_hz:
        horizonte_dias = st.selectbox(
            "🕐 Horizonte temporal",
            options=[7, 14, 30],
            index=0,
            format_func=lambda x: f"{x} días"
        )
    
    with col_reps:
        n_replicas = st.selectbox(
            "🔁 Réplicas Montecarlo",
            options=[100, 300, 500, 1000],
            index=1
        )
    
    st.markdown("---")
    boton_simular = st.button("🚀 EJECUTAR SIMULACIÓN", type="primary", use_container_width=True)
    
    if boton_simular:
        with st.spinner("⏳ Simulando..."):
            resultados = simular_escenario(
                s0=s0_usuario,
                factor_demanda=factor_demanda,
                leak_pct=leak_usuario,
                horizonte_dias=horizonte_dias,
                n_reps=n_replicas,
                interarribos=interarribos_emp,
                duraciones=duraciones_emp
            )
        
        st.success("✅ Simulación completada")
        
        pct_medio = resultados['pct_rechazos_media']
        ic_low, ic_up = resultados['pct_rechazos_ic95']
        cumple = ic_up < 5.0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            color_rechazo = "#2e7d32" if cumple else "#c62828"
            st.markdown(f"""
            <div class="resultado-box">
            <h3>% Rechazos Promedio</h3>
            <h1 style="color: {color_rechazo};">{pct_medio:.2f}%</h1>
            <p>IC95: [{ic_low:.2f}%, {ic_up:.2f}%]</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="resultado-box">
            <h3>Stock Promedio</h3>
            <h1 style="color: #01579b;">{resultados['stock_promedio']:.1f}</h1>
            <p>Utilización: {resultados['stock_promedio']/s0_usuario*100:.0f}%</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            estado = "✅ CUMPLE" if cumple else "❌ NO CUMPLE"
            color = "#2e7d32" if cumple else "#c62828"
            st.markdown(f"""
            <div class="resultado-box">
            <h3>Criterio (IC95 < 5%)</h3>
            <h1 style="color: {color};">{estado}</h1>
            <p>Nivel de servicio: {100-ic_up:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("Distribución empírica de rechazos (Montecarlo)")
        
        fig = go.Figure()
        fig.add_histogram(
            x=resultados['distribucion_rechazos'],
            nbinsx=40,
            name='Frecuencia',
            marker_color='rgba(0, 119, 182, 0.6)',
            marker_line_color='white',
            marker_line_width=1
        )
        fig.add_vline(x=5, line_dash="dash", line_color="red", line_width=3,
                     annotation_text="Umbral 5%", annotation_position="top right")
        fig.add_vline(x=pct_medio, line_dash="dot", line_color="green", line_width=2,
                     annotation_text=f"Media: {pct_medio:.1f}%", annotation_position="top left")
        fig.update_layout(
            xaxis_title="% Rechazos por réplica",
            yaxis_title="Frecuencia",
            height=450,
            template='plotly_white',
            hovermode='x'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### 💬 Interpretación")
        if cumple:
            st.success(f"✅ **Escenario viable.** Con S₀={s0_usuario} bicis, el sistema garantiza <5 % rechazos con 95 % confianza. Nivel de servicio: {100-ic_up:.1f}%.")
        else:
            st.error(f"❌ **Insuficiente.** IC95 superior ({ic_up:.1f}%) > 5 %. Aumentar S₀ o reducir demanda. Nivel de servicio: {100-ic_up:.1f}%.")
    
    else:
        st.info("👆 Ajustar los parámetros y presionar **EJECUTAR SIMULACIÓN**")

# ─────────────────────────────────────────────────────────
# TAB 3: ANÁLISIS EMPÍRICO
# ─────────────────────────────────────────────────────────

with tab3:
    st.header("Resultados del análisis empírico")
    st.subheader("Curva de sensibilidad: S₀ vs % rechazos")
    
    fig = go.Figure()
    fig.add_scatter(
        x=df_resultados['S0'],
        y=df_resultados['pct_medio'],
        mode='lines+markers',
        name='% Rechazos',
        line=dict(color='#0077b6', width=3),
        marker=dict(size=8)
    )
    fig.add_hline(y=5, line_dash="dash", line_color="red",
                 annotation_text="Umbral 5%", annotation_position="right")
    fig.add_vline(x=parametros['s0_recomendado'], line_dash="dot",
                 line_color="green", annotation_text=f"S₀ óptimo = {parametros['s0_recomendado']}")
    fig.update_layout(
        xaxis_title="Stock Inicial (S₀)",
        yaxis_title="% Rechazos Medio",
        height=500,
        template='plotly_white',
        paper_bgcolor='#ffffff',
        plot_bgcolor='#ffffff',
        font=dict(color='#1a1a1a')
    )


    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Metadata del análisis")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Observaciones", f"{metadata['n_observaciones']:,}")
    with col2:
        st.metric("Evaluaciones DES", metadata['n_evaluaciones'])

# FOOTER
st.markdown("---")
st.markdown("**Desarrollado por:** Stefania Cuicchi | **Curso:** Modelos y Simulación 2025, LAyGD, UNSL | **Método:** DES + Bootstrap + Búsqueda binaria")










