# Organizador de Archivos SUNAT con Sincronización en OneDrive

Esta herramienta permite organizar automáticamente archivos de SUNAT descargados y sincronizarlos con tu cuenta de OneDrive para tener un respaldo en la nube.

## Características

- **Organización automática**: Identifica y clasifica diferentes tipos de documentos de SUNAT (facturas, boletas, recibos, etc.)
- **Estructura de carpetas**: Organiza los documentos en una estructura de carpetas específica para cada tipo de documento
- **Sincronización con OneDrive**: Sube automáticamente los archivos organizados a tu cuenta de OneDrive
- **Soporte para archivos ZIP**: Extrae y organiza documentos SUNAT contenidos dentro de archivos ZIP

## Requisitos previos

1. Python 3.6 o superior
2. Bibliotecas necesarias (se instalan automáticamente)
3. Una cuenta de OneDrive
4. Token de acceso para OneDrive (ver instrucciones abajo)

## Instalación

Se recomienda usar un entorno virtual para contener las dependencias:

```bash
# Crear entorno virtual
python -m venv venv_sunat

# Activar el entorno virtual
# En Windows:
venv_sunat\Scripts\activate
# En Linux/Mac:
# source venv_sunat/bin/activate

# Instalar las dependencias
pip install -r requirements.txt
```

## Configuración

### 1. Obtener un token de acceso para OneDrive

Para acceder a tu cuenta de OneDrive, necesitas un token de acceso. Puedes obtenerlo siguiendo estos pasos:

1. Ve a [Portal de Azure](https://portal.azure.com) e inicia sesión
2. Ve a "Registros de aplicaciones" > "Nuevo registro"
3. Asigna un nombre a tu aplicación (ej. "SUNAT Organizer")
4. En "URI de redirección" elige "Web" y agrega: `http://localhost:8080/`
5. Haz clic en "Registrar"
6. Ve a "Permisos de API" > "Agregar un permiso" > "Microsoft Graph" > "Permisos delegados"
7. Busca y selecciona los siguientes permisos:
   - Files.ReadWrite
   - Files.ReadWrite.All
   - User.Read
8. Haz clic en "Agregar permisos" y luego en "Conceder consentimiento de administrador"
9. Ve a "Certificados y secretos" > "Nuevo secreto de cliente"
10. Asigna un nombre al secreto, selecciona un período de expiración y haz clic en "Agregar"
11. **¡IMPORTANTE!** Copia el "Valor" del secreto (solo se muestra una vez)

A continuación, necesitas obtener un token de acceso utilizando alguna de estas opciones:
- [Herramienta Graph Explorer](https://developer.microsoft.com/en-us/graph/graph-explorer)
- [Postman](https://www.postman.com/) siguiendo [estas instrucciones](https://learn.microsoft.com/en-us/graph/auth-v2-user)
- Utilizar un script personalizado con MSAL (Microsoft Authentication Library)

El token de acceso será solicitado la primera vez que ejecutes la aplicación.

### 2. Primera ejecución

La primera vez que ejecutes la herramienta, se te pedirá ingresar el token de acceso de OneDrive que obtuviste en el paso anterior.

## Uso

### Organización local y sincronización con OneDrive

```bash
python sunat_onedrive_sync.py --origen "C:\Descargas" --destino "C:\SUNAT_Organizados" --carpeta-onedrive "SUNAT_Documentos"
```

### Solo organización local (sin sincronización con OneDrive)

```bash
python sunat_onedrive_sync.py --origen "C:\Descargas" --destino "C:\SUNAT_Organizados" --solo-local
```

### Opciones disponibles

- `--origen`, `-o`: Directorio donde buscar archivos de SUNAT (requerido)
- `--destino`, `-d`: Directorio donde organizar los archivos localmente (requerido)
- `--extension`, `-e`: Extensión de archivos a buscar (predeterminado: '.pdf')
- `--carpeta-onedrive`, `-c`: Nombre de la carpeta en OneDrive donde sincronizar (predeterminado: 'SUNAT_Documentos')
- `--verbose`, `-v`: Mostrar información detallada durante la ejecución
- `--solo-local`, `-l`: No sincronizar con OneDrive, solo organizar localmente

## Estructura de carpetas creada

```
SUNAT_Documentos/
├── Reportes_Ficha_RUC/
├── Retenciones_y_Detracciones/
├── Constancias/
├── Valores/
├── Facturas/
├── Boletas/
├── Notas_Credito/
├── Recibos_Honorarios/
├── Declaraciones/
└── Otros_Documentos_SUNAT/
```

## Solución de problemas

### Problemas de autenticación con OneDrive

Si encuentras problemas con la autenticación, puedes eliminar el archivo de configuración y volver a intentarlo:

```
# En Windows:
del %USERPROFILE%\.config\onedrive_sunat\config.ini

# En Linux/Mac:
rm ~/.config/onedrive_sunat/config.ini
```

### Los tokens de acceso caducan

Los tokens de acceso de OneDrive suelen caducar después de cierto tiempo (generalmente 1 hora). Si esto ocurre, necesitarás obtener un nuevo token siguiendo los pasos anteriores.

### Logs

Los archivos de registro se almacenan en la carpeta `logs/` y pueden ser útiles para diagnosticar problemas.

## Licencia

Este proyecto está licenciado bajo los términos de la licencia MIT. 