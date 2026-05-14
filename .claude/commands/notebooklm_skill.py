#!/usr/bin/env python3
"""
NotebookLM Integration Skill — notebooklm
==========================================
Automatiza Google NotebookLM usando la API Python no oficial notebooklm-py
(by Teng Lin). Permite crear cuadernos, subir fuentes de YouTube y
generar entregables como infografías, presentaciones y tarjetas de estudio.

PREREQUISITO: Autenticarse primero ejecutando en una terminal separada:
    notebooklm login

Uso desde Claude Code:
    /notebooklm create --title "Mi cuaderno"
    /notebooklm add-source <notebook_id> --url <youtube_url>
    /notebooklm analyze <notebook_id> --question "¿Cuáles son los hallazgos principales?"
    /notebooklm generate <notebook_id> --type infographic --style sketch_note
    /notebooklm list

Uso directo:
    python notebooklm.py create --title "Investigación IA 2025"
    python notebooklm.py add-source <id> --url "https://youtube.com/..."
    python notebooklm.py generate <id> --type infographic --style sketch_note
"""

import argparse
import asyncio
import json
import sys
from typing import Optional

import notebooklm
from notebooklm import NotebookLMClient
from notebooklm.exceptions import AuthError, NotebookLMError
from notebooklm.rpc.types import (
    InfographicDetail,
    InfographicOrientation,
    InfographicStyle,
    ReportFormat,
    VideoStyle,
)

# Mapeos de nombre legible → enum
INFOGRAPHIC_STYLES = {
    "auto": InfographicStyle.AUTO_SELECT,
    "sketch_note": InfographicStyle.SKETCH_NOTE,       # manuscrito / pizarrón
    "whiteboard": InfographicStyle.SKETCH_NOTE,        # alias para "whiteboard"
    "manuscript": InfographicStyle.SKETCH_NOTE,        # alias
    "professional": InfographicStyle.PROFESSIONAL,
    "bento_grid": InfographicStyle.BENTO_GRID,
    "editorial": InfographicStyle.EDITORIAL,
    "instructional": InfographicStyle.INSTRUCTIONAL,
    "bricks": InfographicStyle.BRICKS,
    "clay": InfographicStyle.CLAY,
    "anime": InfographicStyle.ANIME,
    "kawaii": InfographicStyle.KAWAII,
    "scientific": InfographicStyle.SCIENTIFIC,
}

INFOGRAPHIC_ORIENTATIONS = {
    "landscape": InfographicOrientation.LANDSCAPE,
    "portrait": InfographicOrientation.PORTRAIT,
    "square": InfographicOrientation.SQUARE,
}

INFOGRAPHIC_DETAILS = {
    "concise": InfographicDetail.CONCISE,
    "standard": InfographicDetail.STANDARD,
    "detailed": InfographicDetail.DETAILED,
}

VIDEO_STYLES = {
    "auto": VideoStyle.AUTO_SELECT,
    "whiteboard": VideoStyle.WHITEBOARD,
    "classic": VideoStyle.CLASSIC,
    "kawaii": VideoStyle.KAWAII,
    "anime": VideoStyle.ANIME,
    "watercolor": VideoStyle.WATERCOLOR,
    "retro_print": VideoStyle.RETRO_PRINT,
    "heritage": VideoStyle.HERITAGE,
    "paper_craft": VideoStyle.PAPER_CRAFT,
}


# ─────────────────────────────────────────────
#  Operaciones principales
# ─────────────────────────────────────────────

async def cmd_list(client: NotebookLMClient) -> None:
    """Lista todos los cuadernos disponibles."""
    notebooks = await client.notebooks.list()
    if not notebooks:
        print("No hay cuadernos. Crea uno con: notebooklm create --title 'Mi cuaderno'")
        return

    print(f"## Cuadernos en NotebookLM ({len(notebooks)})\n")
    for nb in notebooks:
        print(f"- **{nb.title}**  `{nb.id}`")


