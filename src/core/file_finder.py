import os
import re
import zipfile
import io
from typing import List, Dict, Any

# Patrones regex para los nombres estructurados de archivos SUNAT
PATRONES_ESTRUCTURADOS = {
    "guia_remision": (re.compile(r"^(\d{11})-09-([A-Z0-9]{4})-(\d{1,8})\.(pdf|xml)$", re.IGNORECASE), ["ruc", "serie", "correlativo", "ext"]),
    "reporte_planilla_zip": (re.compile(r"^(\d{11})_[A-Z]+_(\d{8})\.(zip)$", re.IGNORECASE), ["ruc", "periodo", "ext"]),
    "declaraciones_pagos": (re.compile(r"^DetalleDeclaraciones_(\d{11})_(\d{14})\.(xlsx)$", re.IGNORECASE), ["ruc", "timestamp", "ext"]),
    "ficha_ruc": (re.compile(r"^reporteec_ficharuc_(\d{11})_(\d{14})\.(pdf)$", re.IGNORECASE), ["ruc", "timestamp", "ext"]),
    "ingreso_recaudacion": (re.compile(r"^ridetrac_(\d{11})_(\d{13})_(\d{14})_(\d{9})\.(pdf)$", re.IGNORECASE), ["ruc", "num_operacion", "timestamp", "id", "ext"]),
    "liberacion_fondos": (re.compile(r"^rilf_(\d{11})_(\d{13})_(\d{14})_(\d{9})\.(pdf)$", re.IGNORECASE), ["ruc", "num_operacion", "timestamp", "id", "ext"]),
    "multa": (re.compile(r"^rmgen_(\d{11})_(\d{3})-(\d{3})-(\d{7})_(\d{14})_(\d{9})\.(pdf)$", re.IGNORECASE), ["ruc", "cod1", "cod2", "num_multa", "timestamp", "id", "ext"]),
    "notificacion": (re.compile(r"^constancia_(\d{14})_(\d{20})_(\d{13})_(\d{9})\.(pdf)$", re.IGNORECASE), ["timestamp", "id_notif", "num_operacion", "id", "ext"]),
    "valores": (re.compile(r"^rvalores_(\d{11})_([A-Z0-9]{12,17})_(\d{14})_(\d{9})\.(pdf)$", re.IGNORECASE), ["ruc", "num_valor", "timestamp", "id", "ext"]),
    "coactiva": (re.compile(r"^recgen_(\d{11})_(\d{13})_(\d{14})_(\d{9})\.(pdf)$", re.IGNORECASE), ["ruc", "num_expediente", "timestamp", "id", "ext"]),
    "baja_oficio": (re.compile(r"^bod_(\d{6})_(\d{11})_(\d{4})\.(pdf)$", re.IGNORECASE), ["id_baja", "ruc", "periodo", "ext"]),
    "factura": (re.compile(r"^(?:\d{11}-)?(01)-([A-Z0-9]{4})-(\d{1,8})\.(xml|zip|pdf)$", re.IGNORECASE), ["tipo_doc", "serie", "correlativo", "ext"]),
    "boleta": (re.compile(r"^(?:\d{11}-)?(03)-([A-Z0-9]{4})-(\d{1,8})\.(xml|zip|pdf)$", re.IGNORECASE), ["tipo_doc", "serie", "correlativo", "ext"]),
    "nota_credito": (re.compile(r"^(?:\d{11}-)?(07)-([A-Z0-9]{4})-(\d{1,8})\.(xml|zip|pdf)$", re.IGNORECASE), ["tipo_doc", "serie", "correlativo", "ext"]),
    "nota_debito": (re.compile(r"^(?:\d{11}-)?(08)-([A-Z0-9]{4})-(\d{1,8})\.(xml|zip|pdf)$", re.IGNORECASE), ["tipo_doc", "serie", "correlativo", "ext"]),
    "recibo_honorarios": (re.compile(r"^(?:\d{11}-)?(RHE)-([A-Z0-9]{4})-(\d{1,8})\.(xml|pdf)$", re.IGNORECASE), ["tipo_doc", "serie", "correlativo", "ext"]),
}

def _analyze_filename(filename: str, path: str) -> Dict[str, Any]:
    """Tries to match a filename against all known patterns."""
    for doc_type, (pattern, fields) in PATRONES_ESTRUCTURADOS.items():
        match = pattern.match(filename)
        if match:
            groups = match.groups()
            file_info = {
                "classification": doc_type,
                "filename": filename,
                "path": path,
            }
            # Dynamically assign captured groups to their field names
            for i, field in enumerate(fields):
                file_info[field] = groups[i]
            return file_info
    return None

def _analyze_zip_recursively(zip_file: zipfile.ZipFile, current_path: str, found_files: List[Dict[str, Any]], seen_filenames: set):
    """Recursively analyzes a zip file's contents."""
    for zip_info in zip_file.infolist():
        if zip_info.is_dir():
            continue

        filename = os.path.basename(zip_info.filename)
        nested_path = f"{current_path}:{zip_info.filename}"

        file_details = _analyze_filename(filename, nested_path)
        if file_details:
            if filename in seen_filenames:
                file_details['status'] = 'DUPLICADO'
            else:
                file_details['status'] = 'UNICO'
                seen_filenames.add(filename)
            found_files.append(file_details)

        # If a nested zip doesn't match a pattern, search inside it
        if filename.lower().endswith(".zip") and not file_details:
            try:
                with zip_file.open(zip_info) as nested_file:
                    nested_bytes = io.BytesIO(nested_file.read())
                    with zipfile.ZipFile(nested_bytes) as nested_zip:
                        _analyze_zip_recursively(nested_zip, nested_path, found_files, seen_filenames)
            except zipfile.BadZipFile:
                print(f"⚠️ Invalid nested zip file: {nested_path}")
                continue

def find_files(search_path: str) -> List[Dict[str, Any]]:
    """
    Recursively finds and classifies SUNAT files in a given path,
    including searching within ZIP files and marking duplicates.

    Args:
        search_path: The absolute path to the directory to search in.

    Returns:
        A list of dictionaries, where each dictionary represents a found
        and classified SUNAT file with its status (UNICO/DUPLICADO).
    """
    found_files = []
    seen_filenames = set()
    if not os.path.isdir(search_path):
        return []

    for root, _, files in os.walk(search_path):
        for file in files:
            full_path = os.path.join(root, file)
            
            # Analyze file on disk
            file_details = _analyze_filename(file, full_path)
            if file_details:
                if file in seen_filenames:
                    file_details['status'] = 'DUPLICADO'
                else:
                    file_details['status'] = 'UNICO'
                    seen_filenames.add(file)
                found_files.append(file_details)

            # If it's a ZIP, search inside it, unless the ZIP itself was already classified
            if file.lower().endswith(".zip") and not file_details:
                try:
                    with zipfile.ZipFile(full_path) as zip_file:
                        _analyze_zip_recursively(zip_file, full_path, found_files, seen_filenames)
                except zipfile.BadZipFile:
                    print(f"⚠️ Invalid zip file on disk: {full_path}")
                    continue
    
    return found_files