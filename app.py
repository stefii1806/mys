import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import heapq
from pathlib import Path

# ============================================
# CONFIGURACIÓN DE LA APP
# ============================================

st.set_page_config(
    page_title="Simulador Ecobici Rosario",
    page_icon="🚴",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .big-font {font-size:20px !important; font-weight:bold;}
    .metric-box {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        margin: 8px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================
# CARGAR DATOS
# ============================================

@st.cache_data
def cargar_datos():
    """Carga todos los archivos exportados desde Colab"""
    data_dir = Path("data")
    
    # Parámetros
    with open(data_dir / "parametros_simulacion.json", 'r') as f:
        parametros = json.load(f)
    
    # Datos empíricos
    interarribos = np.load(data_dir / "interarribos_empiricos.npy")
    duraciones = np.load(data_dir / "duraciones_empiricas.npy")
    
    # Resultados del análisis
    df_resultados = pd.read_csv(data_dir / "resultados_busqueda_binaria.csv")
    df_resumen = pd.read_csv(data_dir / "resumen_ejecutivo.csv")
    
    # Metadata
    with open(data_dir / "metadata_analisis.json", 'r') as f:
        metadata = json.load(f)
    
    return parametros, interarribos, duraciones, df_resultados, df_resumen, metadata

# Cargar datos
parametros, interarribos_emp, duraciones_emp, df_resultados, df_resumen, metadata = cargar_datos()

# ============================================
# FUNCIÓN DE SIMULACIÓN (DES)
# ============================================

def simular_escenario(s0, factor_demanda, leak_pct, horizonte_dias, n_reps, 
                      interarribos, duraciones):
    """
    Simulación DES con parámetros ajustables.
    Retorna: dict con métricas agregadas
    """
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
        
        # Primer arribo (escalado por factor demanda)
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
                    # Aplicar leak
                    if np.random.rand() > leak_prob:
                        dur = float(np.random.choice(duraciones))
                        heapq.heappush(eventos, (t + dur, 'retorno'))
                else:
                    rechazos += 1
                
                # Próximo arribo
                inter = np.random.choice(interarribos) / factor_demanda
                prox = t + inter
                if prox < tiempo_sim:
                    heapq.heappush(eventos, (prox, 'arribo'))
                    
            elif tipo == 'retorno':
                stock += 1
            
            historico_stock.append(stock)
        
        # Métricas
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
# SIDEBAR - CONTROLES
# ============================================

st.sidebar.title("🎛️ Controles de Simulación")

st.sidebar.markdown("### 📦 Stock Inicial")
s0_usuario = st.sidebar.slider(
    "S₀ (bicis disponibles)",
    min_value=0,
    max_value=150,
    value=parametros['s0_recomendado'],
    step=5,
    help="Stock inicial de bicis en Distrito Centro"
)

st.sidebar.markdown("### 📈 Demanda")
factor_demanda = st.sidebar.slider(
    "Factor de demanda (m)",
    min_value=0.5,
    max_value=2.0,
    value=1.0,
    step=0.1,
    help="Multiplica la tasa de arribos λ. 1.0 = demanda actual, 1.5 = +50%"
)

st.sidebar.markdown("### 🔴 Leak (Fuga)")
leak_usuario = st.sidebar.slider(
    "% de bicis que no retornan",
    min_value=0.0,
    max_value=20.0,
    value=parametros['leak_mediana']*100,
    step=0.5,
    help="Porcentaje de viajes donde la bici no vuelve al sistema"
)

st.sidebar.markdown("### ⚙️ Simulación")
horizonte_dias = st.sidebar.selectbox(
    "Horizonte temporal",
    options=[7, 14, 30],
    index=0,
    format_func=lambda x: f"{x} días"
)

n_replicas = st.sidebar.selectbox(
    "Réplicas Monte Carlo",
    options=[100, 300, 500],
    index=1
)

boton_simular = st.sidebar.button("🚀 SIMULAR", type="primary", use_container_width=True)

# ============================================
# VISTA PRINCIPAL
# ============================================

st.title("🚴 Simulador de Sistema Ecobici - Distrito Centro")
st.markdown("**Análisis de escenarios con Monte Carlo | Modelos y Simulación**")

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Resumen Ejecutivo", "🎮 Simulador", "📈 Análisis Original"])

# --- TAB 1: RESUMEN ---
with tab1:
    st.header("Situación Actual del Sistema")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("λ (arribos)", f"{parametros['lambda_global']:.2f} /h")
    with col2:
        st.metric("Duración media", f"{parametros['duracion_media_min']:.1f} min")
    with col3:
        st.metric("Leak empírico", f"{parametros['leak_mediana']*100:.1f}%")
    with col4:
        st.metric("S₀ recomendado", f"{parametros['s0_recomendado']} bicis")
    
    st.info("ℹ️ El sistema está **balanceado**: las devoluciones compensan los retiros en el largo plazo.")
    
    st.subheader("Comparación de Escenarios")
    st.dataframe(df_resumen, use_container_width=True, hide_index=True)

# --- TAB 2: SIMULADOR ---
with tab2:
    st.header("Simular Escenario Personalizado")
    
    if boton_simular:
        with st.spinner("🔄 Simulando... (esto puede tomar unos segundos)"):
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
        
        # Métricas principales
        col1, col2, col3 = st.columns(3)
        
        pct_medio = resultados['pct_rechazos_media']
        ic_low, ic_up = resultados['pct_rechazos_ic95']
        
        with col1:
            delta_color = "inverse" if pct_medio < 5 else "normal"
            st.metric(
                "% Rechazos",
                f"{pct_medio:.2f}%",
                delta=f"IC95: [{ic_low:.1f}%, {ic_up:.1f}%]"
            )
        
        with col2:
            st.metric(
                "Stock Promedio",
                f"{resultados['stock_promedio']:.1f} bicis",
                delta=f"{resultados['stock_promedio']/s0_usuario*100:.0f}% de S₀"
            )
        
        with col3:
            cumple = "✅ Cumple" if ic_up < 5 else "❌ No cumple"
            st.metric("Criterio (IC95<5%)", cumple)
        
        # Gráfico de distribución
        st.subheader("Distribución de % Rechazos")
        fig_hist = go.Figure()
        fig_hist.add_histogram(x=resultados['distribucion_rechazos'], 
                              nbinsx=30, name='Frecuencia',
                              marker_color='steelblue')
        fig_hist.add_vline(x=5, line_dash="dash", line_color="red",
                         annotation_text="Umbral 5%")
        fig_hist.update_layout(
            xaxis_title="% Rechazos",
            yaxis_title="Frecuencia",
            height=400,
            template='plotly_white'
        )
        st.plotly_chart(fig_hist, use_container_width=True)
        
        # Interpretación
        if ic_up < 5:
            st.success(f"✅ **ESCENARIO VIABLE**: Con S₀={s0_usuario} y estos parámetros, "
                      f"el sistema cumple el criterio de servicio (<5% rechazos).")
        elif pct_medio < 5:
            st.warning(f"⚠️ **BORDERLINE**: El promedio es aceptable pero el IC95 superior "
                      f"({ic_up:.1f}%) supera el 5%. Considerar aumentar S₀.")
        else:
            st.error(f"❌ **INSUFICIENTE**: Con estos parámetros se esperan {pct_medio:.1f}% "
                    f"de rechazos. Aumentar S₀ o mejorar el leak.")
    
    else:
        st.info("👈 Ajustá los parámetros en el panel izquierdo y presioná **SIMULAR**")

# --- TAB 3: ANÁLISIS ORIGINAL ---
with tab3:
    st.header("Resultados del Análisis Original")
    
    st.subheader("Curva de Sensibilidad S₀ vs % Rechazos")
    
    # Gráfico original
    fig = go.Figure()
    fig.add_scatter(x=df_resultados['S0'], y=df_resultados['pct_medio'],
                   mode='lines+markers', name='% Rechazos',
                   line=dict(color='steelblue', width=3))
    fig.add_hline(y=5, line_dash="dash", line_color="red",
                 annotation_text="Umbral 5%")
    fig.add_vline(x=parametros['s0_recomendado'], line_dash="dot",
                 line_color="green", annotation_text=f"S₀={parametros['s0_recomendado']}")
    fig.update_layout(
        xaxis_title="Stock Inicial (S₀)",
        yaxis_title="% Rechazos",
        height=500,
        template='plotly_white'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Metadata del Análisis")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Observaciones", f"{metadata['n_observaciones']:,}")
    with col2:
        st.metric("Período", f"{metadata['periodo_inicio']} - {metadata['periodo_fin']}")
    with col3:
        st.metric("Evaluaciones", metadata['n_evaluaciones'])

# Footer
st.markdown("---")
st.markdown("**Desarrollado para:** Trabajo Práctico de Modelos y Simulación | **Método:** Simulación de eventos discretos (DES) con búsqueda binaria")
