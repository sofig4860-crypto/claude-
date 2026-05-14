# Pipeline de Investigación Automatizada: YouTube → NotebookLM

Este repositorio contiene una pipeline que conecta Claude Code con NotebookLM para investigación automatizada.

## Dependencias

```bash
pip install yt-dlp notebooklm-py
```

## Autenticación (OBLIGATORIO antes de usar NotebookLM)

Abre una terminal separada y ejecuta:
```bash
notebooklm login
```
Sigue el flujo OAuth con tu cuenta de Google. Solo necesitas hacerlo una vez; las credenciales se guardan localmente.

---

## Habilidades disponibles

### `/yt-research` — Búsqueda en YouTube

Busca videos en YouTube y extrae metadatos (título, canal, vistas, duración, URL).

```bash
# Uso básico (25 videos)
python .claude/commands/yt-research.py "inteligencia artificial 2025"

# Cambiar número de resultados
python .claude/commands/yt-research.py "machine learning" --limit 10

# Salida en JSON para scripts
python .claude/commands/yt-research.py "deep learning" --json
```

**Campos que devuelve por video:** `title`, `url`, `views`, `author`, `duration`, `upload_date`, `video_id`

---

### `/notebooklm` — Automatización de NotebookLM

Crea cuadernos, agrega fuentes de YouTube y genera entregables.

```bash
# Listar cuadernos existentes
python .claude/commands/notebooklm_skill.py list

# Crear cuaderno
python .claude/commands/notebooklm_skill.py create --title "Investigación IA 2025"

# Agregar URL de YouTube como fuente
python .claude/commands/notebooklm_skill.py add-source <NOTEBOOK_ID> --url "https://youtube.com/watch?v=..."

# Pedir análisis
python .claude/commands/notebooklm_skill.py analyze <NOTEBOOK_ID> \
  --question "¿Cuáles son los hallazgos principales?"

# Generar entregables
python .claude/commands/notebooklm_skill.py generate <NOTEBOOK_ID> --type infographic --style sketch_note
python .claude/commands/notebooklm_skill.py generate <NOTEBOOK_ID> --type slide_deck
python .claude/commands/notebooklm_skill.py generate <NOTEBOOK_ID> --type flashcards
python .claude/commands/notebooklm_skill.py generate <NOTEBOOK_ID> --type study_guide
python .claude/commands/notebooklm_skill.py generate <NOTEBOOK_ID> --type quiz

# Pipeline completo (crear + fuentes + analizar + generar)
python .claude/commands/notebooklm_skill.py pipeline \
  --title "Investigación: IA 2025" \
  --urls "https://youtube.com/..." "https://youtube.com/..." \
  --question "¿Cuáles son las tendencias principales?" \
  --type infographic --style sketch_note
```

**Estilos de infografía disponibles:**
| Clave | Descripción |
|---|---|
| `sketch_note` | Manuscrito / pizarrón (recomendado) |
| `whiteboard` | Alias de sketch_note |
| `manuscript` | Alias de sketch_note |
| `professional` | Estilo profesional limpio |
| `bento_grid` | Cuadrícula tipo Bento |
| `editorial` | Estilo editorial |
| `scientific` | Estilo científico |
| `anime` / `kawaii` | Estilos ilustrados |

**Tipos de entregables:**
`infographic` · `slide_deck` · `study_guide` · `briefing_doc` · `quiz` · `flashcards` · `mind_map` · `audio` · `video`

---

## Pipeline completo: ejemplo de uso con Claude Code

Una vez configurado, puedes dar comandos como:

> "Usa la habilidad yt-research para encontrar los 25 videos más recientes y tendencia sobre **inteligencia artificial generativa**. Una vez que tengamos esos videos, envíalos a NotebookLM usando la habilidad notebooklm. Dame su análisis de los hallazgos principales, luego pide a NotebookLM que cree una infografía en estilo manuscrito / pizarrón que represente ese análisis."

**Nota:** Si das el comando de investigación sin especificar un tema, Claude te preguntará qué tema quieres investigar antes de continuar.

---

## Flujo interno de la pipeline

```
[Consulta] → yt-research → [Lista de URLs de YouTube]
                                      ↓
                          notebooklm create (nuevo cuaderno)
                                      ↓
                          notebooklm add-source (× N videos)
                                      ↓
                          notebooklm analyze (hallazgos principales)
                                      ↓
                          notebooklm generate --type infographic --style sketch_note
                                      ↓
                          [Infografía lista en NotebookLM]
```
