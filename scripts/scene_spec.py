#!/usr/bin/env python3
"""Scaffold, validate, and compile concise Higgsfield scene prompts."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - depends on host runtime
    raise SystemExit(
        "PyYAML is required for scene_spec.py. Run it with a Python environment "
        "where `import yaml` succeeds."
    ) from exc

FILL_PREFIX = "<HIGGSFIELD_FILL"
REQUIRED_CONSTRAINTS = {
    "spatial_clarity",
    "ceiling_visible",
    "no_people",
    "no_dead_space",
    "daylight_windows",
    "no_spec_text",
}
REQUIRED_NODES = {
    "architecture",
    "major_furnishings",
    "lighting_fixtures",
    "decor_and_fill",
}
FORBIDDEN_SCENE_KEYS = {
    "id",
    "output",
    "generation",
    "aspect_ratio",
    "candidate_count",
    "repair_attempts",
    "image_role",
    "model",
    "models",
    "model_policy",
    "media_id",
    "media_ids",
    "product_media_ids",
    "reference_images",
    "status",
    "value",
    "guidance",
}


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping at the root.")
    return data


def nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict)):
        return bool(value)
    return True


def is_fill(value: Any) -> bool:
    return isinstance(value, str) and value.strip().startswith(FILL_PREFIX)


def walk_paths(value: Any, path: str = ""):
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            yield child_path, child
            yield from walk_paths(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            yield child_path, child
            yield from walk_paths(child, child_path)


def validate_scene(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1.")
    if "generation" in data:
        errors.append(
            "Top-level generation is not allowed; keep API configuration outside scene.yaml."
        )

    asset = data.get("asset")
    if not isinstance(asset, dict) or not nonempty(asset.get("id")) or not nonempty(asset.get("name")):
        errors.append("asset.id and asset.name are required.")

    scene = data.get("scene")
    if not isinstance(scene, dict):
        errors.append("scene must be a mapping.")
        return errors
    for key in ("intent", "composition", "style", "constraints", "nodes"):
        if key not in scene:
            errors.append(f"scene.{key} is required.")

    unresolved = re.compile(r"\{\{[^}]+\}\}")
    fill_count = 0
    concrete_count = 0
    for path, value in walk_paths(scene):
        key = path.rsplit(".", 1)[-1]
        if key in FORBIDDEN_SCENE_KEYS:
            errors.append(
                f"scene contains API or obsolete field {path!r}; move it outside scene or remove it."
            )
        if isinstance(value, str):
            if unresolved.search(value):
                errors.append(f"{path} still contains an unresolved template value: {value}")
            if is_fill(value):
                fill_count += 1
            elif value.strip():
                concrete_count += 1
    if fill_count == 0:
        errors.append("At least one <HIGGSFIELD_FILL> placeholder is required.")
    if concrete_count == 0:
        errors.append("At least one concrete scene value is required.")

    constraints = scene.get("constraints", {})
    if not isinstance(constraints, dict):
        errors.append("scene.constraints must be a mapping.")
    else:
        missing = sorted(REQUIRED_CONSTRAINTS - set(constraints))
        if missing:
            errors.append(f"Missing constraints: {', '.join(missing)}")

    nodes = scene.get("nodes", {})
    if not isinstance(nodes, dict):
        errors.append("scene.nodes must be a mapping.")
        nodes = {}
    for node_name in REQUIRED_NODES:
        if node_name not in nodes:
            errors.append(f"scene.nodes.{node_name} is required.")
    hero_product = nodes.get("hero_product")
    if isinstance(hero_product, dict) and "identity" in hero_product:
        errors.append(
            "scene.nodes.hero_product.identity is not allowed; exact reference consistency "
            "is added automatically by the compiler."
        )
    return errors


def build_prompt(data: dict[str, Any], style_guide: str) -> str:
    scene = data["scene"]
    has_hero_product = "hero_product" in scene.get("nodes", {})
    scene_tree = yaml.safe_dump(
        {"scene": scene},
        allow_unicode=True,
        sort_keys=False,
        width=2000,
    ).rstrip()

    product_block = (
        "PRODUCT AUTHORITY\n"
        "Keep the hero product exactly consistent with the attached product reference image. "
        "Use the reference only for the product itself; unless explicitly requested, ignore every "
        "other object and the original scene. Honor the instance count and placement required by "
        "the scene tree.\n"
        if has_hero_product
        else "PRODUCT AUTHORITY\nNo hero product is required.\n"
    )

    return f"""\
HIGGSFIELD SCENE REFERENCE
Create one seamless photorealistic architectural interior reference with a clear spatial layout, readable furniture contacts and circulation, and the full ceiling with visible light fixtures.

