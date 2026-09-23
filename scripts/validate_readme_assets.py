"""Valida imagens locais, capitalização, acessibilidade e SVGs autocontidos."""

import argparse
import json
import math
import re
import xml.etree.ElementTree as ET
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


class ReadmeHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.images, self.errors, self.stack = [], [], []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag not in VOID:
            self.stack.append(tag)
        if tag == "img":
            if not attrs.get("alt", "").strip() or attrs.get("alt", "").lower() in {"icon", "image", "ícone"}:
                self.errors.append("Imagem HTML sem alt descritivo")
            if not attrs.get("src"):
                self.errors.append("Imagem HTML sem src")
            else:
                self.images.append(attrs["src"])
            if ".github/assets/icons/" in attrs.get("src", ""):
                if attrs.get("width") != "48" or attrs.get("height") != "48":
                    self.errors.append("Ícone fora do padrão 48 x 48")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f"HTML: fechamento inesperado </{tag}>")
        else:
            self.stack.pop()


def markdown_images(text):
    """Lê imagens inline (incluindo parênteses) e referências Markdown."""
    references = {m[1].strip().casefold(): m[2] or m[3] for m in re.finditer(
        r'^\s{0,3}\[([^\]]+)\]:\s*(?:<([^>]+)>|(\S+))', text, re.M)}
    images, errors = [], []
    for match in re.finditer(r'(?<!\\)!\[((?:\\.|[^\]\\])*)\]', text):
        alt = match[1]
        if not alt.strip():
            errors.append("Imagem Markdown sem alt descritivo")
        tail = text[match.end():]
        if tail.startswith("("):
            tail = tail[1:].lstrip()
            if tail.startswith("<"):
                end = tail.find(">")
                if end == -1:
                    errors.append("Destino Markdown sem fechamento")
                    continue
                images.append(tail[1:end])
                continue
            depth, escaped, destination = 0, False, []
            for char in tail:
                if escaped:
                    destination.append(char)
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == "(" :
                    depth += 1
                    destination.append(char)
                elif char == ")":
                    if depth == 0:
                        break
                    depth -= 1
                    destination.append(char)
                elif char.isspace() and depth == 0:
                    break
                else:
                    destination.append(char)
            else:
                errors.append("Imagem Markdown sem fechamento")
            images.append("".join(destination))
        else:
            reference = re.match(r'\[([^\]]*)\]', tail)
            key = ((reference[1] or alt) if reference else alt).strip().casefold()
            if key in references:
                images.append(references[key])
            elif reference:
                errors.append(f"Referência Markdown ausente: {key}")
    return images, errors


def resolve_local(root, source):
    """Percorre cada componente para detectar case incorreto também no Windows."""
    source = unescape(source)
    parsed = urlsplit(source)
    if parsed.scheme in {"http", "https"} or source.startswith("//"):
        return None, None
    if parsed.scheme:
        return None, f"Esquema de imagem não permitido: {source}"
    decoded = unquote(parsed.path)
    if not decoded or "\\" in decoded:
        return None, f"Caminho inválido: {source}"
    current = root.resolve()
    wrong_case = False
    for component in decoded.lstrip("/").split("/"):
        if component in {"", "."}:
            continue
        if component == "..":
            current = current.parent
            if not current.is_relative_to(root.resolve()):
                return None, f"Caminho fora do repositório: {source}"
            continue
        if not current.is_dir():
            return None, f"Missing: {source}"
        names = {p.name: p for p in current.iterdir()}
        if component in names:
            current = names[component]
        else:
            candidates = [p for name, p in names.items() if name.casefold() == component.casefold()]
            if len(candidates) != 1:
                return None, f"Missing: {source}"
            current = candidates[0]
            wrong_case = True
        if not current.resolve().is_relative_to(root.resolve()):
            return None, f"Caminho fora do repositório: {source}"
    if not current.is_file():
        return None, f"Missing: {source}"
    if wrong_case:
        return current, f"Case mismatch: {source} -> {current.relative_to(root).as_posix()}"
    return current, None


