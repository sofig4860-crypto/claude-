#!/usr/bin/env python3
"""
YouTube Research Skill — yt-research
====================================
Extrae metadatos de YouTube usando yt-dlp: títulos, vistas, autor,
duración y URLs a partir de una consulta de búsqueda.

Uso desde Claude Code:
    /yt-research <consulta> [--limit N]

Uso directo:
    python yt-research.py "inteligencia artificial 2025" --limit 25
"""

import argparse
import json
import sys

import yt_dlp


def search_youtube(query: str, limit: int = 25) -> list[dict]:
    """
    Busca videos en YouTube y devuelve metadatos estructurados.

    Args:
        query: Consulta de búsqueda.
        limit: Número máximo de resultados (default 25).

    Returns:
        Lista de dicts con title, url, views, author, duration_sec, upload_date.
    """
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "force_generic_extractor": False,
        "default_search": "ytsearch",
        "playlist_items": f"1-{limit}",
        "nocheckcertificate": True,  # needed in environments with SSL inspection proxies
    }

    search_query = f"ytsearch{limit}:{query}"

    results = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_query, download=False)
        entries = info.get("entries", []) if info else []

        for entry in entries:
            if not entry:
                continue

            duration_sec = entry.get("duration") or 0
            minutes, seconds = divmod(int(duration_sec), 60)
            hours, minutes = divmod(minutes, 60)
            if hours:
                duration_str = f"{hours}h {minutes}m {seconds}s"
            else:
                duration_str = f"{minutes}m {seconds}s"

            results.append(
                {
                    "title": entry.get("title", "Sin título"),
                    "url": entry.get("url") or f"https://www.youtube.com/watch?v={entry.get('id', '')}",
                    "views": entry.get("view_count"),
                    "author": entry.get("uploader") or entry.get("channel", "Desconocido"),
                    "duration_sec": duration_sec,
                    "duration": duration_str,
                    "upload_date": entry.get("upload_date", ""),
                    "video_id": entry.get("id", ""),
                }
            )

    return results


def format_results(results: list[dict]) -> str:
    """Formatea los resultados como texto legible para Claude."""
    if not results:
        return "No se encontraron resultados."

    lines = [f"## Resultados de YouTube ({len(results)} videos)\n"]
    for i, v in enumerate(results, 1):
        views = f"{v['views']:,}" if v["views"] else "N/D"
        lines.append(
            f"### {i}. {v['title']}\n"
            f"- **URL:** {v['url']}\n"
            f"- **Canal:** {v['author']}\n"
            f"- **Vistas:** {views}\n"
            f"- **Duración:** {v['duration']}\n"
            f"- **Fecha de subida:** {v['upload_date'] or 'N/D'}\n"
        )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Busca videos en YouTube y extrae sus metadatos."
    )
    parser.add_argument("query", help="Consulta de búsqueda")
    parser.add_argument(
        "--limit", type=int, default=25, help="Número máximo de resultados (default: 25)"
    )
    parser.add_argument(
        "--json", action="store_true", dest="as_json", help="Salida en formato JSON"
    )
    args = parser.parse_args()

    print(f"Buscando '{args.query}' en YouTube (máximo {args.limit} videos)...\n", file=sys.stderr)

    results = search_youtube(args.query, args.limit)

    if args.as_json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(format_results(results))

    return results


if __name__ == "__main__":
    main()
