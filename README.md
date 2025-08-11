# SUNAT File Finder & Processor

Una herramienta avanzada para localizar, clasificar, y empaquetar archivos de comprobantes electrónicos de SUNAT. Busca de forma recursiva en directorios, inspecciona archivos ZIP anidados y puede consolidar todos los archivos encontrados en un único paquete.

## Características Principales

- **Clasificación Avanzada**: Identifica una gran variedad de documentos de SUNAT (`facturas`, `boletas`, `recibos`, `fichas RUC`, `multas`, etc.) usando patrones de nombres de archivo específicos.
- **Análisis de ZIPs Anidados**: Busca archivos de SUNAT no solo en el directorio principal, sino también dentro de archivos `.zip`, incluyendo ZIPs que están dentro de otros ZIPs.
- **Doble Interfaz (CLI y API)**: Ofrece tanto una interfaz de línea de comandos (CLI) para uso directo como una API web para integraciones.
- **Dos Modos de Operación**:
  1.  **Find (Encontrar)**: Solo busca y lista los archivos, mostrando su clasificación y ubicación (incluso dentro de un ZIP).
  2.  **Process (Procesar)**: Busca los archivos, los extrae (si están en un ZIP) y los consolida en un único archivo `.zip` de salida, con la opción de eliminar los originales.

## Instalación

1.  **Entorno virtual (Recomendado):**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Linux/macOS
    # source venv/bin/activate
    ```

2.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

## Uso

### Modo 1: Interfaz de Línea de Comandos (CLI)

La CLI tiene dos comandos principales: `find` y `process`.

#### Comando `find`

Busca y lista todos los archivos SUNAT que encuentra.

**Sintaxis:**
`python main.py cli find <ruta_de_busqueda> [-o <archivo_salida.json>]`

**Ejemplo:**
```bash
python main.py cli find "D:\\Comprobantes"
```

#### Comando `process`

Busca los archivos, los extrae y los empaqueta en un nuevo ZIP.

**Sintaxis:**
`python main.py cli process <ruta_de_busqueda> <ruta_zip_salida> [--delete-originals]`

**Ejemplo:**
```bash
# Simplemente empaqueta los archivos
python main.py cli process "D:\\Comprobantes" "D:\\Consolidados\\SUNAT_2024.zip"

# Empaqueta y elimina los archivos originales
python main.py cli process "D:\\Comprobantes" "D:\\Consolidados\\SUNAT_2024.zip" --delete-originals
```

---

### Modo 2: API Web

Inicia un servidor web para acceder a la funcionalidad a través de endpoints HTTP.

**Iniciar el servidor:**
```bash
python main.py api --host 127.0.0.1 --port 8000
```
Accede a la documentación interactiva en `http://127.0.0.1:8000/docs`.

#### Endpoint `/find`

Busca y devuelve una lista de archivos en formato JSON.
- **URL:** `/find`
- **Método:** `POST`
- **Cuerpo (Body):** `{"path": "D:\\Comprobantes"}`

#### Endpoint `/process`

Busca, empaqueta y opcionalmente elimina los archivos originales.
- **URL:** `/process`
- **Método:** `POST`
- **Cuerpo (Body):** 
  ```json
  {
    "search_path": "D:\\Comprobantes",
    "output_zip_path": "D:\\Consolidados\\SUNAT_2024.zip",
    "delete_originals": false
  }
  ```
