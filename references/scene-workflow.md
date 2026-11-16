# Scene Reference Workflow

This reference defines the compact schema and generation behavior. Use it with `assets/scene-template.yaml`.

## Data boundary

`scene.yaml` has two top-level parts:

- `asset`: local naming and storage metadata;
- `scene`: the creative tree that may be sent to Higgsfield.

The prompt compiler sends only `scene`. Keep model, aspect ratio, resolution, candidate count, repair budget, and reference media IDs in the API call or generation record, never in `scene.yaml`.

## Placeholder semantics

A concrete string is locked. A string beginning with `<HIGGSFIELD_FILL>` is open:

```yaml
palette: "Warm ivory, greige limestone, and smoked walnut"
wall_treatment: "<HIGGSFIELD_FILL: restrained finish consistent with the palette>"
```

Do not add `status`, `value`, `guidance`, or another control wrapper. Put a short design-space hint directly in the placeholder only when the intended range is not obvious.

## Tree grammar

`scene.nodes` is a mapping of nodes. Every node can contain:

- `type`: `zone` or `object`;
- direct attribute values;
- `children`: another node mapping.

Keep names concrete and short. The generated prompt should be compact enough for Higgsfield's prompt LLM to understand without reading presentation metadata.

Example object:

```yaml
reading_lamp:
  type: object
  silhouette: "<HIGGSFIELD_FILL: slim fixture supporting the room's material language>"
  placement: "On the left table, 0.45 m from the sofa arm"
  light_behavior: "<HIGGSFIELD_FILL: warm diffused pool subordinate to daylight>"
  children: {}
```

## Locking decisions

Write a concrete value for:

- user-specified requirements;
- root art direction, palette, architecture, lighting, camera, and circulation;
- major spatial relationships;
- product presence and identity;
- details required for continuity across future shots.

Use `<HIGGSFIELD_FILL>` for secondary decor, ornamental motifs, subtle material variation, and other details that can vary while preserving the design grammar.

## Density and decor

The template defaults to a lived-in, styled room. Include visibly layered throw pillows and a draped or folded throw blanket on seating, one or two credible plants with appropriate containers, one restrained floral or flowering-branch arrangement, deliberate small decor, and one or more visible auxiliary table, floor, or wall lights. Keep these subordinate to the main architecture and lighting, and preserve circulation. A scene brief may explicitly replace or remove these defaults.

## Hero product

When the user supplies product reference images:

1. Add `nodes.hero_product`.
2. Do not describe the product's appearance or enumerate its materials, pattern, color, or hardware. The compiler requires exact consistency with the attached reference.
3. Use only scene-specific attributes such as placement, open/closed state, required framing, visibility, and functional constraints.
4. Unless the user explicitly requests otherwise, extract no design information from other objects or the original scene in the reference.
5. Do not put media IDs in the scene or prompt. Upload them and pass them separately through the generation API.

Example:

```yaml
hero_product:
  type: object
  presence: "One clearly recognizable hero product integrated into the scene"
  placement: "Primary focal zone; recognizable but allowed to be partially occluded"
  contact: "<HIGGSFIELD_FILL: credible floor or wall contact, shadows, and reflections>"
  children: {}
```

## Style guide

Use a compact, keyword-led note that gives Higgsfield clear design direction while leaving room for its prompt LLM to resolve details. Use four to six labeled lines, such as:

```text
Composition: elevated three-quarter; architectural editorial; legible hierarchy
Interior: quiet-luxury European; restrained Art Deco
Palette: 60% warm ivory; 25% deep petrol; 10% smoked oak; 5% brass
Lighting: soft side daylight; concealed cove; no curtain backlight
Density: purposeful restraint; inhabited; clear circulation
Product: dense matte blackout; uninterrupted overlap; zero transmission
```

Use two to five precise professional terms per dimension. Do not write a continuous paragraph or restate every YAML field. The compiler allows at most eight labeled lines and 180 characters per line.

The palette must include at least two visibly different hue families, not only variations within one family. Include one `Palette:` line with a percentage for every color; percentages must total 100%. A useful default hierarchy is a dominant color, a clearly contrasting secondary color, and small accents.

## Prompt compiler

Compile with:

```text
pwsh scripts/run_scene_spec.ps1 compile scenes/<slug>/scene.yaml \
  --style-guide scenes/<slug>/style-guide.txt \
  --out scenes/<slug>/prompts/reference-v1.txt
```

The default hard limit is 100 lines. The compiler:

- serializes only `scene`;
- rejects a top-level `generation` block;
- rejects obsolete `status/value/guidance` fields;
- rejects API fields inside `scene`;
- rejects unresolved `{{...}}` template values;
- requires the six fixed constraints;
- requires at least one OPEN placeholder.
- requires a `Palette:` line with at least two percentages totaling 100%.

If the prompt exceeds 100 lines, shorten the tree, the style guide, or filenames. Do not restore the removed control wrapper.

## Generation routing

### No product media

- Model: `soul_location`
- Count: `1`
- Prompt: the compiled scene prompt

### Product media supplied

- Model: `nano_banana_pro`
- Resolution: `2k`
- Reference role: `image_references`
- Media: upload the supplied product reference and pass its media ID in the API call
- Count: `1`

If a model rejects the request or the service fails, report it. One repair generation is allowed only for a rendered result that misses hard constraints. A provider-side failure without output does not consume another automatic retry unless the user authorizes one.

## Review

Check:

- one seamless image;
- readable wall planes, furniture footprint, floor contacts, and circulation;
- ceiling design and fixtures visible;
- no people, portraits, or identifiable faces;
- window exteriors are bright daytime;
- no dead zones or obvious repeated props;
- default decor coverage is visible: seating soft goods, auxiliary light, plants, and florals, unless the brief overrides them;
- no text, YAML, labels, or watermark;
- product present and recognizable when required.

## Persistence and reuse

Keep `scene.yaml`, `style-guide.txt`, prompts, references, outputs, and generation records under `scenes/<slug>/`. The generation record stores API parameters and media IDs. Reuse reads the YAML and attaches the approved scene image. Reuse does not regenerate the environment or create video unless separately requested.
