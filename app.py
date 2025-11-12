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
    layout="wide"
)

# Logo en header
col_logo, col_titulo = st.columns([1, 4])
with col_logo:
    st.image("mbtb.png", width=120)
with col_titulo:
    st.title("Sistema Mi Bici Tu Bici - Rosario")
    st.markdown("**Distrito Centro** | Simulación de Eventos Discretos")

st.markdown("---")

# CSS personalizado - TEMA CLARO
st.markdown("""
    <style>
    /* Fondo general blanco */
    .stApp {
        background-color: #ffffff;
    }
    
    /* Cards de resultados con borde celeste */
    .resultado-box {
        background-color: #f8fcff;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #00b4d8;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Título principal */
    h1 {
        color: #0077b6;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #e3f2fd;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        color: #0077b6;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #0077b6;
        color: white;
    }
    
    /* Botón principal */
    .stButton>button {
        background-color: #00b4d8;
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-size: 16px;
    }
    
    .stButton>button:hover {
        background-color: #0096c7;
        border: none;
    }
    
    /* Métricas */
    [data-testid="stMetricValue"] {
        color: #0077b6;
        font-size: 24px;
    }
    </style>
    """, unsafe_allow_html=True)


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

tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🎮 Simulador Interactivo", "📈 Resultados Empíricos"])

# ─────────────────────────────────────────────────────────
# TAB 1: DASHBOARD
# ─────────────────────────────────────────────────────────

with tab1:
    st.header("Resumen del Sistema")
    
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
    st.subheader("Comparación de Escenarios Analizados")
    st.dataframe(df_resumen, use_container_width=True, hide_index=True)
    
    st.info("ℹ️ El sistema está **naturalmente balanceado**: las devoluciones compensan los retiros en el largo plazo. La búsqueda binaria encontró el stock óptimo en solo 15 evaluaciones.")

# ─────────────────────────────────────────────────────────
# TAB 2: SIMULADOR (CONTROLES INTEGRADOS)
# ─────────────────────────────────────────────────────────