async def cmd_create(client: NotebookLMClient, title: str) -> None:
    """Crea un nuevo cuaderno."""
    nb = await client.notebooks.create(title)
    result = {"id": nb.id, "title": nb.title}
    print(f"Cuaderno creado exitosamente:")
    print(f"  Título : {nb.title}")
    print(f"  ID     : {nb.id}")
    print(json.dumps(result))


async def cmd_add_source(
    client: NotebookLMClient,
    notebook_id: str,
    url: str,
    wait: bool = True,
) -> None:
    """Agrega una URL (YouTube u otra) como fuente al cuaderno."""
    print(f"Agregando fuente: {url}")
    print("Esperando que NotebookLM procese la fuente..." if wait else "")
    source = await client.sources.add_url(notebook_id, url, wait=wait)
    print(f"Fuente agregada: '{source.title}'  ID: {source.id}")


async def cmd_add_multiple_sources(
    client: NotebookLMClient,
    notebook_id: str,
    urls: list[str],
) -> list[str]:
    """Agrega múltiples URLs como fuentes. Devuelve lista de IDs de fuentes."""
    source_ids = []
    total = len(urls)
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{total}] Agregando: {url}", file=sys.stderr)
        try:
            source = await client.sources.add_url(notebook_id, url, wait=True)
            source_ids.append(source.id)
            print(f"  OK: {source.title}", file=sys.stderr)
        except NotebookLMError as e:
            print(f"  FALLO: {e}", file=sys.stderr)
    return source_ids


async def cmd_analyze(
    client: NotebookLMClient,
    notebook_id: str,
    question: str,
) -> None:
    """Hace una pregunta al cuaderno y muestra la respuesta."""
    print(f"Consultando NotebookLM: {question}\n")
    result = await client.chat.ask(notebook_id, question)
    print("## Análisis de NotebookLM\n")
    print(result.answer)


async def cmd_generate(
    client: NotebookLMClient,
    notebook_id: str,
    artifact_type: str,
    style: Optional[str] = None,
    orientation: Optional[str] = None,
    detail: Optional[str] = None,
    instructions: Optional[str] = None,
    output_file: Optional[str] = None,
    language: str = "es",
) -> None:
    """
    Genera un entregable (infografía, presentación, guía de estudio, etc.).

    artifact_type opciones:
        infographic   → infografía (soporta --style, --orientation, --detail)
        slide_deck    → presentación / diapositivas
        study_guide   → guía de estudio
        briefing_doc  → documento de resumen
        quiz          → cuestionario
        flashcards    → tarjetas de estudio
        mind_map      → mapa mental
        audio         → podcast de audio
        video         → video resumen
    """
    print(f"Generando '{artifact_type}' en NotebookLM...")
    artifacts_api = client.artifacts
    status = None

    if artifact_type == "infographic":
        inf_style = INFOGRAPHIC_STYLES.get(style or "sketch_note", InfographicStyle.SKETCH_NOTE)
        inf_orient = INFOGRAPHIC_ORIENTATIONS.get(orientation or "landscape", InfographicOrientation.LANDSCAPE)
        inf_detail = INFOGRAPHIC_DETAILS.get(detail or "standard", InfographicDetail.STANDARD)
        status = await artifacts_api.generate_infographic(
            notebook_id,
            language=language,
            instructions=instructions,
            orientation=inf_orient,
            detail_level=inf_detail,
            style=inf_style,
        )

    elif artifact_type == "slide_deck":
        status = await artifacts_api.generate_slide_deck(
            notebook_id,
            language=language,
            instructions=instructions,
        )

    elif artifact_type == "study_guide":
        status = await artifacts_api.generate_study_guide(
            notebook_id,
            language=language,
            extra_instructions=instructions,
        )

    elif artifact_type == "briefing_doc":
        status = await artifacts_api.generate_report(
            notebook_id,
            report_format=ReportFormat.BRIEFING_DOC,
            language=language,
            extra_instructions=instructions,
        )

    elif artifact_type == "quiz":
        status = await artifacts_api.generate_quiz(
            notebook_id,
            instructions=instructions,
        )

    elif artifact_type == "flashcards":
        status = await artifacts_api.generate_flashcards(
            notebook_id,
            instructions=instructions,
        )

    elif artifact_type == "mind_map":
        result = await artifacts_api.generate_mind_map(
            notebook_id,
            language=language,
            instructions=instructions,
        )
        print("Mapa mental generado y guardado en el cuaderno.")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    elif artifact_type == "audio":
        vid_style = VIDEO_STYLES.get(style or "auto", VideoStyle.AUTO_SELECT)
        status = await artifacts_api.generate_audio(
            notebook_id,
            language=language,
            instructions=instructions,
        )

    elif artifact_type == "video":
        vid_style = VIDEO_STYLES.get(style or "whiteboard", VideoStyle.WHITEBOARD)
        status = await artifacts_api.generate_video(
            notebook_id,
            language=language,
            instructions=instructions,
            video_style=vid_style,
        )

    else:
        print(f"Tipo desconocido: {artifact_type}", file=sys.stderr)
        print("Opciones: infographic, slide_deck, study_guide, briefing_doc, quiz, flashcards, mind_map, audio, video")
        sys.exit(1)

    if status:
        print(f"Generación iniciada. Task ID: {status.task_id}")
        print("Esperando completar...")
        await artifacts_api.wait_for_completion(notebook_id, status.task_id)
        print(f"Entregable '{artifact_type}' generado exitosamente.")

        # Intentar descarga si se especificó archivo de salida
        if output_file:
            try:
                if artifact_type == "audio":
                    await artifacts_api.download_audio(notebook_id, output_file)
                    print(f"Audio guardado en: {output_file}")
                elif artifact_type == "infographic":
                    await artifacts_api.download_infographic(notebook_id, output_file)
                    print(f"Infografía guardada en: {output_file}")
                elif artifact_type == "slide_deck":
                    await artifacts_api.download_slide_deck(notebook_id, output_file)
                    print(f"Presentación guardada en: {output_file}")
                elif artifact_type in ("quiz", "flashcards"):
                    await artifacts_api.download_quiz(notebook_id, output_file) if artifact_type == "quiz" \
                        else await artifacts_api.download_flashcards(notebook_id, output_file)
                    print(f"Archivo guardado en: {output_file}")
            except Exception as e:
                print(f"Generado, pero no se pudo descargar: {e}")


