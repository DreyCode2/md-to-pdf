#!/usr/bin/env python3
"""
mdforge — minimal Markdown-to-PDF converter with syntax highlighting
and live preview.
"""

import os
import sys
import time
import hashlib
from pathlib import Path

import click
import yaml
import markdown2
import jinja2
from pygments.formatters import HtmlFormatter
from slugify import slugify
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from weasyprint import HTML

console = Console()

TEMPLATE_DIR = Path(__file__).parent / "templates"

# ── built-in themes ────────────────────────────────────────────

_THEMES = {
    "clean": {
        "pygments": "default",
        "css": """
            @page { size: A4; margin: 2.5cm; }
            body { font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
                   font-size: 11pt; line-height: 1.6; color: #1a1a1a; }
            .doc-header { margin-bottom: 2em; border-bottom: 1px solid #ddd; padding-bottom: 1em; }
            .doc-title { font-size: 24pt; margin: 0 0 .3em; }
            .doc-meta { color: #666; font-size: 10pt; margin: 0; }
            h1 { font-size: 20pt; margin-top: 1.5em; }
            h2 { font-size: 16pt; margin-top: 1.3em; }
            h3 { font-size: 13pt; margin-top: 1.1em; }
            code { background: #f4f4f4; padding: .15em .35em; border-radius: 3px; font-size: .9em; }
            pre { background: #f8f8f8; padding: 1em; border-radius: 4px; overflow-x: auto; }
            pre code { background: none; padding: 0; }
            table { border-collapse: collapse; width: 100%; margin: 1em 0; }
            th, td { border: 1px solid #ddd; padding: .5em .75em; text-align: left; }
            th { background: #f4f4f4; }
            blockquote { border-left: 3px solid #ccc; margin: 1em 0; padding: .5em 1em; color: #555; }
            img { max-width: 100%; } a { color: #2563eb; }
        """,
    },
    "academic": {
        "pygments": "borland",
        "css": """
            @page { size: A4; margin: 3cm 2.5cm; }
            body { font-family: 'Times New Roman', Georgia, serif;
                   font-size: 12pt; line-height: 1.8; color: #000; }
            .doc-header { text-align: center; margin-bottom: 3em; }
            .doc-title { font-size: 18pt; font-weight: normal; margin: 0 0 .5em; }
            .doc-meta { font-size: 11pt; color: #333; margin: 0; }
            h1 { font-size: 16pt; margin-top: 2em; }
            h2 { font-size: 14pt; margin-top: 1.6em; }
            h3 { font-size: 12pt; font-style: italic; margin-top: 1.3em; }
            code { font-family: 'Courier New', monospace; font-size: .85em; }
            pre { border: 1px solid #ccc; padding: .8em; font-size: .85em; }
            table { border-collapse: collapse; width: 100%; margin: 1.5em 0; }
            th, td { border: 1px solid #000; padding: .4em .6em; }
            blockquote { margin: 1.5em 2em; font-style: italic; }
            a { color: #000; text-decoration: underline; }
        """,
    },
    "dark": {
        "pygments": "monokai",
        "css": """
            @page { size: A4; margin: 2.5cm; }
            body { font-family: 'Inter', 'Segoe UI', sans-serif;
                   font-size: 11pt; line-height: 1.6; color: #e0e0e0; background: #1e1e1e; }
            .doc-header { margin-bottom: 2em; border-bottom: 1px solid #444; padding-bottom: 1em; }
            .doc-title { font-size: 24pt; margin: 0 0 .3em; color: #fff; }
            .doc-meta { color: #999; font-size: 10pt; margin: 0; }
            h1 { color: #fff; font-size: 20pt; }
            h2 { color: #ddd; font-size: 16pt; }
            code { background: #2d2d2d; padding: .15em .35em; border-radius: 3px; }
            pre { background: #2d2d2d; padding: 1em; border-radius: 4px; }
            pre code { background: none; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #444; padding: .5em .75em; }
            th { background: #2d2d2d; }
            blockquote { border-left: 3px solid #555; padding: .5em 1em; color: #aaa; }
            a { color: #6ea8fe; }
        """,
    },
    "minimal": {
        "pygments": "friendly",
        "css": """
            @page { size: A4; margin: 2cm; }
            body { font-family: system-ui, -apple-system, sans-serif;
                   font-size: 10.5pt; line-height: 1.55; color: #222; }
            .doc-header { margin-bottom: 1.5em; }
            .doc-title { font-size: 20pt; font-weight: 600; margin: 0; }
            .doc-meta { color: #888; font-size: 9pt; margin: .3em 0 0; }
            h1 { font-size: 17pt; } h2 { font-size: 14pt; }
            code { font-size: .88em; }
            pre { padding: .8em; background: #fafafa; }
            table { border-collapse: collapse; }
            th, td { border-bottom: 1px solid #eee; padding: .4em .6em; }
            th { text-align: left; font-weight: 600; }
            blockquote { margin-left: 0; padding-left: 1em; border-left: 2px solid #ddd; color: #666; }
            a { color: #111; text-decoration: underline; }
        """,
    },
    "newsletter": {
        "pygments": "autumn",
        "css": """
            @page { size: A4; margin: 2.5cm 3cm; }
            body { font-family: Georgia, 'Times New Roman', serif;
                   font-size: 11.5pt; line-height: 1.7; color: #2c2c2c; max-width: 38em; }
            .doc-header { margin-bottom: 2.5em; }
            .doc-title { font-size: 28pt; font-weight: 700; margin: 0 0 .2em; letter-spacing: -.02em; }
            .doc-meta { font-size: 10pt; color: #777; margin: 0;
                        text-transform: uppercase; letter-spacing: .05em; }
            h1 { font-size: 20pt; margin-top: 2em; }
            h2 { font-size: 15pt; margin-top: 1.5em; text-transform: uppercase;
                 letter-spacing: .03em; font-weight: 600; }
            code { background: #f0ede6; padding: .1em .3em; border-radius: 2px; }
            pre { background: #f9f7f3; padding: 1em; border-left: 3px solid #c9a96e; }
            pre code { background: none; }
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: .5em; border-bottom: 1px solid #ddd; }
            blockquote { font-style: italic; border-left: 3px solid #c9a96e;
                         margin: 1.5em 0; padding: .5em 1.2em; color: #555; }
            a { color: #8b5e3c; }
        """,
    },
}


