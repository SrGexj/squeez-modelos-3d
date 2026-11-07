# Atribución y licencia

Modelos de grupos musculares de squeez (`modelos/masculino.meshopt.glb` y
`modelos/femenino-a.meshopt.glb`).

**Licencia de estos derivados: Creative Commons Atribución-CompartirIgual 4.0 Internacional
(CC BY-SA 4.0).** Texto completo en `LICENSE`; resumen y texto legal oficial en
https://creativecommons.org/licenses/by-sa/4.0/ y
https://creativecommons.org/licenses/by-sa/4.0/legalcode

## Origen

Derivados de **Z-Anatomy** (plantilla de Blender `Startup.blend` del repositorio
https://github.com/Z-Anatomy/Models-of-human-anatomy, fichero `Z-Anatomy.zip`), que a su vez
parte de **BodyParts3D**.

Atribuciones tal como las pide el Readme de Z-Anatomy:

- **"BodyParts3D - The Database Center for Life Science - CC-BY-SA 2.1 Japan"**
  Modelo original: https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html
  Licencia: https://creativecommons.org/licenses/by-sa/2.1/jp/
- **"Z-Anatomy - The libre 3D atlas of anatomy - CC-BY-SA 4.0"**
  https://www.z-anatomy.com/ · licencia: https://creativecommons.org/licenses/by-sa/4.0/

Autores: Kousaku OKUBO (BodyParts3D), Gauthier KERVYN (diseño, 3D, anatomía),
Marcin ZIELINSKI (add-on de Blender).

## Cambios realizados (nota de modificación)

### masculino.meshopt.glb
- Mallas convertidas a GLB, decimadas y agrupadas. Solo piezas de las colecciones
  «4: Muscular system» y «1: Skeletal system» (huesos de cráneo, mandíbula, esternón,
  clavícula, rótula, manos y pies, como contexto).
- Músculos fusionados por grupo de entrenamiento (pecho, espalda, hombros, biceps, triceps,
  antebrazos, core, lumbares, cuadriceps, femorales, gluteos, pantorrillas, aductores,
  abductores): una malla por grupo y lado (`_izq` / `_der`), un material por grupo. El
  mapeo pieza -> grupo está en `datos/mapeo-musculos.json`.
- Decimado (Decimate, collapse) hasta ~48.000 triángulos, reescalado a 1,8 m de alto,
  centrado en el origen, Y arriba. Cuantización y compresión meshopt (glTF-Transform 4.5.1).

### femenino-a.meshopt.glb
- Misma malla, nombres, extras y materiales que el masculino; los vértices se han deformado
  con un campo continuo (`scripts/femenino/variante_a.py`) a proporciones femeninas: hombros
  y cintura más estrechos, pelvis y caderas más anchas, tronco ~6 % más corto, muslos algo
  más llenos, brazos más finos, volumen moderado de pecho y glúteo, altura 1,65 m.
- Cuantización y compresión meshopt (glTF-Transform 4.5.1).

## Piezas excluidas por licencia

No se ha usado ninguna pieza de «Anatomy of the Inner Ear» (CC-BY-NC-SA 4.0), «Kidney»
(CC-BY-NC 4.0), «Brainder» ni «White matter» (Universidad de Washington, licencia no clara),
ni de «Cranial Nerves and Foramina». Los modelos no contienen oído interno, riñón, encéfalo
ni nervios.

## No hay garantías

Los modelos se ofrecen tal cual, sin garantía alguna (ver `LICENSE`). Son una ilustración
con fines de entrenamiento, no material médico.

## Cómo atribuir al usarlos (texto sugerido)

> Modelo anatómico basado en Z-Anatomy (CC BY-SA 4.0) y BodyParts3D, © The Database
> Center for Life Science (CC BY-SA 2.1 JP). Autores: Kousaku Okubo, Gauthier Kervyn,
> Marcin Zielinski. Mallas convertidas a GLB, decimadas, agrupadas (y, en la versión
> femenina, reproporcionadas) por squeez. Licencia del derivado: CC BY-SA 4.0.
> https://creativecommons.org/licenses/by-sa/4.0/
