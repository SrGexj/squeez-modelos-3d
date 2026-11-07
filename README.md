# squeez-modelos-3d

Modelos 3D de músculos de squeez (glTF binario con compresión meshopt). Obra derivada de
[Z-Anatomy](https://github.com/Z-Anatomy/Models-of-human-anatomy) y BodyParts3D.
**Licencia: CC BY-SA 4.0** (ver `LICENSE` y `ATRIBUCION.md`; la atribución es obligatoria al usarlos).

## Contenido

| Fichero | Qué es | Tamaño |
|---|---|---|
| `modelos/masculino.meshopt.glb` | Músculos agrupados + huesos de contexto, 1,8 m, ~48.000 triángulos | 284.008 B |
| `modelos/femenino-a.meshopt.glb` | Misma malla reproporcionada a femenino, 1,65 m | 285.668 B |
| `datos/mapeo-musculos.json` | Pieza de Z-Anatomy -> grupo muscular y lado | |
| `scripts/` | Cómo se generaron (Blender + Python) | |

Cada grupo (pecho, espalda, hombros, biceps, triceps, antebrazos, core, lumbares, cuadriceps,
femorales, gluteos, pantorrillas, aductores, abductores) es una malla por lado (`_izq` / `_der`)
con su propio material.

## URLs previstas (CDN)

- https://cdn.gexj.es/modelos/v1/masculino.meshopt.glb
- https://cdn.gexj.es/modelos/v1/femenino-a.meshopt.glb

Aún NO publicadas. Al cargarlos desde la app hace falta el decodificador meshopt
(three.js `MeshoptDecoder`) y CORS abierto en el CDN para `https://squeez.es`,
`capacitor://localhost` y `https://localhost`.

## Cómo regenerar

Requisitos: Blender (probado con la serie 4.x) y `@gltf-transform/cli` 4.5.1.

1. Descargar `Z-Anatomy.zip` del repositorio de Z-Anatomy y extraer `Startup.blend`.
2. Masculino:
   ```
   blender --background --factory-startup --disable-autoexec Startup.blend \
     --python scripts/masculino/construir.py -- <dir_salida> [presupuesto_tris=48000]
   ```
   Genera el `.glb` y el mapeo (`datos/mapeo-musculos.json`). `scripts/masculino/inventario.py`
   lista las piezas y `render.py` hace capturas de comprobación.
3. Femenino A (parte del GLB masculino sin comprimir):
   ```
   blender --background --python scripts/femenino/variante_a.py -- <masculino.glb> <femenino-a.glb>
   ```
   `medir.py` y `render.py` miden proporciones y capturan.
4. Comprimir: `npx @gltf-transform/cli@4.5.1 meshopt <entrada>.glb <salida>.meshopt.glb`
   (los parámetros exactos usados originalmente no se conservaron; comprobar tamaño y que cargue).