async def cmd_pipeline(
    client: NotebookLMClient,
    title: str,
    urls: list[str],
    question: str,
    artifact_type: str = "infographic",
    style: str = "sketch_note",
    orientation: str = "landscape",
    instructions: Optional[str] = None,
    language: str = "es",
) -> None:
    """
    Pipeline completo: crea cuaderno → agrega fuentes → analiza → genera entregable.
    """
    print(f"\n{'='*60}")
    print(f"PIPELINE NotebookLM: {title}")
    print(f"{'='*60}\n")

    # 1. Crear cuaderno
    print("PASO 1: Creando cuaderno...")
    nb = await client.notebooks.create(title)
    print(f"  Cuaderno: '{nb.title}'  ID: {nb.id}\n")

    # 2. Agregar fuentes
    print(f"PASO 2: Agregando {len(urls)} fuentes...")
    await cmd_add_multiple_sources(client, nb.id, urls)
    print()

    # 3. Analizar
    print("PASO 3: Analizando hallazgos principales...")
    result = await client.chat.ask(nb.id, question)
    print("\n## Análisis de NotebookLM\n")
    print(result.answer)
    print()

    # 4. Generar entregable
    print(f"PASO 4: Generando entregable '{artifact_type}' (estilo: {style})...")
    await cmd_generate(
        client,
        nb.id,
        artifact_type=artifact_type,
        style=style,
        orientation=orientation,
        instructions=instructions,
        language=language,
    )

    print(f"\n{'='*60}")
    print(f"Pipeline completado. Cuaderno ID: {nb.id}")
    print(f"{'='*60}")


