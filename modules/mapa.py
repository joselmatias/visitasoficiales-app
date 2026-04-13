"""
mapa.py — Globo 3D satelital con globe.gl (Three.js via CDN, gratuito)
Textura NASA Blue Marble + rotación horizontal automática
Etiquetas HTML nativas (htmlElementsData + decodeURIComponent) para tildes correctas
Clic en ciudad/marcador → navega con ?vid=X para abrir panel de detalle completo
"""

import json
from urllib.parse import quote
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# Paleta de colores por tipo de actividad
COLORES_ACTIVIDAD = {
    "Firma de Convenio":         "#00E5CC",
    "Conferencia Internacional":  "#C77DFF",
    "Visita Técnica":            "#FFD166",
    "Reunión Bilateral":         "#FFEF5E",
    "Foro / Cumbre":             "#FF6B9D",
    "Visita Oficial":            "#4FC3F7",
}


def _html_globo(puntos_json: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #0a0a14; overflow: hidden; font-family: sans-serif; }}
    #g   {{ width: 100vw; height: 520px; }}
    .etiqueta {{
      font-size: 13px;
      font-weight: 700;
      text-shadow: 0 0 6px #000, 0 0 12px #000;
      pointer-events: auto;
      cursor: pointer;
      white-space: nowrap;
      padding: 2px 4px;
    }}
    #tooltip {{
      display: none;
      position: fixed;
      background: rgba(10, 10, 30, 0.93);
      border: 1px solid #555;
      border-radius: 9px;
      padding: 10px 14px;
      color: #fff;
      font-size: 13px;
      line-height: 1.6;
      pointer-events: none;
      z-index: 9999;
      max-width: 230px;
      box-shadow: 0 4px 18px rgba(0,0,0,0.6);
    }}
    #tooltip .tip-ciudad {{ font-size: 15px; font-weight: 700; margin-bottom: 4px; }}
    #tooltip .tip-tipo   {{ font-size: 11px; opacity: 0.75; margin-bottom: 6px; }}
    #tooltip .tip-fecha  {{ font-size: 12px; }}
    #tooltip .tip-hint   {{ font-size: 11px; opacity: 0.5; margin-top: 6px; font-style: italic; }}
  </style>
</head>
<body>
  <div id="g"></div>
  <div id="tooltip">
    <div class="tip-ciudad" id="tip-ciudad"></div>
    <div class="tip-tipo"   id="tip-tipo"></div>
    <div class="tip-fecha"  id="tip-fecha"></div>
    <div class="tip-hint">Clic para ver detalle completo</div>
  </div>
  <script src="https://unpkg.com/globe.gl/dist/globe.gl.min.js"></script>
  <script>
    const pts = {puntos_json};
    const tip = document.getElementById('tooltip');

    function mostrarTooltip(d, x, y) {{
      document.getElementById('tip-ciudad').textContent = decodeURIComponent(d.ciudad) + ' — ' + d.pais;
      document.getElementById('tip-tipo').textContent   = d.tipo;
      document.getElementById('tip-fecha').textContent  = '📅 ' + d.fecha + ' · ' + d.dias + ' día' + (d.dias > 1 ? 's' : '');
      document.getElementById('tip-ciudad').style.color = d.color;
      tip.style.left    = (x + 14) + 'px';
      tip.style.top     = (y - 10) + 'px';
      tip.style.display = 'block';
    }}

    function ocultarTooltip() {{
      tip.style.display = 'none';
    }}

    function abrirDetalle(p) {{
      ocultarTooltip();
      const url = new URL(window.parent.location.href);
      url.searchParams.set('vid', p.id);
      window.parent.location.href = url.toString();
    }}

    const world = Globe({{ animateIn: false }})
      .globeImageUrl(
        'https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg')
      .bumpImageUrl(
        'https://unpkg.com/three-globe/example/img/earth-topology.png')
      .backgroundColor('#0a0a14')

      // Marcadores de punto
      .pointsData(pts)
      .pointLat('lat')
      .pointLng('lon')
      .pointColor('color')
      .pointRadius(0.45)
      .pointAltitude(0.05)
      .onPointClick(p => abrirDetalle(p))

      // Etiquetas HTML — soporte nativo de tildes/Unicode + tooltip al pasar el cursor
      .htmlElementsData(pts)
      .htmlLat('lat')
      .htmlLng('lon')
      .htmlAltitude(0.08)
      .htmlElement(d => {{
        const el = document.createElement('div');
        el.className = 'etiqueta';
        el.textContent = decodeURIComponent(d.ciudad);
        el.style.color = d.color;
        el.addEventListener('mouseenter', e => mostrarTooltip(d, e.clientX, e.clientY));
        el.addEventListener('mousemove',  e => {{
          tip.style.left = (e.clientX + 14) + 'px';
          tip.style.top  = (e.clientY - 10) + 'px';
        }});
        el.addEventListener('mouseleave', ocultarTooltip);
        el.addEventListener('click', () => abrirDetalle(d));
        return el;
      }})

      (document.getElementById('g'));

    // Rotación horizontal automática
    world.controls().autoRotate      = true;
    world.controls().autoRotateSpeed = 0.7;
    world.controls().enableZoom      = true;

    // Pausa al arrastrar, reanuda al soltar
    const ctrl = world.controls();
    document.getElementById('g').addEventListener('mousedown',
      () => ctrl.autoRotate = false);
    document.addEventListener('mouseup',
      () => ctrl.autoRotate = true);
  </script>
