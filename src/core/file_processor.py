import os
import io
import zipfile
from typing import List, Dict, Any
from datetime import datetime

def _parse_zip_path(full_path: str):
    """Splits a path into the physical file path and nested paths within ZIPs."""
    # Normalize path separators for consistency
    full_path = full_path.replace('\\', '/')
    parts = full_path.split(':')

    # Handle Windows drive letters (e.g., C:/...)
    if len(parts) > 1 and len(parts[0]) == 1 and parts[1].startswith('/'):
        drive = parts[0]
        rest = ':'.join(parts[1:]).lstrip('/')
        rest_parts = rest.split(':')
        base_path = f"{drive}:/{rest_parts[0]}"
        inner_paths = rest_parts[1:]
    else:
        base_path = parts[0]
        inner_paths = parts[1:]

    # Convert back to OS-specific separator for the base path
    base_path = base_path.replace('/', os.sep)
    return base_path, inner_paths

def _extract_from_zip(zip_path: any, inner_path_parts: List[str]):
    """Recursively extracts a file's binary data from a zip or nested zips."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # If this is the last part of the path, read the file
            if len(inner_path_parts) == 1:
                return zf.read(inner_path_parts[0])
            
            # Otherwise, go one level deeper
            nested_zip_data = zf.read(inner_path_parts[0])
            nested_zip_file = io.BytesIO(nested_zip_data)
            return _extract_from_zip(nested_zip_file, inner_path_parts[1:])
    except zipfile.BadZipFile:
        print(f"Error: Invalid ZIP format for {zip_path}")
        raise
    except KeyError:
        print(f"Error: Path not found inside ZIP: {inner_path_parts[0]}")
        raise

def create_zip_package(files_to_package: List[Dict[str, Any]], physical_files_to_delete: set, output_zip_path: str, log_filepath: str = None):
    """
    Creates a final ZIP package, logs the actions, and optionally deletes source files.

    Args:
        files_to_package: A list of file dictionaries to be added to the zip.
        physical_files_to_delete: A set of absolute paths to physical files to be deleted.
        output_zip_path: The full path for the output ZIP file.
        log_filepath: Optional path to a .txt file to log actions.
    """
    log_lines = []

    def log_action(message):
        if log_filepath:
            log_lines.append(message)

    output_dir = os.path.dirname(output_zip_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        log_action(f"Directorio creado: {output_dir}")

    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as final_zip:
        for file_info in files_to_package:
            full_path = file_info['path']
            filename = file_info['filename']
            
            log_action(f"Procesando {filename}...")

            try:
                base_path, inner_paths = _parse_zip_path(full_path)

                if not inner_paths:
                    if os.path.exists(base_path):
                        with open(base_path, 'rb') as f:
                            final_zip.writestr(filename, f.read())
                        log_action(f"  -> [AGREGADO] {filename} al paquete.")
                    else:
                        log_action(f"  -> [ADVERTENCIA] No se encontró el archivo en disco: {base_path}")
                else:
                    if os.path.exists(base_path):
                        file_data = _extract_from_zip(base_path, inner_paths)
                        final_zip.writestr(filename, file_data)
                        log_action(f"  -> [EXTRAÍDO Y AGREGADO] {filename} al paquete.")
                    else:
                        log_action(f"  -> [ADVERTENCIA] No se encontró el ZIP contenedor en disco: {base_path}")

            except Exception as e:
                log_action(f"  -> [ERROR] procesando {full_path}: {e}")

    log_action(f"\nPaquete ZIP creado con éxito en: {output_zip_path}")

    if physical_files_to_delete:
        log_action("\nEliminando archivos físicos originales...")
        for file_path in physical_files_to_delete:
            try:
                os.remove(file_path)
                log_action(f"  -> [ELIMINADO] {file_path}")
            except OSError as e:
                log_action(f"  -> [ERROR] al eliminar {file_path}: {e}")
    
    # Write the collected log lines to the file
    if log_filepath:
        try:
            with open(log_filepath, 'w', encoding='utf-8') as log_f:
                log_f.write("--- Log de Proceso ---\n")
                log_f.write(f"Paquete ZIP de salida: {output_zip_path}\n")
                log_f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                log_f.write("------------------------\n\n")
                log_f.write("\n".join(log_lines))
            print(f"\nLog del proceso guardado en: {log_filepath}")
        except IOError as e:
            print(f"\n[ERROR] No se pudo escribir el archivo de log: {e}")