def _theme_css(name: str) -> str:
    return _THEMES[name]["css"]


def _code_css(name: str) -> str:
    style = _THEMES[name]["pygments"]
    return HtmlFormatter(style=style).get_style_defs("pre code")


# ── markdown helpers ────────────────────────────────────────────

def _read_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("---", 3)
    if end < 0:
        return {}, text
    try:
        meta = yaml.safe_load(text[3:end]) or {}
    except yaml.YAMLError:
        meta = {}
    return meta, text[end + 3 :].lstrip("\n")


def _md_to_html(body: str) -> str:
    return markdown2.markdown(
        body,
        extras=[
            "fenced-code-blocks", "tables", "footnotes",
            "strike", "task_list", "header-ids", "code-friendly",
        ],
    )


def _output_name(meta: dict, src: Path, suffix: str = ".pdf") -> Path:
    """Derive output filename from frontmatter title or source name."""
    title = meta.get("title")
    if title:
        return src.parent / (slugify(title, max_length=64) + suffix)
    return src.with_suffix(suffix)


def _render_pdf(src: Path, dst: Path, theme: str, template_name: str, toc: bool) -> None:
    raw = src.read_text(encoding="utf-8")
    meta, body = _read_frontmatter(raw)

    html_body = _md_to_html(body)
    theme_css = _theme_css(theme)
    code_css = _code_css(theme)
    highlight_inline = HtmlFormatter(style="monokai", nowrap=False).get_style_defs(".highlight")

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=False,
    )
    tmpl = env.get_template(template_name)
    full_html = tmpl.render(
        title=meta.get("title", src.stem),
        author=meta.get("author", ""),
        date=meta.get("date", ""),
        body=html_body,
        theme_css=theme_css,
        code_css=code_css,
        highlight_css=highlight_inline,
        toc=toc,
    )
    HTML(string=full_html).write_pdf(str(dst))


