# Higgsfield Scene Reference

Create reusable, YAML-defined scene reference images with Higgsfield. The YAML
tree is the source of truth for room design, spatial relationships, furnishings,
ceiling fixtures, and optional hero-product placement. The generated image can
then be reused as a visual reference for different camera setups without
rebuilding the environment.

This skill is designed to take advantage of Higgsfield's own prompt LLM: lock
only the decisions that must remain stable, leave secondary details as
`<HIGGSFIELD_FILL>` placeholders, and provide a short keyword-led style guide.

## What it does

- Scaffolds a scene tree from `assets/scene-template.yaml`.
- Validates locked values, placeholders, palette ratios, and API-data boundaries.
- Compiles a concise Higgsfield prompt capped at 100 lines.
- Supports product references without inventing or copying unrelated product details.
- Enforces clear spatial composition, a visible ceiling and fixtures, no people or portraits, purposeful density, and bright daytime window views.
- Keeps generation metadata outside `scene.yaml`.

## Requirements

- A Codex environment with the Higgsfield tools or plugin available.
- PowerShell 7 for the bundled Windows wrapper.
- Python 3 with PyYAML.

## Install

Clone the repository into your Codex skills directory:

```powershell
git clone https://github.com/ZavierYan/higgsfield-scene-reference.git `
  "$env:USERPROFILE\.codex\skills\higgsfield-scene-reference"
```

Restart or reload Codex if the skill is not detected automatically.

## Usage

Invoke the skill with a scene brief:

```text
Use $higgsfield-scene-reference to create a reusable reference image for a warm,
quiet-luxury living room. The camera must show two wall planes and the ceiling.
```

For a hero product, attach its reference image and state where it must appear.
The skill will preserve the product identity from the image while defining only
its scene-specific placement and state in YAML.

Typical scene generation:

```powershell
pwsh scripts/run_scene_spec.ps1 scaffold scenes/<slug> --id <slug> --name "<scene name>"
pwsh scripts/run_scene_spec.ps1 validate scenes/<slug>/scene.yaml
pwsh scripts/run_scene_spec.ps1 compile scenes/<slug>/scene.yaml `
  --style-guide scenes/<slug>/style-guide.txt `
  --out scenes/<slug>/prompts/reference-v1.txt
```

Use `nano_banana_pro` at 2K when product references are attached. Use
`soul_location` when no product reference is supplied.

## Repository layout

```text
SKILL.md
agents/openai.yaml
assets/scene-template.yaml
references/scene-workflow.md
scripts/scene_spec.py
scripts/run_scene_spec.ps1
```

`scene_spec.py` contains three commands:

- `scaffold`: create a scene directory from the template.
- `validate`: check the YAML tree and hard constraints.
- `compile`: produce the compact prompt sent to Higgsfield.

## Design principles

1. Lock stable decisions; leave room for Higgsfield to resolve secondary details.
2. Keep prompts short and professional rather than exhaustively specifying every object.
3. Use at least two visibly distinct hue families with explicit palette percentages.
4. Reuse accepted scene references instead of regenerating the environment.
5. Create a sibling scene when layout or product identity materially changes.

## License

No license has been specified for this repository.
