#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
doc_explorer_2.py — Explorador interactivo (ASCII + Q&A desde .ipynb)
---------------------------------------------------------------------
Requisitos: Python 3.8+ (sin librerías externas).
Uso: python doc_explorer_2.py

Funciones:
1) Ver diagrama de flujo (JPG)
2) Ver esquema ER en ASCII (opción principal, sin submenú)
3) Ver especificaciones técnicas del dataset
4) Ver características del dataset
5) Configuración
6) Navegar Preguntas/Respuestas desde un cuaderno .ipynb (Q&A Navigator)
   - Al entrar, lista las primeras 15 preguntas detectadas.
   - El usuario elige un índice y se muestra la solución.
"""

from __future__ import annotations
import json
import os
import re
import platform
import shutil
import subprocess
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

# ---------------------------
# Configuración del programa
# ---------------------------

@dataclass
class Config:
    ruta_diagrama: str = os.path.join("img", "diagrama_flujo.jpg")
    titulo: str = "Explorador de Documentación — Proyecto Ventas"
    limpiar_consola: bool = True
    ruta_notebook: str = "Aurelion_Ejercicios.ipynb"  # por defecto

CONFIG = Config()

# ---------------------------
# Datos del ER (para ASCII)
# ---------------------------

TABLES = {
    "CLIENTES": {
        "pk": ["ID_Cliente"],
        "fields": ["Nombre", "Ciudad", "Fecha_Registro"]
    },
    "PRODUCTOS": {
        "pk": ["ID_Producto"],
        "fields": ["Nombre_Producto", "Categoria"]
    },
    "VENTAS": {
        "pk": ["ID_Venta"],
        "fk": {"ID_Cliente": ("CLIENTES", "ID_Cliente")},
        "fields": ["Fecha_Venta", "Medio_Pago", "Monto_Total"]
    },
    "DETALLE_VENTAS": {
        "pk": [],  # clave compuesta implícita (ID_Venta + ID_Producto)
        "fk": {
            "ID_Venta": ("VENTAS", "ID_Venta"),
            "ID_Producto": ("PRODUCTOS", "ID_Producto"),
        },
        "fields": ["Cantidad", "Precio_Unitario", "Costo_Unitario", "Importe"]
    }
}

RELATIONSHIPS = [
    ("CLIENTES", "VENTAS", "1", "N", 'realiza', ("ID_Cliente", "ID_Cliente")),
    ("VENTAS", "DETALLE_VENTAS", "1", "N", 'contiene', ("ID_Venta", "ID_Venta")),
    ("PRODUCTOS", "DETALLE_VENTAS", "1", "N", 'incluye', ("ID_Producto", "ID_Producto")),
]

ESPEC_TECNICAS = [
    {"Tabla": "👥 Clientes", "Registros": "100","Relaciones": "PK: ID_Cliente","Campos Principales": "ID, Nombre, Ciudad, Fecha_Registro"},
    {"Tabla": "📦 Productos","Registros": "100","Relaciones": "PK: ID_Producto","Campos Principales": "ID, Nombre, Categoría"},
    {"Tabla": "🛒 Ventas","Registros": "120","Relaciones": "PK: ID_Venta → FK: ID_Cliente","Campos Principales": "ID_Venta, Fecha, Medio_Pago, Monto"},
    {"Tabla": "📋 Detalle_Ventas","Registros": "120","Relaciones": "FK: ID_Venta, ID_Producto","Campos Principales": "Cantidad, Precios, Costos, Importe"},
]

CARACTERISTICAS = [
    ("📊 Tipo", "Simulación de Base de Datos Relacional (OLTP → OLAP)"),
    ("📏 Escala", "Pequeña a mediana (miles de registros)"),
    ("💾 Formato", "Archivos Excel (.xlsx)"),
    ("🚀 Procesamiento", "Completamente en memoria con Pandas"),
]

# ---------------------------
# Utilitarios
# ---------------------------

def limpiar():
    if CONFIG.limpiar_consola:
        os.system("cls" if os.name == "nt" else "clear")

def pausa():
    input("\nPresiona Enter para continuar...")

def ancho_terminal(default: int = 100) -> int:
    try:
        cols = shutil.get_terminal_size().columns
        return max(cols, default)
    except Exception:
        return default

def hr(char: str = "─"):
    print(char * min(ancho_terminal(), 120))

def center(text: str):
    cols = min(ancho_terminal(), 120)
    print(text.center(cols))

def open_with_default_app(path: str) -> bool:
    try:
        if not os.path.exists(path):
            return False
        system = platform.system().lower()
        if system == "windows":
            os.startfile(path)  # type: ignore[attr-defined]
        elif system == "darwin":
            subprocess.check_call(["open", path])
        else:
            subprocess.check_call(["xdg-open", path])
        return True
    except Exception:
        return False

def print_table(rows: List[Dict[str, str]], headers: List[str]) -> None:
    cols = headers[:]
    col_widths = {h: len(h) for h in cols}
    for row in rows:
        for h in cols:
            col_widths[h] = max(col_widths[h], len(str(row.get(h, ""))))
    sep = " | "
    line = sep.join(h.ljust(col_widths[h]) for h in cols)
    divider = "-+-".join("-" * col_widths[h] for h in cols)
    print(line)
    print(divider)
    for row in rows:
        print(sep.join(str(row.get(h, "")).ljust(col_widths[h]) for h in cols))

def print_kv_list(pairs: List[Tuple[str, str]]):
    max_key = max(len(k) for k, _ in pairs)
    for k, v in pairs:
        print(f"{k.ljust(max_key)} : {v}")

# ---------------------------
# ER en ASCII (opción 2)
# ---------------------------

def _box(title: str, lines: List[str], width: Optional[int] = None) -> List[str]:
    content = [title] + ["─" * len(title)] + lines
    inner_width = max(len(s) for s in content) + 2
    if width is not None:
        inner_width = max(inner_width, width)
    top = "┌" + "─" * inner_width + "┐"
    bottom = "└" + "─" * inner_width + "┘"
    out = [top]
    for s in content:
        out.append("│ " + s.ljust(inner_width - 2) + " │")
    out.append(bottom)
    return out

def render_er_ascii() -> str:
    def table_lines(name: str) -> List[str]:
        t = TABLES[name]
        parts = []
        pk = t.get("pk", [])
        fk = t.get("fk", {})
        if pk:
            parts.append("PK: " + ", ".join(pk))
        if fk:
            parts.append("FK: " + ", ".join(f"{k}->{v[0]}.{v[1]}" for k, v in fk.items()))
        parts.append("— Campos —")
        parts.extend(t.get("fields", []))
        return parts

    boxes = []
    maxw = 0
    for name in TABLES.keys():
        b = _box(f" {name} ", table_lines(name))
        boxes.append(b)
        maxw = max(maxw, max(len(line) for line in b))

    # Normalizar ancho
    norm = []
    for b in boxes:
        title = b[1][2:-2].strip()
        body = [line[2:-2].strip() for line in b[2:-1]]
        norm.append(_box(f" {title} ", body, width=maxw-2))

    # Dos columnas
    lines = []
    for i in range(0, len(norm), 2):
        left = norm[i]
        right = norm[i+1] if i+1 < len(norm) else []
        max_lines = max(len(left), len(right))
        for j in range(max_lines):
            l = left[j] if j < len(left) else " " * maxw
            r = right[j] if right and j < len(right) else ""
            lines.append(l + "   " + r)
        lines.append("")

    # Relaciones
    lines.append("Relaciones:")
    for a, b, c1, cN, verb, (ka, kb) in RELATIONSHIPS:
        lines.append(f"  {a}.{ka}  ({c1}:{cN}, '{verb}')  {b}.{kb}")
    return "\n".join(lines)

# ---------------------------
# Diagrama JPG (opción 1)
# ---------------------------

def vista_diagrama():
    limpiar()
    center(CONFIG.titulo)
    hr()
    print("📌 Diagrama de flujo (JPG)\n")
    ruta = CONFIG.ruta_diagrama
    print(f"Ruta configurada: {ruta}")
    if os.path.exists(ruta):
        print("✔ Archivo encontrado.")
        print("\n¿Deseas abrirlo con el visor predeterminado del sistema?\n1) Sí\n2) No")
        choice = input("> ").strip()
        if choice == "1":
            ok = open_with_default_app(ruta)
            print("Intentando abrir el archivo..." if ok else "⚠ No se pudo abrir automáticamente.")
    else:
        print("⚠ No se encontró el archivo. Asegúrate de que exista en la carpeta 'img/'.")
    pausa()

# ---------------------------
# ER ASCII (opción 2, prevalente)
# ---------------------------

def vista_er_ascii():
    limpiar()
    center(CONFIG.titulo)
    hr()
    print("🧩 Esquema Relacional — Vista ASCII (principal)\n")
    print(render_er_ascii())
    pausa()

# ---------------------------
# Especificaciones (opción 3)
# ---------------------------

def vista_especificaciones():
    limpiar()
    center(CONFIG.titulo)
    hr()
    print("📚 Especificaciones Técnicas del Dataset\n")
    headers = ["Tabla", "Registros", "Relaciones", "Campos Principales"]
    print_table(ESPEC_TECNICAS, headers)
    pausa()

# ---------------------------
# Características (opción 4)
# ---------------------------

def vista_caracteristicas():
    limpiar()
    center(CONFIG.titulo)
    hr()
    print("🔧 Características del Dataset\n")
    print_kv_list(CARACTERISTICAS)
    pausa()

# ---------------------------
# Configuración (opción 5)
# ---------------------------

def vista_configuracion():
    limpiar()
    center(CONFIG.titulo)
    hr()
    print("⚙ Configuración actual\n")
    print(f"- Sistema operativo: {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"- Ruta del diagrama: {CONFIG.ruta_diagrama}")
    print(f"- Ruta del notebook (.ipynb): {CONFIG.ruta_notebook}")
    print(f"- Limpiar consola: {CONFIG.limpiar_consola}")
    print("\nOpciones:")
    print("1) Cambiar ruta del diagrama")
    print("2) Cambiar ruta del notebook")
    print("3) Alternar 'limpiar consola'")
    print("4) Volver")
    choice = input("> ").strip()
    if choice == "1":
        nueva = input("Nueva ruta (ej. img/diagrama_flujo.jpg): ").strip()
        if nueva:
            CONFIG.ruta_diagrama = nueva
            print("✔ Ruta de diagrama actualizada.")
        else:
            print("⚠ Ruta no modificada.")
        pausa()
    elif choice == "2":
        nueva = input("Nueva ruta del .ipynb: ").strip()
        if nueva:
            CONFIG.ruta_notebook = nueva
            print("✔ Ruta del notebook actualizada.")
        else:
            print("⚠ Ruta no modificada.")
        pausa()
    elif choice == "3":
        CONFIG.limpiar_consola = not CONFIG.limpiar_consola
        print(f"✔ limpiar_consola = {CONFIG.limpiar_consola}")
        pausa()

# ---------------------------
# Q&A Navigator (opción 6, simplificado)
# ---------------------------

Q_MARKERS = re.compile(r"^\s*(?:#{1,6}\s*)?(?:pregunta|question|q[:\-\s])\b", re.IGNORECASE)
A_MARKERS = re.compile(r"^\s*(?:#{1,6}\s*)?(?:respuesta|answer|a[:\-\s])\b", re.IGNORECASE)

def _cell_text(cell: dict) -> str:
    if cell.get("cell_type") == "markdown":
        return "".join(cell.get("source", []))
    if cell.get("cell_type") == "code":
        src = "".join(cell.get("source", []))
        return "```python\n" + src + "\n```"
    if cell.get("cell_type") == "raw":
        return "".join(cell.get("source", []))
    return ""

def parse_notebook_qa(nb_path: str) -> List[Dict[str, str]]:
    """
    Reglas mejoradas (robusto para cuadernos con encabezados):
    - Cualquier celda cuyo PRIMERA línea sea un ENCABEZADO Markdown (#, ##, ###) inicia una nueva Pregunta.
    - Marcadores explícitos (Pregunta:, Q:, etc.) también inician Pregunta.
    - La Respuesta incluye TODAS las celdas siguientes hasta antes del próximo encabezado/marcador de pregunta.
    - Se conservan bloques de código formateados.
    """
    if not os.path.exists(nb_path):
        return []
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    cells = nb.get("cells", [])
    qa: List[Dict[str, str]] = []

    def is_heading_first_line(line: str) -> bool:
        return bool(re.match(r"^\s*#{1,6}\s+.+", line))

    def is_q_marker(line: str) -> bool:
        return bool(Q_MARKERS.search(line))

    i = 0
    while i < len(cells):
        cell = cells[i]
        text = _cell_text(cell).strip()
        lines = text.splitlines()
        first = lines[0] if lines else ""

        if not text:
            i += 1
            continue

        # ¿Empieza pregunta?
        if is_heading_first_line(first) or is_q_marker(first):
            # Construir enunciado (pregunta): usar encabezado/primer línea sin hashes/marker
            if is_heading_first_line(first):
                question = re.sub(r"^\s*#{1,6}\s*", "", first).strip()
                rest = "\n".join(lines[1:]).strip()
                if rest:
                    question = (question + "\n" + rest).strip()
            else:
                # Q markers
                q_clean = re.sub(r"^\s*(?:#{1,6}\s*)?(?:pregunta|question|q[:\-\s])\s*", "", first, flags=re.IGNORECASE)
                rest = "\n".join(lines[1:]).strip()
                question = (q_clean + ("\n" + rest if rest else "")).strip()

            # Acumular respuesta hasta el próximo encabezado/marker
            answer_chunks: List[str] = []
            j = i + 1
            while j < len(cells):
                nxt = cells[j]
                t = _cell_text(nxt).strip()
                if t:
                    fl = t.splitlines()[0]
                    if is_heading_first_line(fl) or is_q_marker(fl):
                        break
                    # Si la celda inicia con marcador de Respuesta, limpiarlo
                    if A_MARKERS.search(fl):
                        a_clean = re.sub(r"^\s*(?:#{1,6}\s*)?(?:respuesta|answer|a[:\-\s])\s*", "", fl, flags=re.IGNORECASE)
                        rest = "\n".join(t.splitlines()[1:]).strip()
                        t = (a_clean + ("\n" + rest if rest else "")).strip()
                    answer_chunks.append(t)
                j += 1

            qa.append({"question": question, "answer": "\n\n".join(answer_chunks).strip()})
            i = j
            continue

        i += 1

    return qa


def vista_qa():
    nb_path = CONFIG.ruta_notebook
    limpiar()
    center(CONFIG.titulo)
    hr()
    print("🧭 Q&A Navigator — Notebook:", nb_path, "\n")

    if not os.path.exists(nb_path):
        print("⚠ No se encontró el archivo .ipynb. Actualiza la ruta en Configuración (opción 5).")
        pausa()
        return

    qa = parse_notebook_qa(nb_path)
    if not qa:
        print("⚠ No se detectaron preguntas/respuestas con las heurísticas actuales.")
        print("Tip: usa marcadores 'Pregunta:' / 'Respuesta:' o encabezados '##' para preguntas.")
        pausa()
        return

    # Mostrar listado (hasta 15)
    while True:
        limpiar()
        center("Q&A Navigator")
        hr()
        total = len(qa)
        to_show = qa[:15]
        print(f"Detectadas: {total} preguntas. Mostrando primeras {min(15, total)}.\n")
        for i, item in enumerate(to_show, 1):
            title = item["question"].splitlines()[0]
            print(f"[{i}] {title[:110]}{'…' if len(title) > 110 else ''}")
        print("\nElige un índice (1..{n}) o 0 para volver:".format(n=len(to_show)))
        choice = input("> ").strip()

        if choice == "0":
            break
        if not choice.isdigit():
            print("⚠ Índice inválido."); pausa(); continue
        idx = int(choice)
        if idx < 1 or idx > len(to_show):
            print("⚠ Fuera de rango."); pausa(); continue

        # Mostrar solución de la pregunta elegida
        item = to_show[idx - 1]
        limpiar()
        center(f"Q[{idx}]")
        hr()
        print("❓ Pregunta:\n" + item["question"] + "\n")
        print("✅ Respuesta:\n" + (item["answer"] or "(sin respuesta detectada)"))
        print("\nAcciones:")
        print("1) Volver al listado")
        print("0) Salir a menú principal")
        sub = input("> ").strip()
        if sub == "0":
            break
        # cualquier otra entrada regresa al listado

# ---------------------------
# Menú principal
# ---------------------------

def menu():
    while True:
        limpiar()
        center(CONFIG.titulo)
        hr()
        print("Selecciona una opción:\n")
        print("1) Ver diagrama de flujo (JPG)")
        print("2) Ver esquema relacional en ASCII (principal)")
        print("3) Ver especificaciones técnicas del dataset")
        print("4) Ver características del dataset")
        print("5) Configuración")
        print("6) Q&A desde notebook (.ipynb)")
        print("0) Salir")
        choice = input("\n> ").strip()

        if choice == "1":
            vista_diagrama()
        elif choice == "2":
            vista_er_ascii()
        elif choice == "3":
            vista_especificaciones()
        elif choice == "4":
            vista_caracteristicas()
        elif choice == "5":
            vista_configuracion()
        elif choice == "6":
            vista_qa()
        elif choice == "0":
            print("\n¡Hasta luego! 👋")
            break
        else:
            print("⚠ Opción inválida.")
            pausa()

if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        print("\nInterrupción del usuario. Saliendo...")
    except Exception as e:
        print(f"\nOcurrió un error inesperado: {e}")
