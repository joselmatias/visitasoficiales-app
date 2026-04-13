"""
mapa.py — Globo 3D satelital con globe.gl (Three.js via CDN, gratuito)
Textura NASA Blue Marble + rotación horizontal automática
Etiquetas HTML nativas (htmlElementsData + decodeURIComponent) para tildes correctas
Clic en ciudad/marcador → navega con ?vid=X para abrir panel de detalle completo
"""

import json
from datetime import timedelta
from urllib.parse import quote
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}


def _rango_fechas(fecha_inicio: pd.Timestamp, duracion: int) -> str:
    """Devuelve 'DD – DD de Mes de AAAA' o 'DD de Mes de AAAA' si es 1 día."""
    fi = fecha_inicio
    if duracion <= 1:
        return f"{fi.day} de {MESES_ES[fi.month]} de {fi.year}"
    ff = fi + timedelta(days=duracion - 1)
    if fi.month == ff.month:
        return f"{fi.day} – {ff.day} de {MESES_ES[fi.month]} de {fi.year}"
    return (f"{fi.day} de {MESES_ES[fi.month]} – "
            f"{ff.day} de {MESES_ES[ff.month]} de {ff.year}")

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

    # ── Acordeones por año ────────────────────────────────────────────────────
    st.caption("👆 Haz clic en una ciudad del globo para ver el detalle · "
               "o despliega el año para consultar todos los eventos:")

    df_tmp = df.copy()
    df_tmp["_fecha_ts"] = pd.to_datetime(df_tmp["fecha"])
    df_tmp["_year"]     = df_tmp["_fecha_ts"].dt.year
    años = sorted(df_tmp["_year"].unique())

    for año in años:
        eventos = df_tmp[df_tmp["_year"] == año].sort_values("_fecha_ts")
        n = len(eventos)
        label = f"**{año}**  —  {n} evento{'s' if n > 1 else ''}"
        with st.expander(label, expanded=False):
            for _, row in eventos.iterrows():
                color  = COLORES_ACTIVIDAD.get(str(row["tipo_actividad"]), "#FFFFFF")
                rango  = _rango_fechas(row["_fecha_ts"], int(row["duracion_dias"]))
                dias   = int(row["duracion_dias"])
                badge  = (
                    f'<span style="background:{color};color:#000;'
                    f'padding:2px 9px;border-radius:10px;'
                    f'font-size:0.75em;font-weight:700;">'
                    f'{row["tipo_actividad"]}</span>'
                )

                st.markdown(
                    f"""
<div style="border:1px solid #333;border-radius:10px;
            padding:14px 18px;margin-bottom:12px;background:#0d0d1f;">
  <div style="font-size:1.05em;font-weight:700;margin-bottom:6px;">
    {row['descripcion']}
  </div>
  <div style="margin-bottom:8px;">{badge}</div>
  <table style="width:100%;border-collapse:collapse;font-size:0.9em;color:#ccc;">
    <tr>
      <td style="padding:3px 8px 3px 0;width:50%;">
        📍 <b>{row['ciudad']}</b>, {row['pais']}
      </td>
      <td style="padding:3px 0;">
        📅 {rango}
      </td>
    </tr>
    <tr>
      <td style="padding:3px 8px 3px 0;">
        ⏱ {dias} día{'s' if dias > 1 else ''}
      </td>
      <td style="padding:3px 0;">
        🤝 {row.get('contraparte', '—')}
      </td>
    </tr>
  </table>
</div>
""",
                    unsafe_allow_html=True,
                )

    return None
