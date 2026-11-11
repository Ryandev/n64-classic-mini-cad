# Credits and third-party models

None of the third-party models below are in this repository. Their STEP files are git-ignored
(`lib/step/*.step`), and you download them yourself to run the reference checks.

| Model | Author / owner | Source | Terms | Used for |
|---|---|---|---|---|
| Nintendo 64 console (SolidWorks, 2014, `nintendo-64-1.snapshot.1.zip`) | Bruno Amaral (credited by other projects that used this model; to confirm on the GrabCAD page) | [grabcad.com/library/nintendo-64-console-1](https://grabcad.com/library/nintendo-64-console-1) | GrabCAD Community: personal use; other use needs the author's agreement | Reference shape for the 50% shell: outlines, scan profiles and plaque/label outlines in `lib/part/shared/`, and the `SH_OUTSIDE` fidelity check |
| Radxa X4 V1.11 3D STP (`radxa_x4_v1.11_3d_20241120.stp`) | Radxa Computer (Shenzhen) Co., Ltd. | Official: [dl.radxa.com/x/x4/radxa_x4_3d_pcba.zip](https://dl.radxa.com/x/x4/radxa_x4_3d_pcba.zip) (also mirrored at [grabcad.com/library/radxa-x4-1](https://grabcad.com/library/radxa-x4-1)) | Not stated for the model (Radxa's CC BY 4.0 covers their documentation text only) | Board fit, connector positions and clearance checks |
| Radxa X4 heatsink (`radxa_heatsink_for_x4_3d.stp`) | Radxa Computer (Shenzhen) Co., Ltd. | Official: [dl.radxa.com/accessories/heatsink-for-x4/radxa_heatsink_for_x4_3d.zip](https://dl.radxa.com/accessories/heatsink-for-x4/radxa_heatsink_for_x4_3d.zip) ([product page](https://docs.radxa.com/x/x4/accessories/heatsink-for-x4)) | Not stated | Heatsink fit; `variant/radxa_heatsink.py` trims it to the SoC fin block |
| TE Connectivity 292303-7 USB-A | TE Connectivity, via KiCad's 3D library (`Connector_USB.3dshapes/USB_A_TE_292303-7_Horizontal.step`) | [KiCad packages3D](https://gitlab.com/kicad/libraries/kicad-packages3D) | CC-BY-SA-4.0 with KiCad's library exception | Front USB-A port fit |

The engraved plaque lettering uses DejaVu Sans Bold (`lib/part/shared/fonts/`, licence alongside).
