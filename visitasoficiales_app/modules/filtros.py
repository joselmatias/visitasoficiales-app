"""
filtros.py — Panel de filtros en el sidebar
Proporciona controles de filtrado para país, tipo de actividad y rango de fechas
Retorna el DataFrame filtrado para pasarlo al mapa
"""

import pandas as pd
import streamlit as st
from datetime import date


# Lista fija de tipos de actividad para la versión de prueba
TIPOS_ACTIVIDAD = [
    "Firma de Convenio",
    "Conferencia Internacional",
    "Visita Técnica",
    "Reunión Bilateral",
    "Foro / Cumbre",
    "Visita Oficial",
]

# Lista de países disponibles en la versión de prueba
PAISES_PRUEBA = ["Japón", "Alemania", "Colombia"]


def _inicializar_estado() -> None:
    """
    Inicializa los valores predeterminados de los filtros en session_state
    si aún no existen. Se llama una vez al arrancar la app.
    """
    if "filtro_pais" not in st.session_state:
        st.session_state["filtro_pais"] = "Todos"
    if "filtro_tipos" not in st.session_state:
        st.session_state["filtro_tipos"] = TIPOS_ACTIVIDAD.copy()
    if "filtro_fecha_inicio" not in st.session_state:
        st.session_state["filtro_fecha_inicio"] = date(2024, 1, 1)
    if "filtro_fecha_fin" not in st.session_state:
        st.session_state["filtro_fecha_fin"] = date(2024, 12, 31)


def renderizar_filtros(df: pd.DataFrame) -> pd.DataFrame:
    """
    Renderiza los controles de filtro en el sidebar y aplica el filtrado
    al DataFrame recibido.

    Parámetros:
        df (pd.DataFrame): DataFrame original con todas las visitas.

    Retorna:
        pd.DataFrame: DataFrame filtrado según los controles del usuario.
    """
    _inicializar_estado()

    st.sidebar.markdown("## Filtros")
    st.sidebar.markdown("---")

    # ── Filtro por país ───────────────────────────────────────────────────────
    pais_seleccionado = st.sidebar.selectbox(
        label="País",
        options=["Todos"] + PAISES_PRUEBA,
        index=(["Todos"] + PAISES_PRUEBA).index(
            st.session_state.get("filtro_pais", "Todos")
        ),
        key="filtro_pais",
    )

    # ── Filtro por tipo de actividad ──────────────────────────────────────────
    tipos_seleccionados = st.sidebar.multiselect(
        label="Tipo de actividad",
        options=TIPOS_ACTIVIDAD,
        default=st.session_state.get("filtro_tipos", TIPOS_ACTIVIDAD),
        key="filtro_tipos",
    )

    # ── Filtro por rango de fechas ────────────────────────────────────────────
    st.sidebar.markdown("**Rango de fechas**")

    col_a, col_b = st.sidebar.columns(2)
    with col_a:
        fecha_inicio = st.date_input(
            label="Desde",
            value=st.session_state.get("filtro_fecha_inicio", date(2024, 1, 1)),
            min_value=date(2020, 1, 1),
            max_value=date(2030, 12, 31),
            key="filtro_fecha_inicio",
        )
    with col_b:
        fecha_fin = st.date_input(
            label="Hasta",
            value=st.session_state.get("filtro_fecha_fin", date(2024, 12, 31)),
            min_value=date(2020, 1, 1),
            max_value=date(2030, 12, 31),
            key="filtro_fecha_fin",
        )

    # ── Botón "Ver todos" para resetear filtros ───────────────────────────────
    st.sidebar.markdown("---")
    if st.sidebar.button("Restablecer", use_container_width=True, key="btn_ver_todos"):
        st.session_state["filtro_pais"] = "Todos"
        st.session_state["filtro_tipos"] = TIPOS_ACTIVIDAD.copy()
        st.session_state["filtro_fecha_inicio"] = date(2024, 1, 1)
        st.session_state["filtro_fecha_fin"] = date(2024, 12, 31)
        st.rerun()

    # ── Aplicar filtros al DataFrame ──────────────────────────────────────────
    df_filtrado = df.copy()

    # Convertir columna fecha a tipo date para comparación
    df_filtrado["fecha"] = pd.to_datetime(df_filtrado["fecha"]).dt.date

    # Filtrar por país
    if pais_seleccionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado["pais"] == pais_seleccionado]

    # Filtrar por tipo de actividad
    if tipos_seleccionados:
        df_filtrado = df_filtrado[
            df_filtrado["tipo_actividad"].isin(tipos_seleccionados)
        ]
    else:
        # Si no hay ningún tipo seleccionado, no mostrar nada
        df_filtrado = df_filtrado.iloc[0:0]

    # Filtrar por rango de fechas
    df_filtrado = df_filtrado[
        (df_filtrado["fecha"] >= fecha_inicio) &
        (df_filtrado["fecha"] <= fecha_fin)
    ]

    # Mostrar contador de resultados en sidebar
    st.sidebar.caption(f"Mostrando {len(df_filtrado)} de {len(df)} visitas")

    return df_filtrado
