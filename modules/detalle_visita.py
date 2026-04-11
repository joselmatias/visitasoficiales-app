"""
detalle_visita.py — Panel lateral con foto y detalle de la visita seleccionada
Renderiza en el sidebar de Streamlit la información completa de una visita
"""

import os
import pandas as pd
import streamlit as st
from datetime import datetime

# Mapeo de colores HTML para cada tipo de actividad (badge de color)
COLORES_BADGE = {
    "Firma de Convenio":        "#00C9A7",
    "Conferencia Internacional": "#845EC2",
    "Visita Técnica":           "#FFC75F",
    "Reunión Bilateral":        "#F9F871",
    "Foro / Cumbre":            "#FF6F91",
    "Visita Oficial":           "#4FC3F7",
}

# Nombres de meses en español para el formato de fecha
MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}


def _formatear_fecha(fecha_str: str) -> str:
    """
    Convierte una fecha en formato YYYY-MM-DD al formato 'DD de Mes de AAAA' en español.

    Parámetros:
        fecha_str (str): Fecha en formato ISO (YYYY-MM-DD).

    Retorna:
        str: Fecha formateada en español.
    """
    try:
        if isinstance(fecha_str, str):
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
        else:
            fecha = pd.Timestamp(fecha_str).to_pydatetime()
        mes_nombre = MESES_ES[fecha.month]
        return f"{fecha.day} de {mes_nombre} de {fecha.year}"
    except (ValueError, KeyError):
        return str(fecha_str)


def _badge_tipo(tipo: str) -> str:
    """
    Genera HTML de un badge con color para el tipo de actividad.

    Parámetros:
        tipo (str): Nombre del tipo de actividad.

    Retorna:
        str: Cadena HTML con el badge estilizado.
    """
    color = COLORES_BADGE.get(tipo, "#AAAAAA")
    return (
        f'<span style="'
        f'background-color:{color};'
        f'color:#000000;'
        f'padding:3px 10px;'
        f'border-radius:12px;'
        f'font-size:0.78em;'
        f'font-weight:600;'
        f'letter-spacing:0.5px;'
        f'">{tipo}</span>'
    )


def mostrar_detalle(fila: pd.Series) -> None:
    """
    Renderiza en el sidebar de Streamlit el detalle completo de una visita,
    incluyendo foto de la autoridad, encabezado, métricas y descripción.

    Parámetros:
        fila (pd.Series): Fila del DataFrame con los datos de la visita.
    """

    # ── SECCIÓN 1: Foto de la autoridad ──────────────────────────────────────
    st.markdown("### Foto de la Autoridad")

    foto_ruta = str(fila.get("foto_path", ""))

    try:
        if not foto_ruta:
            raise FileNotFoundError("Ruta vacía")

        if not os.path.exists(foto_ruta):
            raise FileNotFoundError(f"No se encontró: {foto_ruta}")

        st.image(
            foto_ruta,
            use_container_width=True,
            caption=f"Máxima Autoridad — {fila['pais']}",
        )

    except FileNotFoundError:
        st.warning("Foto no disponible para esta visita")

    st.markdown("---")

    # ── SECCIÓN 2: Encabezado de la visita ───────────────────────────────────
    st.markdown(f"### {fila['pais']} — {fila['ciudad']}")

    tipo = str(fila.get("tipo_actividad", ""))
    st.markdown(_badge_tipo(tipo), unsafe_allow_html=True)
    st.markdown("")  # Espaciado visual

    # ── SECCIÓN 3: Datos de la visita ─────────────────────────────────────────
    st.metric(
        label="Duración",
        value=f"{int(fila['duracion_dias'])} días",
    )

    fecha_formateada = _formatear_fecha(str(fila.get("fecha", "")))
    st.caption(f"Fecha: {fecha_formateada}")

    st.write(fila.get("descripcion", "Sin descripción disponible."))

    st.info(f"**Contraparte:** {fila.get('contraparte', 'No especificada')}")

    # ── SECCIÓN 4: Separador y botón de cierre ────────────────────────────────
    st.divider()

    if st.button("Cerrar detalle", key="btn_cerrar_detalle", use_container_width=True):
        st.session_state["visita_seleccionada"] = None
        st.rerun()
