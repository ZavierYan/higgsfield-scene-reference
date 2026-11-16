---
name: higgsfield-scene-reference
description: Create and reuse a YAML-defined Higgsfield scene reference for consistent room layout, furnishings, ceiling fixtures, and optional hero-product identity across shots.
---

# Higgsfield Scene Reference

Use this skill to turn a scene request into one reusable, spatially legible Higgsfield reference image. The YAML scene tree is the source of truth; the generated image is a rendering of that specification.

Read [references/scene-workflow.md](references/scene-workflow.md) completely before creating or reusing a scene. Start every new scene from [assets/scene-template.yaml](assets/scene-template.yaml).

## Core contract

- Produce one seamless main view per scene. Use `16:9` and a slightly elevated three-quarter perspective unless the user explicitly requests another framing.
- Show the room's two main wall planes, floor relationship, furniture footprint, and the complete upper ceiling region with visible light fixtures.
- Default to an inhabited, styled room: visibly include throw pillows and a throw blanket on seating, at least one credible plant, a restrained floral arrangement, small decor, and subordinate auxiliary lighting when compatible with the brief. Preserve clear circulation and let the user's scene override these defaults.
- Keep the root style, palette, architecture, lighting, camera, and spatial hierarchy decisive. Writing a concrete value locks it; writing `<HIGGSFIELD_FILL>` or `<HIGGSFIELD_FILL: short hint>` leaves it for Higgsfield's prompt LLM to resolve. Do not add status fields.
- Treat the furniture program as a design decision, not a template consequence. If the user has not specified it, keep layout and selection OPEN and let Higgsfield choose a functional, varied mix rather than defaulting to one sofa plus two chairs. When distinct scene concepts are requested, vary the primary furniture typology or arrangement as well as the art direction.
- Use at least two visibly distinct hue families, not merely different tints or shades of one color. The style guide must include percentage weights for every palette color that total 100%.
- Keep API configuration out of `scene.yaml`. Model, aspect ratio, resolution, candidate count, repair budget, and reference media IDs belong to the generation call.
- A user request to create the scene authorizes exactly one paid candidate. If a hard constraint fails, repair the prompt and generate once more. Stop after that second result.
- Treat a supplied hero product as a strict identity reference: require exact consistency with the attached product image. Do not restate its appearance in the YAML; use `hero_product` only for scene-specific placement, state, and constraints. Unless the user explicitly requests otherwise, extract no design information from other objects or the original scene in the reference.
- When product references are attached, use `nano_banana_pro` at `2k`. Without product references, use `soul_location`.
- Additional requirements from the current request must be merged into the YAML and prompt. They must not silently drop the fixed scene-reference constraints.

## Fixed visual constraints

1. Spatial relationships must be immediately readable.
2. The full ceiling design and its light fixtures must be visible.
3. Do not include people, human figures, portraits, portrait paintings, or identifiable faces.
4. Avoid dead, empty space; populate it with purposeful furniture, objects, or architectural detail while preserving a believable circulation path.
5. Any exterior seen through windows must be a bright, clear daytime scene. Avoid darkened, stormy, nocturnal, or ambiguous exterior views.
6. The rendered image must not display YAML, field names, placeholders, headings, captions, labels, watermarks, or readable text.

## Workflow

1. Extract the user's scene, style, product, framing, and extra constraints.
2. Fill the decisions that must stay stable with concise, concrete values. Mark the remaining visual details with a `<HIGGSFIELD_FILL>` placeholder. Keep an unspecified furniture program open instead of completing the template with a familiar seating group; add only a short inline hint when the design space is not obvious.
3. Write a keyword-led style guide with four to six labeled dimensions. Use two to five precise professional terms per dimension; do not write a long explanatory paragraph or restate every YAML field. Include one `Palette` line with explicit percentages, for example `60% warm ivory; 25% deep petrol; 10% smoked oak; 5% brass`.
4. Scaffold and validate the scene with the included script. On Windows, use the wrapper so it can locate a Python runtime with PyYAML:

   ```text
   pwsh scripts/run_scene_spec.ps1 scaffold scenes/<slug> --id <slug> --name "<scene name>"
   pwsh scripts/run_scene_spec.ps1 validate scenes/<slug>/scene.yaml
   pwsh scripts/run_scene_spec.ps1 compile scenes/<slug>/scene.yaml --style-guide scenes/<slug>/style-guide.txt --out scenes/<slug>/prompts/reference-v1.txt
   ```

   Outside Windows, run the same commands through a Python interpreter that has PyYAML. The compiler rejects prompts over 100 lines by default.

5. Upload local product references through Higgsfield before generation. Pass the returned media IDs, aspect ratio, resolution, model choice, candidate count, and repair budget directly to the API call; keep them out of `scene.yaml` and the compiled prompt.
6. Submit the compiled prompt to the selected Higgsfield image model. Render and inspect the result against the hard-constraint checklist before calling the task complete.
7. Save the actual prompt snapshot, generated asset, and generation metadata under the scene directory. Copy local product references into `refs/` when possible so the scene remains reproducible.

For a hard-constraint failure, change only the cause of the failure, preserve locked product and scene identity, increment the prompt/output version, and allow one repair generation. If the repair still fails, report the failed checks and stop.

## Reuse

For an existing scene, read `scene.yaml` and reuse its canonical reference image and, when needed, the product media IDs recorded in the latest generation metadata. Prepare the requested shot's framing, subject placement, lighting, and camera direction as a shot brief, attaching the scene image as a reference. `reuse` mode must not regenerate the environment or create a video unless the user separately asks for one.

Do not mutate an accepted scene in place when layout or product identity changes. Create a new version or a sibling scene folder and keep the prior version available for rollback.
