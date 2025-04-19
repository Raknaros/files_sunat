#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import configparser
import logging
from pathlib import Path
from datetime import datetime

# Usar la biblioteca actualizada en lugar de onedrivesdk
from msdrive import OneDrive
from sunat_organizer import SunatFileOrganizer

class OneDriveSync:
    """Clase para sincronizar archivos con OneDrive"""
    
    def __init__(self, logger=None):
        self.logger = logger or self._setup_logger()
        self.client = None
        self.config_file = self._get_config_path()
        
    def _setup_logger(self):
        """Configura el logger para la aplicación"""
        logger = logging.getLogger('onedrive_sync')
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Handler para archivo
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(f'logs/onedrive_sync_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def _get_config_path(self):
        """Obtiene la ruta del archivo de configuración"""
        home_dir = Path.home()
        config_dir = home_dir / '.config' / 'onedrive_sunat'
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / 'config.ini'
    
    def authenticate(self):
        """Autenticar con la API de OneDrive"""
        self.logger.info("Iniciando autenticación con OneDrive")
        
        # Cargar configuración
        config = configparser.ConfigParser()
        
        if self.config_file.exists():
            config.read(self.config_file)
        
        # Verificar si existe la sección 'onedrive'
        if not config.has_section('onedrive'):
            config.add_section('onedrive')
        
        # Si no hay access_token, solicitarlo
        if not config.has_option('onedrive', 'access_token'):
            print("Es necesario configurar un token de acceso de OneDrive.")
            print("Nota: Para obtener un token de acceso, debes registrar una aplicación en el Portal de Azure.")
            print("Sigue las instrucciones en https://learn.microsoft.com/en-us/graph/auth-register-app-v2")
            config['onedrive']['access_token'] = input("Ingresa el token de acceso de OneDrive: ")
            
            # Guardar configuración
            with open(self.config_file, 'w') as f:
                config.write(f)
        
        access_token = config['onedrive']['access_token']
        
        try:
            # Inicializar el cliente de OneDrive con el token
            self.client = OneDrive(access_token)
            self.logger.info("Autenticación exitosa con OneDrive")
            return True
        except Exception as e:
            self.logger.error(f"Error durante la autenticación: {str(e)}")
            return False
    
    def create_folder_if_not_exists(self, folder_name, parent_path='/'):
        """Crea una carpeta en OneDrive si no existe"""
        try:
            # Comprobar si la carpeta ya existe
            items = self.client.list_items(item_path=parent_path)
            for item in items:
                if item.get('name') == folder_name and item.get('folder') is not None:
                    self.logger.info(f"Carpeta '{folder_name}' ya existe en OneDrive")
                    return True
                    
            # Si no se encuentra, crear la carpeta
            full_path = os.path.join(parent_path, folder_name).replace('\\', '/')
            
            # Para carpetas nuevas, usamos un archivo temporal y luego lo eliminamos
            # (Esta es una solución alternativa ya que la biblioteca actual no tiene un método directo para crear carpetas)
            temp_file = 'temp.txt'
            with open(temp_file, 'w') as f:
                f.write('Temp file for folder creation')
                
            # Subir el archivo a la carpeta que queremos crear (la API creará la carpeta automáticamente)
            self.client.upload_item(item_path=f"{full_path}/temp.txt", file_path=temp_file)
            
            # Eliminar el archivo temporal local
            os.remove(temp_file)
            
            self.logger.info(f"Carpeta '{folder_name}' creada en OneDrive")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al crear carpeta '{folder_name}': {str(e)}")
            return False
            
    def upload_file(self, file_path, onedrive_path='/'):
        """Sube un archivo a OneDrive"""
        try:
            file_name = os.path.basename(file_path)
            target_path = os.path.join(onedrive_path, file_name).replace('\\', '/')
            
            # Subir archivo a OneDrive
            self.client.upload_item(item_path=target_path, file_path=file_path)
            self.logger.info(f"Archivo '{file_name}' subido exitosamente a OneDrive en '{onedrive_path}'")
            return True
        except Exception as e:
            self.logger.error(f"Error al subir archivo '{file_path}': {str(e)}")
            return False
            
    def sync_organized_files(self, directorio_local, carpeta_onedrive='SUNAT_Documentos'):
        """Sincroniza los archivos organizados con OneDrive"""
        if not self.client:
            self.logger.error("No hay un cliente de OneDrive autenticado")
            return False
            
        try:
            # Crear carpeta base en OneDrive
            if not self.create_folder_if_not_exists(carpeta_onedrive, '/'):
                self.logger.error("No se pudo crear la carpeta base en OneDrive")
                return False
                
            # Recorrer directorios locales
            directorio_local_path = Path(directorio_local)
            if not directorio_local_path.exists():
                self.logger.error(f"El directorio local '{directorio_local}' no existe")
                return False
                
            archivos_sincronizados = 0
            
            for carpeta in directorio_local_path.iterdir():
                if carpeta.is_dir():
                    # Crear carpeta correspondiente en OneDrive
                    carpeta_onedrive_path = f"/{carpeta_onedrive}"
                    if not self.create_folder_if_not_exists(carpeta.name, carpeta_onedrive_path):
                        self.logger.warning(f"No se pudo crear la carpeta '{carpeta.name}' en OneDrive, omitiendo...")
                        continue
                        
                    # Subir archivos de esta carpeta
                    for archivo in carpeta.iterdir():
                        if archivo.is_file():
                            target_path = f"/{carpeta_onedrive}/{carpeta.name}"
                            if self.upload_file(str(archivo), target_path):
                                archivos_sincronizados += 1
            
            self.logger.info(f"Sincronización completada. {archivos_sincronizados} archivos subidos a OneDrive")
            return True
            
        except Exception as e:
            self.logger.error(f"Error durante la sincronización: {str(e)}")
            return False
            
class SunatOneDriveOrganizer(SunatFileOrganizer):
    """Extiende el organizador de SUNAT para sincronizar con OneDrive"""
    
    def __init__(self, logger=None):
        super().__init__(logger)
        self.onedrive_sync = OneDriveSync(logger)
        
    def organizar_y_sincronizar(self, directorio_origen, directorio_destino, extension='.pdf', carpeta_onedrive='SUNAT_Documentos'):
        """Organiza los archivos SUNAT y los sincroniza con OneDrive"""
        # Organizar archivos localmente
        archivos = self.analizar_archivos(directorio_origen, extension)
        
        if not archivos:
            self.logger.info("No se encontraron archivos SUNAT para procesar")
            return 0, 0
            
        archivos_movidos = self.mover_archivos(archivos, directorio_destino)
        
        # Autenticar con OneDrive
        if not self.onedrive_sync.authenticate():
            self.logger.error("No se pudo autenticar con OneDrive, omitiendo sincronización")
            return archivos_movidos, 0
            
        # Sincronizar con OneDrive
        sincronizacion_exitosa = self.onedrive_sync.sync_organized_files(directorio_destino, carpeta_onedrive)
        
        if not sincronizacion_exitosa:
            self.logger.error("Ocurrió un error durante la sincronización con OneDrive")
            return archivos_movidos, 0
            
        return archivos_movidos, 1

def main():
    """Función principal para ejecutar desde línea de comandos"""
    parser = argparse.ArgumentParser(description='Organizador de archivos SUNAT con sincronización en OneDrive')
    parser.add_argument('--origen', '-o', required=True, help='Directorio donde buscar archivos SUNAT')
    parser.add_argument('--destino', '-d', required=True, help='Directorio donde organizar los archivos localmente')
    parser.add_argument('--extension', '-e', default='.pdf', help='Extensión de archivos a buscar (default: .pdf)')
    parser.add_argument('--carpeta-onedrive', '-c', default='SUNAT_Documentos', 
                      help='Nombre de la carpeta en OneDrive donde sincronizar los archivos (default: SUNAT_Documentos)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Mostrar información detallada')
    parser.add_argument('--solo-local', '-l', action='store_true', help='No sincronizar con OneDrive, solo organizar localmente')
    
    args = parser.parse_args()
    
    # Configurar nivel de log según verbose
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.getLogger('sunat_organizer').setLevel(log_level)
    logging.getLogger('onedrive_sync').setLevel(log_level)
    
    # Crear y ejecutar el organizador
    organizador = SunatOneDriveOrganizer()
    
    print(f"Buscando archivos SUNAT en {args.origen}...")
    
    if args.solo_local:
        # Solo organizar localmente
        archivos = organizador.analizar_archivos(args.origen, args.extension)
        
        if archivos:
            print(f"Se encontraron {len(archivos)} archivos SUNAT.")
            print(f"Organizando archivos en {args.destino}...")
            archivos_movidos = organizador.mover_archivos(archivos, args.destino)
            print(f"Proceso completado. Se organizaron {archivos_movidos} archivos localmente.")
        else:
            print("No se encontraron archivos SUNAT en el directorio especificado.")
    else:
        # Organizar y sincronizar
        print(f"Organizando archivos y sincronizando con OneDrive en carpeta {args.carpeta_onedrive}...")
        archivos_movidos, sync_status = organizador.organizar_y_sincronizar(
            args.origen, args.destino, args.extension, args.carpeta_onedrive
        )
        
        if archivos_movidos > 0:
            print(f"Se organizaron {archivos_movidos} archivos localmente.")
            
            if sync_status:
                print(f"Los archivos se sincronizaron correctamente con OneDrive en la carpeta '{args.carpeta_onedrive}'.")
            else:
                print("Hubo un problema al sincronizar con OneDrive. Revise los logs para más detalles.")
        else:
            print("No se encontraron archivos SUNAT en el directorio especificado.")

if __name__ == "__main__":
    import argparse
    main() 