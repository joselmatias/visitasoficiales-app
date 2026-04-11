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

# Extensiones de imagen soportadas (orden de preferencia)
EXTENSIONES_IMAGEN = [".jpg", ".jpeg", ".jfif", ".png", ".webp"]


def buscar_foto(ruta_base: str) -> str | None:
    """
    Busca el archivo de foto probando múltiples extensiones si la ruta exacta
    no existe. Esto resuelve diferencias entre .jpg, .jfif, .jpeg, etc.

    Parámetros:
        ruta_base (str): Ruta del CSV (puede tener cualquier extensión).

    Retorna:
        str | None: Ruta válida al archivo encontrado, o None si no existe.
    """
    # Intentar primero con la ruta exacta del CSV
    if os.path.exists(ruta_base):
        return ruta_base

    # Probar todas las extensiones sobre el nombre base sin extensión
    nombre_sin_ext = os.path.splitext(ruta_base)[0]
    for ext in EXTENSIONES_IMAGEN:
        ruta_candidata = nombre_sin_ext + ext
        if os.path.exists(ruta_candidata):
            return ruta_candidata

    return None


def _formatear_fecha(fecha_str: str) -> str:
    """
    Convierte una fecha en formato YYYY-MM-DD al formato 'DD de Mes de AAAA' en español.
    """
    try:
        if isinstance(fecha_str, str):
            fecha = datetime.strptime(fecha_str[:10], "%Y-%m-%d")
        else:
            fecha = pd.Timestamp(fecha_str).to_pydatetime()
        return f"{fecha.day} de {MESES_ES[fecha.month]} de {fecha.year}"
    except (ValueError, KeyError):
        return str(fecha_str)


def _badge_tipo(tipo: str) -> str:
    """
    Genera HTML de un badge con color para el tipo de actividad.
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


def mostrar_foto(fila: pd.Series, use_container_width: bool = True) -> None:
    """
    Renderiza únicamente la foto de la autoridad.
    Puede usarse tanto en el sidebar como en el área principal del mapa.

    Parámetros:
        fila (pd.Series): Fila del DataFrame con los datos de la visita.
        use_container_width (bool): Si la imagen ocupa el ancho del contenedor.
    """
    foto_ruta = str(fila.get("foto_path", ""))
    ruta_encontrada = buscar_foto(foto_ruta)

    if ruta_encontrada:
        st.image(
            ruta_encontrada,
            use_container_width=use_container_width,
            caption=f"Máxima Autoridad — {fila['pais']}",
        )
    else:
        st.warning("Foto no disponible para esta visita")


def mostrar_detalle(fila: pd.Series) -> None:
    """
    Renderiza en el sidebar el detalle completo de una visita:
    foto, encabezado, métricas, descripción y botón de cierre.

    Parámetros:
        fila (pd.Series): Fila del DataFrame con los datos de la visita.
    """

    # ── SECCIÓN 1: Foto de la autoridad ──────────────────────────────────────
    st.markdown("### Foto de la Autoridad")
    mostrar_foto(fila, use_container_width=True)
    st.markdown("---")

    # ── SECCIÓN 2: Encabezado de la visita ───────────────────────────────────
    st.markdown(f"### {fila['pais']} — {fila['ciudad']}")
    tipo = str(fila.get("tipo_actividad", ""))
    st.markdown(_badge_tipo(tipo), unsafe_allow_html=True)
    st.markdown("")

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
