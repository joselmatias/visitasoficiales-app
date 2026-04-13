"""
filtros.py — Panel de filtros en el sidebar
Proporciona controles de filtrado para país, tipo de actividad y rango de fechas
Retorna el DataFrame filtrado para pasarlo al mapa
"""

import pandas as pd
import streamlit as st
from datetime import date


def renderizar_filtros(df: pd.DataFrame) -> pd.DataFrame:
    """
    Renderiza los controles de filtro en el sidebar y aplica el filtrado
    al DataFrame recibido. Tipos y países se derivan dinámicamente del DataFrame.

    Parámetros:
        df (pd.DataFrame): DataFrame original con todas las visitas.

    Retorna:
        pd.DataFrame: DataFrame filtrado según los controles del usuario.
    """
    # Valores dinámicos derivados del CSV actual
    tipos_en_db  = sorted(df["tipo_actividad"].dropna().unique().tolist())
    paises_en_db = sorted(df["pais"].dropna().unique().tolist())

    # Inicializar session_state con los valores reales de la base de datos
    if "filtro_pais" not in st.session_state:
        st.session_state["filtro_pais"] = "Todos"
    if "filtro_tipos" not in st.session_state:
        st.session_state["filtro_tipos"] = tipos_en_db.copy()
    if "filtro_fecha_inicio" not in st.session_state:
        st.session_state["filtro_fecha_inicio"] = date(2024, 1, 1)
    if "filtro_fecha_fin" not in st.session_state:
        st.session_state["filtro_fecha_fin"] = date(2026, 12, 31)

    # Sanitizar tipos guardados: descartar los que ya no existan en la DB
    tipos_guardados = [t for t in st.session_state["filtro_tipos"] if t in tipos_en_db]
    if not tipos_guardados:
        tipos_guardados = tipos_en_db.copy()

    # ── Filtro por país ───────────────────────────────────────────────────────
    opciones_pais = ["Todos"] + paises_en_db
    pais_actual   = st.session_state.get("filtro_pais", "Todos")
    if pais_actual not in opciones_pais:
        pais_actual = "Todos"

    pais_seleccionado = st.sidebar.selectbox(
        label="País",
        options=opciones_pais,
        index=opciones_pais.index(pais_actual),
        key="filtro_pais",
    )

    # ── Filtro por tipo de actividad (solo tipos presentes en la DB) ──────────
    tipos_seleccionados = st.sidebar.multiselect(
        label="Tipo de actividad",
        options=tipos_en_db,
        default=tipos_guardados,
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
            value=st.session_state.get("filtro_fecha_fin", date(2026, 12, 31)),
            min_value=date(2020, 1, 1),
            max_value=date(2030, 12, 31),
            key="filtro_fecha_fin",
        )

    # ── Botón "Ver todos" para resetear filtros ───────────────────────────────
    st.sidebar.markdown("---")
    if st.sidebar.button("Restablecer", use_container_width=True, key="btn_ver_todos"):
        # Eliminar las claves para que los widgets vuelvan a su valor por defecto.
        # No se puede asignar session_state[key] directamente sobre claves de widget activas.
        for k in ["filtro_pais", "filtro_tipos", "filtro_fecha_inicio", "filtro_fecha_fin"]:
            if k in st.session_state:
                del st.session_state[k]
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
