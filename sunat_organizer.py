import os
import zipfile
import shutil
import argparse
import logging
from pathlib import Path
from datetime import datetime

class SunatFileOrganizer:
    """Clase para organizar archivos de SUNAT"""
    
    def __init__(self, logger=None):
        self.logger = logger or self._setup_logger()
        # Lista de inicios de nombres de archivo que identifican documentos SUNAT
        self.inicios_sunat = [
            'reporteec_ficharuc_',
            'ridetrac_',
            'rilf_',
            'rmgen_',
            'constancia_',
            'rvalores_',
            'bod_',
            'PDF-DOC',
            'FACTURA',
            'PDF-BOLETA',
            'PDF-NOTA_CREDITO',
            'RHE',
            'DetalleDeclaraciones'
        ]
        
        # Mapeo de tipos de documentos SUNAT a carpetas destino
        self.tipos_documentos = {
            'reporteec': 'Reportes_Ficha_RUC',
            'ridetrac': 'Retenciones_y_Detracciones',
            'constancia': 'Constancias',
            'rvalores': 'Valores',
            'FACTURA': 'Facturas',
            'PDF-BOLETA': 'Boletas',
            'PDF-NOTA': 'Notas_Credito',
            'RHE': 'Recibos_Honorarios',
            'Detalle': 'Declaraciones'
        }
        
    def _setup_logger(self):
        """Configura el logger para la aplicación"""
        logger = logging.getLogger('sunat_organizer')
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Handler para archivo
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(f'logs/sunat_organizer_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def analizar_archivos(self, directorio, extension='.pdf'):
        """Busca archivos con la extensión especificada y que sean de SUNAT"""
        self.logger.info(f"Analizando archivos en {directorio} con extensión {extension}")
        archivos_encontrados = []
        
        for root, dirs, files in os.walk(directorio):
            for file in files:
                # Verificar si es un archivo de SUNAT por su nombre
                es_archivo_sunat = any(inicio in file for inicio in self.inicios_sunat)
                
                if file.endswith(extension) and es_archivo_sunat:
                    ruta_completa = os.path.join(root, file)
                    self.logger.debug(f"Archivo SUNAT encontrado: {ruta_completa}")
                    archivos_encontrados.append(ruta_completa)
                
                # Si es un archivo ZIP, revisar su contenido
                elif file.endswith('.zip'):
                    try:
                        ruta_zip = os.path.join(root, file)
                        with zipfile.ZipFile(ruta_zip) as zip_file:
                            for zip_info in zip_file.infolist():
                                if zip_info.filename.endswith(extension):
                                    # Verificar si el archivo dentro del ZIP es de SUNAT
                                    es_zip_sunat = any(inicio in zip_info.filename for inicio in self.inicios_sunat)
                                    if es_zip_sunat:
                                        archivo_info = f"{ruta_zip}:{zip_info.filename}"
                                        self.logger.debug(f"Archivo SUNAT en ZIP encontrado: {archivo_info}")
                                        archivos_encontrados.append(archivo_info)
                    except Exception as e:
                        self.logger.error(f"Error al procesar archivo ZIP {ruta_zip}: {str(e)}")
        
        self.logger.info(f"Total de archivos SUNAT encontrados: {len(archivos_encontrados)}")
        return archivos_encontrados
    
    def determinar_tipo_documento(self, nombre_archivo):
        """Determina el tipo de documento SUNAT basado en su nombre"""
        nombre_base = os.path.basename(nombre_archivo)
        
        for clave, carpeta in self.tipos_documentos.items():
            if clave in nombre_base:
                return carpeta
                
        # Si no coincide con ninguno específico, usar "Otros_Documentos_SUNAT"
        return "Otros_Documentos_SUNAT"
    
    def mover_archivos(self, archivos_encontrados, directorio_destino):
        """Mueve los archivos encontrados a directorios según su tipo"""
        self.logger.info(f"Moviendo archivos al directorio base: {directorio_destino}")
        
        # Asegurar que existe el directorio base
        Path(directorio_destino).mkdir(parents=True, exist_ok=True)
        
        archivos_movidos = 0
        for archivo in archivos_encontrados:
            try:
                # Determinar el tipo de documento
                tipo_documento = self.determinar_tipo_documento(archivo)
                directorio_tipo = os.path.join(directorio_destino, tipo_documento)
                
                # Crear el directorio para este tipo si no existe
                Path(directorio_tipo).mkdir(parents=True, exist_ok=True)
                
                if ':' in archivo:
                    # Es un archivo dentro de un zip
                    zip_file_path, zip_file_name = archivo.split(':')
                    with zipfile.ZipFile(zip_file_path) as zip_file:
                        # Extraer el archivo al directorio correspondiente
                        nombre_base = os.path.basename(zip_file_name)
                        ruta_destino = os.path.join(directorio_tipo, nombre_base)
                        
                        # Extraer archivo del ZIP
                        with zip_file.open(zip_file_name) as source, open(ruta_destino, 'wb') as target:
                            shutil.copyfileobj(source, target)
                            
                        self.logger.info(f"Extraído archivo ZIP: {zip_file_name} a {ruta_destino}")
                        archivos_movidos += 1
                else:
                    # Es un archivo normal
                    nombre_base = os.path.basename(archivo)
                    ruta_destino = os.path.join(directorio_tipo, nombre_base)
                    
                    # Mover el archivo
                    shutil.copy2(archivo, ruta_destino)
                    self.logger.info(f"Copiado archivo: {archivo} a {ruta_destino}")
                    archivos_movidos += 1
                    
            except Exception as e:
                self.logger.error(f"Error al mover archivo {archivo}: {str(e)}")
        
        self.logger.info(f"Total de archivos movidos: {archivos_movidos}")
        return archivos_movidos

def main():
    """Función principal para ejecutar desde línea de comandos"""
    parser = argparse.ArgumentParser(description='Organizador de archivos SUNAT')
    parser.add_argument('--origen', '-o', required=True, help='Directorio donde buscar archivos SUNAT')
    parser.add_argument('--destino', '-d', required=True, help='Directorio donde organizar los archivos')
    parser.add_argument('--extension', '-e', default='.pdf', help='Extensión de archivos a buscar (default: .pdf)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Mostrar información detallada')
    
    args = parser.parse_args()
    
    # Configurar nivel de log según verbose
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.getLogger('sunat_organizer').setLevel(log_level)
    
    # Crear y ejecutar el organizador
    organizador = SunatFileOrganizer()
    
    print(f"Buscando archivos SUNAT en {args.origen}...")
    archivos = organizador.analizar_archivos(args.origen, args.extension)
    
    if archivos:
        print(f"Se encontraron {len(archivos)} archivos SUNAT.")
        print(f"Organizando archivos en {args.destino}...")
        archivos_movidos = organizador.mover_archivos(archivos, args.destino)
        print(f"Proceso completado. Se organizaron {archivos_movidos} archivos.")
    else:
        print("No se encontraron archivos SUNAT en el directorio especificado.")

if __name__ == "__main__":
    main() 