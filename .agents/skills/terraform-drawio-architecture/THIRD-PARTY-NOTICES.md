# Third-Party Notices

The code and documentation in this skill are licensed under the Apache
License, Version 2.0 (see `LICENSE`). The bundled icon data described below
is **not** covered by that grant and remains subject to the terms of its
respective owners.

## Scope of bundled third-party material

All bundled icon data lives in `assets/icon-styles.json` and is obtained
from the draw.io source repository (https://github.com/jgraph/drawio) by
the scripts in `maintenance/`:

- `sidebar_images`: SVG icons that draw.io embeds in its sidebar sources
  (`js/diagramly/sidebar/Sidebar-*.js`), copied verbatim by
  `maintenance/sync_sidebar_icons.py`.
- `stencil_svgs`: pre-rendered SVGs for the skill's exporter, produced by
  `maintenance/render_stencils.py`. The AWS and GCP entries are SVG
  renderings of draw.io stencil definitions (`stencils/*.xml`); the Azure
  entries are verbatim copies of the SVG files bundled in the draw.io
  repository (`img/lib/azure2/`), which Microsoft originally provides.
- `stencils` / `aliases`: shape names and library paths only (no image
  data).
- `assets/style-tokens.json`: color values matching the draw.io
  cloud-provider palettes, kept in sync by `maintenance/sync_upstream.py`.

## draw.io (diagrams.net)

draw.io is jointly owned and developed by draw.io Ltd and draw.io AG. Its
source repository licenses the source code under the Apache License,
Version 2.0, and provides the icon sets, stencil libraries, and diagram
templates under the following terms (quoted verbatim from the
repository's README.md, verified 2026-08-20), which are passed on
unchanged and apply to the icon data bundled in this skill:

> The icon sets and stencil libraries included in this software, and any
> derivatives thereof (including conversions to other formats, traced
> reproductions, substantially similar visual representations, or
> AI-generated images created using these icons as reference or training
> input), may not be used as software assets in, distributed for use with,
> or incorporated into Atlassian products or products distributed through
> the Atlassian marketplace or plugin ecosystem, without explicit written
> permission.
>
> This restriction does not apply to end-user diagram output (such as
> exported images or documents) created using this software.

## Cloud provider icons and trademarks

The bundled icon data visually represents product icons owned by the
companies below. This skill bundles that data solely so that generated
architecture diagrams can identify the corresponding cloud services — the
purpose those companies' icon terms are directed at. Each provider's terms
are linked below; if you redistribute this skill or its icon data,
verifying that your distribution complies with those terms is your
responsibility. No trademark rights are granted (see also Section 6 of the
Apache License, Version 2.0). Keep these notices intact when
redistributing.

- **Google Cloud**: product icons are provided by Google for use in
  architecture diagrams. https://cloud.google.com/icons
- **Amazon Web Services**: AWS Architecture Icons are provided by AWS for
  building architecture diagrams; standalone redistribution or resale of
  the icons is not permitted. https://aws.amazon.com/architecture/icons/
- **Microsoft Azure**: Microsoft permits use of the Azure architecture
  icons in architecture diagrams, training materials, and documentation,
  and reserves all other rights.
  https://learn.microsoft.com/azure/architecture/icons/

AWS, Amazon Web Services, Microsoft, Azure, Google, and Google Cloud are
trademarks of their respective owners. The "drawio" in this skill's name
refers to compatibility with the draw.io file format. This skill is not
affiliated with or endorsed by draw.io Ltd, draw.io AG, Amazon, Microsoft,
or Google.

## Removing bundled icon data

The skill's code works independently of the bundled icon data: services
without an icon are drawn as plain labelled boxes. If your use case cannot
accept the terms above, delete the `sidebar_images` and `stencil_svgs`
sections from `assets/icon-styles.json` and either work with the plain-box
fallback, harvest icons you have rights to use with
`scripts/icon_catalog.py --harvest`, or re-fetch the upstream material
with the `maintenance/` scripts — in which case you become the direct
recipient of the draw.io and provider terms above.
