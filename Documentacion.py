#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
doc_explorer_simple.py — Documentación interactiva (intro desde .md + ER ASCII + dataset)
-----------------------------------------------------------------------------------------
Requisitos: Python 3.8+ (sin librerías externas).
Uso: python doc_explorer_simple.py

Estructura:
- Al iniciar: muestra la INTRO del proyecto extraída desde un archivo Markdown
  (por defecto: "Documentacion_Completa - copia.md"). La intro incluye:
    * Tema principal, Problema identificado, Solución propuesta
    * Objetivos específicos
    * Listado de las 15 preguntas estratégicas
- Menú con 3 opciones:
    1) Ver esquema ER en ASCII
    2) Ver especificaciones técnicas del dataset
    3) Ver características del dataset
    0) Salir
"""

from __future__ import annotations
import os, re, sys, shutil
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

# ---------------------------
# Configuración
# ---------------------------

@dataclass
class Config:
    titulo: str = "📘 Documentación — Proyecto Aurelion"
    ruta_md: str = "Documentacion_Completa - copia.md"

CONFIG = Config()

# ---------------------------
# Datos del ER y Dataset
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

RELATIONSHIPS = [
    ("CLIENTES", "VENTAS", "1", "N", 'realiza', ("ID_Cliente", "ID_Cliente")),
    ("VENTAS", "DETALLE_VENTAS", "1", "N", 'contiene', ("ID_Venta", "ID_Venta")),
    ("PRODUCTOS", "DETALLE_VENTAS", "1", "N", 'incluye', ("ID_Producto", "ID_Producto")),
]

# ---------------------------
# Utilitarios
# ---------------------------

def limpiar():
    os.system("cls" if os.name == "nt" else "clear")

def hr(char: str = "─", width: int = 100):
    print(char * width)

def center(text: str, width: int = 100):
    print(text.center(width))

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

def pause():
    input("\nPresiona Enter para continuar...")

# ---------------------------
# ER ASCII
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
# Parser de Markdown para intro
# ---------------------------

def _read_md(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def _extract_section(md: str, start_pattern: str) -> str:
    m = re.search(start_pattern, md, flags=re.IGNORECASE | re.MULTILINE)
    if not m:
        return ""
    start = m.start()
    tail = md[start:]
    nxt = re.search(r"\n##\s", tail)
    return tail[:nxt.start()] if nxt else tail

def build_intro_from_md(md_path: str) -> str:
    md = _read_md(md_path)
    if not md:
        return "⚠ No se encontró el archivo Markdown con la documentación inicial."

    # Resumen
    resumen = _extract_section(md, r"^##\s*🎯\s*Resumen\s*$")
    # Análisis del problema (para objetivos específicos)
    analisis = _extract_section(md, r"^##\s*🔍\s*Análisis del Problema\s*$")
    # Preguntas estratégicas
    preguntas = _extract_section(md, r"^##\s*❓\s*Preguntas Estratégicas Completas\s*$")

    # Listado P1..P15
    q_lines = []
    for m in re.finditer(r"^####\s+.*?P(\d+):\s*(.+)$", preguntas, flags=re.MULTILINE):
        num, title = m.group(1), m.group(2)
        q_lines.append((int(num), title.strip()))
    q_lines.sort(key=lambda x: x[0])

    # Objetivos específicos
    obj_sect = ""
    if analisis:
        m_obj = re.search(r"^###\s*🎯\s*Objetivos Específicos\s*$", analisis, flags=re.MULTILINE)
        if m_obj:
            tail = analisis[m_obj.end():]
            stop = re.search(r"\n###\s", tail)
            obj_sect = tail[:stop.start()] if stop else tail

    # Problema y solución (desde Resumen)
    problema = ""
    solucion = ""
    tema = ""
    if resumen:
        tema_m = re.search(r"^###\s*Tema Principal\s*$([\s\S]*?)(?=\n###\s|$)", resumen, flags=re.MULTILINE)
        if tema_m:
            tema = tema_m.group(1).strip()
        prob_m = re.search(r"^###\s*Problema Identificado\s*$([\s\S]*?)(?=\n###\s|$)", resumen, flags=re.MULTILINE)
        if prob_m:
            problema = prob_m.group(1).strip()
        sol_m = re.search(r"^###\s*Solución Propuesta\s*$([\s\S]*?)(?=\n###\s|$)", resumen, flags=re.MULTILINE)
        if sol_m:
            solucion = sol_m.group(1).strip()

    parts = []
    parts.append("🧭 Introducción del Proyecto\n")
    if tema:
        parts.append("🔹 Tema Principal:\n" + tema.strip() + "\n")
    if problema:
        parts.append("🔹 Problema Identificado:\n" + problema.strip() + "\n")
    if solucion:
        parts.append("🔹 Solución Propuesta:\n" + solucion.strip() + "\n")
    if obj_sect:
        parts.append("🎯 Objetivos Específicos:\n" + obj_sect.strip() + "\n")
    if q_lines:
        parts.append("❓ Preguntas Estratégicas (P1–P15):")
        for n, t in q_lines[:15]:
            parts.append(f"  - P{n}: {t}")
    return "\n".join(parts).strip()

# ---------------------------
# Vistas
# ---------------------------

def vista_intro():
    limpiar()
    center(CONFIG.titulo)
    hr()
    print(build_intro_from_md(CONFIG.ruta_md))
    print("\n")
    hr()
    print("Menú: 1) ER ASCII  2) Especificaciones  3) Características  0) Salir")

def vista_er_ascii():
    limpiar()
    center(CONFIG.titulo + " — ER en ASCII")
    hr()
    print(render_er_ascii())
    print("\n")
    hr()
    print("Menú: 1) ER ASCII  2) Especificaciones  3) Características  0) Salir")

def vista_especificaciones():
    limpiar()
    center(CONFIG.titulo + " — Especificaciones")
    hr()
    headers = ["Tabla", "Registros", "Relaciones", "Campos Principales"]
    print_table(ESPEC_TECNICAS, headers)
    print("\n")
    hr()
    print("Menú: 1) ER ASCII  2) Especificaciones  3) Características  0) Salir")

def vista_caracteristicas():
    limpiar()
    center(CONFIG.titulo + " — Características del Dataset")
    hr()
    print_kv_list(CARACTERISTICAS)
    print("\n")
    hr()
    print("Menú: 1) ER ASCII  2) Especificaciones  3) Características  0) Salir")

# ---------------------------
# Bucle principal
# ---------------------------

def main():
    vista_intro()
    while True:
        choice = input("\nSelecciona una opción [1/2/3/0]: ").strip()
        if choice == "1":
            vista_er_ascii()
        elif choice == "2":
            vista_especificaciones()
        elif choice == "3":
            vista_caracteristicas()
        elif choice == "0":
            print("\n¡Hasta luego! 👋")
            break
        else:
            print("⚠ Opción inválida.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupción del usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"\nOcurrió un error inesperado: {e}")
        sys.exit(1)
