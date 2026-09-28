# E1003 E-Ink Display Template

[English](README.md) | [简体中文](README.zh-CN.md)

A reusable smart-display template powered by the **reTerminal E1003 e-paper panel** + **Seeed XIAO ESP32-S3** + **ESPHome / Home Assistant**:
the design PNG is baked into a bitmap as the static UI, a few dynamic values (clock, temperature/humidity, HA entity state) are overlaid on top, and touch hot zones invoke Home Assistant services.

> This repository is a **template**, not a finished product. To adapt it to a new scenario, hand it to an AI agent (e.g. Claude Code), or follow the adaptation checklist in [CLAUDE.md](CLAUDE.md).

## Features

- **Static UI rendered from a design bitmap** (4bpp PackBits RLE), no widget-by-widget hand drawing
- **Dynamic overlays with dirty-marked partial refresh**: full GC16 refresh on boot, per-region DU fast refresh afterwards — e-paper friendly, no ghosting stack-up
- **GT911 capacitive touch**: freely configurable hot zones, with buzzer feedback on tap
- SHT4x temperature/humidity, PCF8563 RTC (time-synced from Home Assistant)
- All scenario-specific values are centralized in the `substitutions` block at the top of the YAML — no scattered hardcoding

## Project structure

```
esphome-reterminal-e1003-workspace/
├── esphome-reterminal-e1003-workspace-v4.yaml  # main config: display / touch / refresh logic / substitutions
├── CLAUDE.md                                   # AI adaptation guide (read before handing to an AI)
├── README.md                                   # this file (English)
├── README.zh-CN.md                             # 中文版本
├── secrets.example.yaml                        # key template (copy to secrets.yaml)
├── secrets.yaml                                # local real secrets, excluded via .gitignore
├── run_esphome.bat                             # clean-env launcher for the ESPHome CLI on Windows
├── assets/
│   ├── original.png                            # dashboard design source
│   └── dashboard_static_v4.h                   # generated static bitmap header
├── tools/
│   └── png_to_h.py                             # PNG → C header converter
└── .esphome/                                   # build cache (safe to delete)
```

## Quick start

```bash
pip install esphome pillow
cp secrets.example.yaml secrets.yaml    # fill in your WiFi / OTA / API keys
python tools/png_to_h.py assets/original.png assets/dashboard_static_v4.h
run_esphome.bat run esphome-reterminal-e1003-workspace-v4.yaml
```

When the board cannot reach Wi-Fi it falls back to the **E1003-Recovery** access point (captive portal); onboard it via OTA, then register the device in the Home Assistant ESPHome integration.

## Adapting to a new scenario (overview)

| What to change | Where |
|----------------|-------|
| Display content / UI | Replace the design PNG → re-run `png_to_h.py` → rebuild |
| Dynamic data | `draw_*` functions in the `display` lambda + the corresponding `sensor` / `text_sensor` sources |
| Touch buttons / actions | `if` hot zones inside `touchscreen.on_touch` |
| Controlled HA entities / robot phrases | `substitutions` at the top of the YAML |
| Network / credentials | `secrets.yaml` |
| Hardware / porting | GPIO pins, `display` model, font paths (risk points in CLAUDE.md) |

See **[CLAUDE.md](CLAUDE.md)** for the full adaptation checklist.

## Security notes

`secrets.yaml` holds plaintext credentials and must **never be committed**. Change the `ap` fallback password as needed.

## License

Based on the ESPHome open-source ecosystem; free to modify and redistribute.