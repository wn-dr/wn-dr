"""Gera somente os ícones personalizados do manifesto, sem acesso à rede."""

import argparse
import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ICONS = ROOT / ".github/assets/icons"

# Geometria comum em uma grade 64 x 64; nenhuma fonte remota é necessária.
SYMBOLS = {
    "flow": '<rect x="12" y="24" width="10" height="16" rx="3"/><path d="M24 32h6m-3-3 3 3-3 3"/><rect x="33" y="24" width="8" height="16" rx="3"/><path d="M43 32h7m-3-3 3 3-3 3"/>',
    "pipeline": '<circle cx="16" cy="22" r="5"/><circle cx="32" cy="40" r="5"/><circle cx="49" cy="22" r="5"/><path d="m20 26 8 10m8 0 9-10"/>',
    "model": '<rect x="11" y="14" width="17" height="14" rx="2"/><rect x="37" y="34" width="17" height="14" rx="2"/><path d="M11 20h17m9 20h17M20 28v13h17"/>',
    "clean": '<path d="M19 12h20l7 7v29H19zM39 12v9h7M24 28h16m-16 7h9m0 8 5 5 13-15"/>',
    "outliers": '<path d="M14 15v33h38"/><circle cx="24" cy="39" r="2"/><circle cx="32" cy="36" r="2"/><circle cx="39" cy="40" r="2"/><circle cx="47" cy="18" r="4" fill="currentColor"/>',
    "curve": '<path d="M11 46h43M13 42c9 0 8-25 19-25s10 25 19 25"/>',
    "bars": '<path d="M13 46h39M20 42V32m12 10V16m12 26V25" stroke-width="6"/>',
    "mean": '<path d="M22 18h21M23 26l17 18m0-18L23 44"/>',
    "median": '<path d="M12 32h40M17 27v10m15-18v26m15-18v10"/><circle cx="32" cy="32" r="5" fill="currentColor"/>',
    "mode": '<path d="M13 47h39M20 42V32m12 10V17m12 25V35" stroke-width="5"/><circle cx="32" cy="12" r="2" fill="currentColor"/>',
    "hypothesis": '<path d="M11 46h43M13 42c9 0 8-25 19-25s10 25 19 25M42 31v11m5-5v5"/>',
    "board": '<rect x="11" y="14" width="42" height="34" rx="4"/><path d="M25 14v34m14-34v34M16 23h4m-4 8h4m10-8h4m10 0h4m-4 8h4"/>',
    "cycle": '<path d="M48 27a17 17 0 0 0-30-7l-4 6m0-9v9h9M16 37a17 17 0 0 0 30 7l4-6m0 9v-9h-9"/>',
    "sprint": '<path d="M24 17a17 17 0 1 1-9 23M24 10v9h-9M19 30h14l-7 8h13"/>',
    "list": '<path d="M25 19h24M25 32h24M25 45h24m-36-26 3 3 5-7m-8 17 3 3 5-7m-8 17 3 3 5-7"/>',
    "code": '<path d="m23 22-11 10 11 10m18-20 11 10-11 10m-6-27-6 34"/>',
    "database": '<ellipse cx="32" cy="17" rx="17" ry="6"/><path d="M15 17v28c0 8 34 8 34 0V17M15 30c0 8 34 8 34 0"/>',
    "network": '<path d="m20 18 24 14-24 14m0-28v28m0-14h24"/><circle cx="18" cy="18" r="5"/><circle cx="18" cy="32" r="5"/><circle cx="18" cy="46" r="5"/><circle cx="47" cy="32" r="6"/>',
    "ai": '<rect x="19" y="19" width="26" height="26" rx="5"/><path d="M26 12v7m12-7v7m-12 26v7m12-7v7M12 26h7m-7 12h7m26-12h7m-7 12h7m-26-9 6-6 6 6-6 6z"/>',
    "automation": '<path d="M20 17h24l-6-6m6 6-6 6M44 47H20l6 6m-6-6 6-6"/><rect x="12" y="27" width="14" height="12" rx="3"/><rect x="38" y="27" width="14" height="12" rx="3"/><path d="M26 33h12"/>',
    "spreadsheet": '<rect x="13" y="13" width="38" height="38" rx="4"/><path d="M13 25h38M26 13v38M26 38h25M39 25v26m-22-7 5 7m0-7-5 7"/>',
    "bi": '<path d="M17 45V32m15 13V21m15 24V12" stroke-width="8"/>',
    "chat": '<path d="M15 15h34v27H30l-12 9v-9h-3zM22 25h20m-20 8h14"/>',
    "assistant": '<path d="m32 12 5 14 15 6-15 6-5 14-5-14-15-6 15-6z"/>',
}


def render_icon(item):
    """Desenha um cartão independente de tema com título acessível."""
    accent = item["accent"]
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", accent):
        raise ValueError(f"Cor inválida: {accent}")
    if "symbol" in item:
        artwork = SYMBOLS[item["symbol"]]
    else:
        label = escape(item["label"])
        artwork = (f'<text x="32" y="34" text-anchor="middle" '
                   f'dominant-baseline="middle" font-family="sans-serif" '
                   f'font-size="18" font-weight="700" fill="currentColor" '
                   f'stroke="none">{label}</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" '
            f'viewBox="0 0 64 64" role="img" aria-labelledby="title">\n'
            f'  <title id="title">{escape(item["name"])}</title>\n'
            '  <rect x="1" y="1" width="62" height="62" rx="14" '
            'fill="#F1F5F9" stroke="#94A3B8"/>\n'
            f'  <g color="{accent}" fill="none" stroke="currentColor" '
            f'stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">{artwork}</g>\n'
            f'  <rect x="25" y="56" width="14" height="3" rx="1.5" fill="{accent}"/>\n'
            '</svg>\n')


def generate(check=False):
    manifest = json.loads((ROOT / "scripts/icon_manifest.json").read_text(encoding="utf-8"))
    slugs = [item["slug"] for item in manifest]
    if len(slugs) != len(set(slugs)):
        raise ValueError("Slugs duplicados no manifesto")
    outdated = []
    count = 0
    for item in manifest:
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", item["slug"]):
            raise ValueError("Slug inválido")
        # Assets de marca são versionados manualmente e nunca sobrescritos.
        if item["kind"] == "brand":
            continue
        if item["kind"] != "custom":
            raise ValueError(f'Tipo desconhecido: {item["kind"]}')
        target = ICONS / f'{item["slug"]}.svg'
        content = render_icon(item)
        count += 1
        if not target.exists() or target.read_text(encoding="utf-8") != content:
            if check:
                outdated.append(str(target.relative_to(ROOT)))
            else:
                ICONS.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8", newline="\n")
    if outdated:
        print("Ícones desatualizados:\n" + "\n".join(outdated))
        return 1
    print(f"Ícones personalizados {'verificados' if check else 'gerados'}: {count}. Logos de marca preservados.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verifica sem gravar arquivos")
    args = parser.parse_args()
    raise SystemExit(generate(args.check))