def _file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


# ── CLI ─────────────────────────────────────────────────────────

@click.group()
@click.version_option("0.4.1", prog_name="mdforge")
def cli():
    """mdforge — convert Markdown files to styled PDFs."""


@cli.command()
@click.argument("source", type=click.Path(exists=True))
@click.option("-o", "--output", default=None, help="Output path (default: derived from title/source)")
@click.option("-t", "--theme", default="clean", help="CSS theme (see `mdforge themes`)")
@click.option("--template", "template_name", default="default.html", help="Jinja2 template")
@click.option("--toc", is_flag=True, help="Generate table of contents")
def build(source, output, theme, template_name, toc):
    """Convert a Markdown file to PDF."""
    src = Path(source)

    if theme not in _THEMES:
        console.print(f"[red]unknown theme:[/red] {theme}")
        console.print(f"available: {', '.join(_THEMES)}")
        raise SystemExit(1)

    meta, _ = _read_frontmatter(src.read_text(encoding="utf-8"))
    dst = Path(output) if output else _output_name(meta, src)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as prog:
        task = prog.add_task("rendering...", total=None)
        _render_pdf(src, dst, theme, template_name, toc)
        prog.update(task, description="done")

    size_kb = dst.stat().st_size / 1024
    console.print(f"[green]wrote[/green] {dst}  [dim]({size_kb:.1f} KB)[/dim]")


@cli.command()
@click.argument("source", type=click.Path(exists=True))
@click.option("-t", "--theme", default="clean")
@click.option("--template", "template_name", default="default.html")
@click.option("--toc", is_flag=True)
def watch(source, theme, template_name, toc):
    """Watch a Markdown file and rebuild on changes."""
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    src = Path(source)
    meta, _ = _read_frontmatter(src.read_text(encoding="utf-8"))
    dst = _output_name(meta, src)
    last_hash = ""

    class Handler(FileSystemEventHandler):
        def on_modified(self, event):
            nonlocal last_hash
            if Path(event.src_path).resolve() != src.resolve():
                return
            h = _file_hash(src)
            if h == last_hash:
                return
            last_hash = h
            try:
                _render_pdf(src, dst, theme, template_name, toc)
                console.print(f"[green]rebuilt[/green] {dst}")
            except Exception as exc:
                console.print(f"[red]error:[/red] {exc}")

    observer = Observer()
    observer.schedule(Handler(), str(src.parent), recursive=False)
    observer.start()
    console.print(f"[dim]watching {src} — Ctrl+C to stop[/dim]")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


@cli.command(name="themes")
def list_themes_cmd():
    """List available CSS themes."""
    for name in _THEMES:
        console.print(f"  [cyan]{name}[/cyan]")


@cli.command()
@click.argument("source", type=click.Path(exists=True))
@click.option("-t", "--theme", default="clean")
def html(source, theme):
    """Convert a Markdown file to standalone HTML."""
    src = Path(source)
    raw = src.read_text(encoding="utf-8")
    meta, body = _read_frontmatter(raw)
    dst = _output_name(meta, src, suffix=".html")

    html_body = _md_to_html(body)
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)), autoescape=False)
    tmpl = env.get_template("default.html")
    out = tmpl.render(
        title=meta.get("title", src.stem),
        author=meta.get("author", ""),
        date=meta.get("date", ""),
        body=html_body,
        theme_css=_theme_css(theme),
        code_css=_code_css(theme),
        highlight_css="",
        toc=False,
    )
    dst.write_text(out, encoding="utf-8")
    console.print(f"[green]wrote[/green] {dst}")


if __name__ == "__main__":
    cli()