def validate_svg(path):
    errors = []
    try:
        raw = path.read_text(encoding="utf-8")
        if re.search(r'<!\s*(?:DOCTYPE|ENTITY)', raw, re.I):
            return ["DTD/entidades não permitidas"]
        svg = ET.fromstring(raw)
    except (OSError, UnicodeError, ET.ParseError) as exc:
        return [f"XML inválido: {exc}"]
    if svg.tag != "{http://www.w3.org/2000/svg}svg":
        errors.append("Raiz/namespace SVG inválido")
    try:
        box = [float(n) for n in re.split(r'[\s,]+', svg.attrib["viewBox"].strip())]
        if len(box) != 4 or not all(math.isfinite(n) for n in box) or min(box[2:]) <= 0:
            raise ValueError
    except (KeyError, ValueError):
        errors.append("viewBox ausente ou inválido")
    ids = [el.attrib["id"] for el in svg.iter() if "id" in el.attrib]
    if len(ids) != len(set(ids)):
        errors.append("IDs duplicados")
    refs = []
    for element in svg.iter():
        tag = element.tag.rsplit("}", 1)[-1].lower()
        if tag in {"script", "foreignobject", "iframe", "animate", "animatetransform", "animatemotion", "set"}:
            errors.append(f"Elemento ativo não permitido: {tag}")
        values = []
        for key, value in element.attrib.items():
            local_key = key.rsplit("}", 1)[-1].lower()
            if local_key.startswith("on"):
                errors.append(f"Evento JavaScript não permitido: {key}")
            if local_key in {"href", "src"}:
                refs.append(value.strip())
            if local_key in {"aria-labelledby", "aria-describedby"}:
                refs.extend("#" + entry for entry in value.split())
            values.append(value)
        if tag == "style":
            values.append("".join(element.itertext()))
        for value in values:
            if re.search(r'javascript\s*:|@import|expression\s*\(|\\', value, re.I):
                errors.append("Conteúdo ativo ou CSS externo/ofuscado não permitido")
            refs.extend(m.strip().strip("\"'") for m in re.findall(r'url\s*\(([^)]*)\)', value, re.I))
    for ref in refs:
        if not ref.startswith("#"):
            errors.append(f"Referência externa não permitida: {ref}")
        elif ref[1:] not in ids:
            errors.append(f"Referência interna ausente: {ref}")
    return errors


def validate(root=ROOT):
    root = root.resolve()
    try:
        text = (root / "README.md").read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [f"README.md: {exc}"]
    # Exemplos de código e comentários não são imagens renderizadas.
    text = re.sub(r'(?ms)^\s{0,3}(`{3,}|~{3,})[^\n]*\n.*?^\s{0,3}\1\s*$', '', text)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'`[^`\n]+`', '', text)
    parser = ReadmeHTML()
    # Destinos Markdown entre <...> e autolinks não são tags HTML.
    html_text = re.sub(r'(!\[(?:\\.|[^\]])*\]\()\s*<[^>]*>', r'\1', text)
    html_text = re.sub(r'<(?:https?://|mailto:)[^>]+>', '', html_text)
    parser.feed(html_text)
    parser.close()
    errors = parser.errors
    if parser.stack:
        errors.append("HTML: tags não fechadas: " + ", ".join(parser.stack))
    markdown, md_errors = markdown_images(text)
    errors.extend(md_errors)
    svg_paths = set(root.glob(".github/assets/icons/*.svg"))
    for source in sorted(set(parser.images + markdown)):
        path, error = resolve_local(root, source)
        if error:
            errors.append(error)
        if path and path.suffix.lower() == ".svg":
            svg_paths.add(path)
    manifest_path = root / "scripts/icon_manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            seen = set()
            for item in manifest:
                slug = item["slug"]
                if slug in seen:
                    errors.append(f"Slug duplicado: {slug}")
                seen.add(slug)
                source = f".github/assets/icons/{slug}.svg"
                _, error = resolve_local(root, source)
                if error:
                    errors.append(error)
                if source not in parser.images + markdown:
                    errors.append(f"Ícone do manifesto não utilizado: {source}")
        except (ValueError, KeyError, TypeError) as exc:
            errors.append(f"Manifesto inválido: {exc}")
    for path in sorted(svg_paths):
        errors.extend(f"{path.relative_to(root).as_posix()}: {error}" for error in validate_svg(path))
    return sorted(set(errors))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Raiz do repositório")
    errors = validate(parser.parse_args().root)
    if errors:
        print("README asset validation: FAILED\n")
        missing = [error.removeprefix("Missing: ") for error in errors if error.startswith("Missing: ")]
        if missing:
            print("Missing:\n" + "\n".join(missing))
        other = [error for error in errors if not error.startswith("Missing: ")]
        if other:
            print("Errors:\n" + "\n".join(other))
        return 1
    print("README asset validation: OK\nAll local image assets were found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
