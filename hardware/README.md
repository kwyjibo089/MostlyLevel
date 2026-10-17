# Hardware

KiCad project for the MostlyLevel PCB (revision A). Open `mostlylevel.kicad_pro` in KiCad.

| Path | Contents |
| --- | --- |
| `mostlylevel.kicad_sch`, `mostlylevel.kicad_pcb` | Schematic and board layout |
| `mostlylevel.pretty/` | Project footprints |
| `mostlylevel_schematic.pdf`, `mostlylevel.png` | Exported schematic and board image |
| `bom/` | Bill of materials for JLCPCB |
| `fab/revA/` | Gerbers, drill files, BOM, and placement (CPL) for fabrication, plus the Gerbers as one zip for upload |
| `review/` | Renders and exports for design review |
| `routing/` | DRC reports of each routing pass (`drc1.json` … `drc12.json`, latest last), copper layer drawings (`fcu.svg`, `bcu.svg`), and the board before the reroute (`mostlylevel_before_reroute.kicad_pcb`) |
| `vendor/` | Placement and routing drawings; vendor downloads for the display board are kept locally, not in git |