{product_block}
SCENE TREE
```yaml
{scene_tree}
```

OPEN FIELDS: Resolve each `<HIGGSFIELD_FILL>` into a coherent visual choice. When furnishings are OPEN, use an intentional, non-default seating program and vary its typology or arrangement between distinct scene concepts. Never render placeholders, field names, specification markup, labels, or readable text.

STYLE GUIDE
{style_guide.strip()}

PRIORITY: Product identity > explicit constraints > concrete scene values > OPEN-field resolution.
FINAL LIMITS: No people or portraits. Daylight windows only. No dead zones, floating or duplicated objects, impossible geometry, fisheye distortion, logos, or text.
"""


def validate_style_guide(style_guide: str) -> list[str]:
    errors: list[str] = []
    lines = [line.strip() for line in style_guide.splitlines() if line.strip()]
    if len(lines) > 8:
        errors.append(
            "Style guide must use at most 8 lines: one labeled line per design dimension."
        )
    if any(len(line) > 180 for line in lines):
        errors.append(
            "A style-guide line exceeds 180 characters; keep each dimension to a few precise keywords."
        )

    palette_lines = [
        line
        for line in lines
        if re.match(r"^(?:palette|color palette)(?:\s*/\s*materials)?\s*:", line, re.IGNORECASE)
    ]
    if not palette_lines:
        errors.append("Style guide requires a Palette line with color percentages.")
        return errors

    percentages = [int(value) for value in re.findall(r"(\d{1,3})%", palette_lines[0])]
    if len(percentages) < 2:
        errors.append(
            "Palette must include at least two percentage-weighted colors from visibly "
            "distinct hue families."
        )
    if sum(percentages) != 100:
        errors.append(f"Palette percentages must total 100%; got {sum(percentages)}%.")
    return errors


def command_scaffold(args: argparse.Namespace) -> int:
    target = Path(args.path)
    if target.exists():
        raise SystemExit(f"Refusing to overwrite existing path: {target}")
    template = Path(__file__).resolve().parents[1] / "assets" / "scene-template.yaml"
    if not template.exists():
        raise SystemExit(f"Scene template not found: {template}")

    target.mkdir(parents=True)
    (target / "refs").mkdir()
    (target / "prompts").mkdir()
    (target / "outputs").mkdir()
    content = template.read_text(encoding="utf-8")
    content = content.replace("{{scene_slug}}", args.id)
    content = content.replace("{{scene_name}}", args.name)
    content = content.replace("{{scene_intent}}", args.intent)
    (target / "scene.yaml").write_text(content, encoding="utf-8")
    print(target / "scene.yaml")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    path = Path(args.scene)
    data = load_yaml(path)
    errors = validate_scene(data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Valid scene specification: {path}")
    return 0


def command_compile(args: argparse.Namespace) -> int:
    scene_path = Path(args.scene)
    data = load_yaml(scene_path)
    errors = validate_scene(data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    style_path = Path(args.style_guide)
    style_guide = style_path.read_text(encoding="utf-8").strip()
    if not style_guide:
        raise SystemExit(f"Style guide is empty: {style_path}")
    style_errors = validate_style_guide(style_guide)
    if style_errors:
        raise SystemExit("\n".join(style_errors))
    prompt = build_prompt(data, style_guide)
    line_count = len(prompt.splitlines())
    if line_count > args.max_lines:
        raise SystemExit(
            f"Compiled prompt is {line_count} lines; maximum is {args.max_lines}. "
            "Shorten the scene tree, style guide, or filenames."
        )

    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(prompt, encoding="utf-8")
    print(f"{output} ({line_count} lines)")
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)

    scaffold = sub.add_parser("scaffold", help="Create a versioned scene workspace from the template.")
    scaffold.add_argument("path")
    scaffold.add_argument("--id", required=True)
    scaffold.add_argument("--name", required=True)
    scaffold.add_argument("--intent", default="Reusable scene reference for multiple shots")
    scaffold.set_defaults(func=command_scaffold)

    validate = sub.add_parser("validate", help="Validate a scene YAML file.")
    validate.add_argument("scene")
    validate.set_defaults(func=command_validate)

    compile_cmd = sub.add_parser("compile", help="Compile a scene YAML and style guide into a concise prompt.")
    compile_cmd.add_argument("scene")
    compile_cmd.add_argument("--style-guide", required=True)
    compile_cmd.add_argument("--out", required=True)
    compile_cmd.add_argument("--max-lines", type=int, default=100)
    compile_cmd.set_defaults(func=command_compile)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        return args.func(args)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