with tab2:
    st.header("Simulador de Escenarios")
    
    # CONTROLES EN COLUMNAS (NO SIDEBAR)
    st.markdown("### ⚙️ Configuración del Escenario")
    
    col_s0, col_demanda, col_leak = st.columns(3)
    
    with col_s0:
        s0_usuario = st.number_input(
            "📦 Stock Inicial (S₀)",
            min_value=0,
            max_value=150,
            value=67,
            step=5,
            help="Bicis disponibles al inicio de la simulación"
        )
    
    with col_demanda:
        factor_demanda = st.slider(
            "📈 Factor Demanda (m)",
            min_value=0.5,
            max_value=2.0,
            value=1.0,
            step=0.1,
            help="1.0 = demanda actual, 1.5 = +50% de arribos"
        )
    
    with col_leak:
        leak_usuario = st.slider(
            "🔴 Leak (%)",
            min_value=0.0,
            max_value=20.0,
            value=0.6,
            step=0.5,
            help="% de bicis que no retornan al sistema"
        )
    
    col_hz, col_reps = st.columns(2)
    
    with col_hz:
        horizonte_dias = st.selectbox(
            "🕐 Horizonte Temporal",
            options=[7, 14, 30],
            index=0,
            format_func=lambda x: f"{x} días"
        )
    
    with col_reps:
        n_replicas = st.selectbox(
            "🔁 Réplicas Monte Carlo",
            options=[100, 300, 500, 1000],
            index=1
        )
    
    # BOTÓN GRANDE
    st.markdown("---")
    boton_simular = st.button("🚀 EJECUTAR SIMULACIÓN", type="primary", use_container_width=True)
    
    # RESULTADOS
    if boton_simular:
        with st.spinner("⏳ Simulando... (esto puede tomar 10-30 segundos)"):
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
        
        # MÉTRICAS EN CARDS
        pct_medio = resultados['pct_rechazos_media']
        ic_low, ic_up = resultados['pct_rechazos_ic95']
        cumple = ic_up < 5.0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            color_rechazo = "#28a745" if cumple else "#dc3545"
            st.markdown(f"""
            <div class="resultado-box">
            <h3 style="color: #555;">% Rechazos Promedio</h3>
            <h1 style="color: {color_rechazo};">{pct_medio:.2f}%</h1>
            <p style="color: #777;">IC95: [{ic_low:.2f}%, {ic_up:.2f}%]</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="resultado-box">
            <h3 style="color: #555;">Stock Promedio</h3>
            <h1 style="color: #0077b6;">{resultados['stock_promedio']:.1f}</h1>
            <p style="color: #777;">Utilización: {resultados['stock_promedio']/s0_usuario*100:.0f}%</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            estado = "✅ CUMPLE" if cumple else "❌ NO CUMPLE"
            color = "#28a745" if cumple else "#dc3545"
            st.markdown(f"""
            <div class="resultado-box">
            <h3 style="color: #555;">Criterio (IC95 < 5%)</h3>
            <h1 style="color: {color};">{estado}</h1>
            <p style="color: #777;">Nivel de servicio: {100-ic_up:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)

        
        # GRÁFICO DE DISTRIBUCIÓN
        st.markdown("---")
        st.subheader("Distribución Empírica de Rechazos (Monte Carlo)")
        
        fig = go.Figure()
        fig.add_histogram(
            x=resultados['distribucion_rechazos'],
            nbinsx=40,
            name='Frecuencia',
            marker_color='rgba(0, 119, 182, 0.6)',  # ← Azul del logo
            marker_line_color='white',
            marker_line_width=1
        )
        fig.add_vline(x=5, line_dash="dash", line_color="red", line_width=3,
                     annotation_text="Umbral 5%", annotation_position="top right")
        fig.add_vline(x=pct_medio, line_dash="dot", line_color="green", line_width=2,
                     annotation_text=f"Media: {pct_medio:.1f}%", annotation_position="top left")
              fig.update_layout(
            xaxis_title="% Rechazos por Réplica",
            yaxis_title="Frecuencia",
            height=450,
            template='plotly_white',  # ← TEMA CLARO
            hovermode='x'
        )

        st.plotly_chart(fig, use_container_width=True)
        
        # INTERPRETACIÓN AUTOMÁTICA
        st.markdown("### 💬 Interpretación")
        if cumple:
            st.success(f"✅ **Escenario viable.** Con S₀={s0_usuario} bicis y los parámetros seleccionados, el sistema garantiza <5% de rechazos con 95% de confianza. El nivel de servicio esperado es del {100-ic_up:.1f}%.")
        else:
            st.error(f"❌ **Escenario insuficiente.** El IC95 superior ({ic_up:.1f}%) supera el umbral del 5%. Se recomienda aumentar S₀ o reducir el factor de demanda. Nivel de servicio: {100-ic_up:.1f}%.")
    
    else:
        st.info("👆 Ajustá los parámetros arriba y presioná **EJECUTAR SIMULACIÓN**")

# ─────────────────────────────────────────────────────────
# TAB 3: ANÁLISIS EMPÍRICO
# ─────────────────────────────────────────────────────────

with tab3:
    st.header("Resultados del Análisis Empírico")
    st.subheader("Curva de Sensibilidad: S₀ vs % Rechazos")
    
    fig = go.Figure()
    fig.add_scatter(
        x=df_resultados['S0'],
        y=df_resultados['pct_medio'],
        mode='lines+markers',
        name='% Rechazos',
        line=dict(color='cyan', width=3),
        marker=dict(size=8)
    )
    fig.add_hline(y=5, line_dash="dash", line_color="red",
                 annotation_text="Umbral 5%", annotation_position="right")
    fig.add_vline(x=parametros['s0_recomendado'], line_dash="dot",
                 line_color="lime", annotation_text=f"S₀ óptimo = {parametros['s0_recomendado']}")
     fig.update_layout(
        xaxis_title="Stock Inicial (S₀)",
        yaxis_title="% Rechazos Medio",
        height=500,
        template='plotly_white'  # ← TEMA CLARO
    )

    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Metadata del Análisis")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Observaciones", f"{metadata['n_observaciones']:,}")
    with col2:
        st.metric("Período", f"{metadata['periodo_inicio']} / {metadata['periodo_fin']}")
    with col3:
        st.metric("Evaluaciones DES", metadata['n_evaluaciones'])

# FOOTER
st.markdown("---")
st.markdown("**Desarrollado por:** Stefanía Fiorotto | **Curso:** Modelos y Simulación 2025 | **Método:** DES + Bootstrap + Búsqueda Binaria")