# ─────────────────────────────────────────────
#  CLI
# ─────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Automatización de Google NotebookLM via Python."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # list
    sub.add_parser("list", help="Lista todos los cuadernos")

    # create
    p_create = sub.add_parser("create", help="Crea un nuevo cuaderno")
    p_create.add_argument("--title", required=True, help="Título del cuaderno")

    # add-source
    p_source = sub.add_parser("add-source", help="Agrega una URL como fuente")
    p_source.add_argument("notebook_id", help="ID del cuaderno")
    p_source.add_argument("--url", required=True, help="URL de YouTube u otra fuente")

    # analyze
    p_analyze = sub.add_parser("analyze", help="Analiza el cuaderno con una pregunta")
    p_analyze.add_argument("notebook_id", help="ID del cuaderno")
    p_analyze.add_argument(
        "--question",
        default="¿Cuáles son los hallazgos y temas principales de estas fuentes?",
        help="Pregunta para el análisis",
    )

    # generate
    p_gen = sub.add_parser("generate", help="Genera un entregable")
    p_gen.add_argument("notebook_id", help="ID del cuaderno")
    p_gen.add_argument(
        "--type",
        dest="artifact_type",
        default="infographic",
        choices=[
            "infographic", "slide_deck", "study_guide", "briefing_doc",
            "quiz", "flashcards", "mind_map", "audio", "video",
        ],
        help="Tipo de entregable (default: infographic)",
    )
    p_gen.add_argument(
        "--style",
        default="sketch_note",
        help="Estilo visual (sketch_note=manuscrito, professional, anime, etc.)",
    )
    p_gen.add_argument(
        "--orientation",
        default="landscape",
        choices=["landscape", "portrait", "square"],
        help="Orientación de la infografía",
    )
    p_gen.add_argument("--detail", default="standard", choices=["concise", "standard", "detailed"])
    p_gen.add_argument("--instructions", default=None, help="Instrucciones adicionales")
    p_gen.add_argument("--output", default=None, help="Archivo de salida para descargar")
    p_gen.add_argument("--language", default="es", help="Código de idioma (default: es)")

    # pipeline
    p_pipe = sub.add_parser("pipeline", help="Pipeline completo: crear + fuentes + analizar + generar")
    p_pipe.add_argument("--title", required=True, help="Título del nuevo cuaderno")
    p_pipe.add_argument("--urls", nargs="+", required=True, help="URLs de YouTube a agregar")
    p_pipe.add_argument(
        "--question",
        default="¿Cuáles son los hallazgos y temas principales de estas fuentes?",
    )
    p_pipe.add_argument("--type", dest="artifact_type", default="infographic")
    p_pipe.add_argument("--style", default="sketch_note")
    p_pipe.add_argument("--orientation", default="landscape")
    p_pipe.add_argument("--instructions", default=None)
    p_pipe.add_argument("--language", default="es")

    return parser


async def run():
    parser = build_parser()
    args = parser.parse_args()

    try:
        async with await NotebookLMClient.from_storage() as client:
            if args.command == "list":
                await cmd_list(client)

            elif args.command == "create":
                await cmd_create(client, args.title)

            elif args.command == "add-source":
                await cmd_add_source(client, args.notebook_id, args.url)

            elif args.command == "analyze":
                await cmd_analyze(client, args.notebook_id, args.question)

            elif args.command == "generate":
                await cmd_generate(
                    client,
                    args.notebook_id,
                    artifact_type=args.artifact_type,
                    style=args.style,
                    orientation=args.orientation,
                    detail=args.detail,
                    instructions=args.instructions,
                    output_file=args.output,
                    language=args.language,
                )

            elif args.command == "pipeline":
                await cmd_pipeline(
                    client,
                    title=args.title,
                    urls=args.urls,
                    question=args.question,
                    artifact_type=args.artifact_type,
                    style=args.style,
                    orientation=args.orientation,
                    instructions=args.instructions,
                    language=args.language,
                )

    except AuthError:
        print("\nERROR DE AUTENTICACION")
        print("Abre una terminal separada y ejecuta:")
        print("    notebooklm login")
        print("Luego vuelve a intentarlo.")
        sys.exit(1)
    except NotebookLMError as e:
        print(f"\nError de NotebookLM: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