</body>
</html>"""


def renderizar_mapa(df: pd.DataFrame) -> pd.Series | None:
    """
    Renderiza el globo 3D satelital.
    Los clics en el globo navegan con ?vid=X (manejado en app.py).
    Los botones debajo también permiten seleccionar visita.

    Retorna:
        pd.Series | None: Fila seleccionada via botón, o None.
    """
    if df.empty:
        st.warning("No hay visitas para mostrar con los filtros seleccionados.")
        return None

    puntos = [
        {
            "id":    int(row["id"]),
            "lat":   float(row["latitud"]),
            "lon":   float(row["longitud"]),
            "color": COLORES_ACTIVIDAD.get(str(row["tipo_actividad"]), "#FFFFFF"),
            "pais":  str(row["pais"]),
            "ciudad": quote(str(row["ciudad"])),
            "tipo":  str(row["tipo_actividad"]),
            "fecha": str(row["fecha"])[:10],
            "dias":  int(row["duracion_dias"]),
        }
        for _, row in df.iterrows()
    ]

    components.html(
        _html_globo(json.dumps(puntos, ensure_ascii=False)),
        height=528,
        scrolling=False,
    )

    # Botones alternativos en filas de 4 (no requieren recarga de página)
    st.caption("👆 Haz clic en una ciudad del globo o pasa el cursor para ver el resumen · "
               "usa los botones para el detalle completo:")

    COLS_POR_FILA = 4
    filas = list(df.iterrows())
    for inicio in range(0, len(filas), COLS_POR_FILA):
        grupo = filas[inicio : inicio + COLS_POR_FILA]
        cols  = st.columns(COLS_POR_FILA)
        for col, (_, row) in zip(cols, grupo):
            color = COLORES_ACTIVIDAD.get(str(row["tipo_actividad"]), "#FFFFFF")
            with col:
                st.markdown(
                    f"<div style='text-align:center;margin-bottom:3px;"
                    f"font-size:11px;color:{color};'>■ {row['tipo_actividad']}</div>",
                    unsafe_allow_html=True,
                )
                if st.button(
                    f"{row['pais']} — {row['ciudad']}",
                    key=f"btn_v_{int(row['id'])}",
                    use_container_width=True,
                ):
                    return row

    return None
