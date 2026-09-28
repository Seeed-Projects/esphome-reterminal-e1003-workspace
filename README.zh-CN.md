# E1003 电子墨水屏模板(可复用智能屏模板)

[English](README.md) | [简体中文](README.zh-CN.md)

基于 **reTerminal E1003 电子墨水屏** + **Seeed XIAO ESP32-S3** + **ESPHome / Home Assistant** 的可复用智能屏模板:
设计稿 PNG 直接转位图作为静态 UI,叠加少量动态数据(时钟、温湿度、HA 实体状态),触摸热区调用 HA 服务。

> 本仓库是**模板**而非成品。下一个场景的用法:把它交给 AI(如 Claude Code),或按 [CLAUDE.md](CLAUDE.md) 的适配清单逐步修改。

## 特性

- **静态 UI 由设计稿转位图**(4bpp PackBits RLE),不逐控件手绘
- **动态叠加 + 脏标记局部刷新**:首次 GC16 全屏刷新,之后按区域 DU 快速刷新,墨水屏成像友好、无鬼影堆叠
- **GT911 电容触摸**:热区任意配置,点击带蜂鸣反馈
- SHT4x 温湿度、PCF8563 RTC(HA 授时)
- 所有业务可变点集中在 yaml 顶部 `substitutions`,无散落硬编码

## 项目结构

```
esphome-reterminal-e1003-workspace/
├── esphome-reterminal-e1003-workspace-v4.yaml  # 主配置:显示 / 触摸 / 刷新逻辑 / substitutions
├── CLAUDE.md                                   # AI 适配指南(交给 AI 前必读)
├── README.md                                   # 英文版本文档
├── README.zh-CN.md                             # 本文件(简体中文)
├── secrets.example.yaml                        # 密钥模板(复制为 secrets.yaml 使用)
├── secrets.yaml                                # 本机真实密钥,已被 .gitignore 排除
├── run_esphome.bat                             # Windows 干净环境启动 ESPHome CLI
├── assets/
│   ├── original.png                            # 仪表盘设计稿
│   └── dashboard_static_v4.h                   # 转换后的静态位图头文件
├── tools/
│   └── png_to_h.py                             # PNG → C 头文件转换脚本
└── .esphome/                                   # 构建缓存(可删,不影响)
```

## 快速开始

```bash
pip install esphome pillow
cp secrets.example.yaml secrets.yaml    # 填入真实 WiFi / OTA / API 密钥
python tools/png_to_h.py assets/original.png assets/dashboard_static_v4.h
run_esphome.bat run esphome-reterminal-e1003-workspace-v4.yaml
```

设备上电连不上 WiFi 时自动进入 **E1003-Recovery** 热点(captive portal),接入后可完成 OTA;随后在 Home Assistant 的 ESPHome 插件中注册设备即可。

## 适配新场景(总览)

| 想改什么 | 改哪里 |
|----------|--------|
| 显示内容 / UI | 换设计稿 PNG → 重跑 `png_to_h.py` → 重新编译 |
| 动态数据 | `display` lambda 里的 `draw_*` 函数 + 对应的 `sensor` / `text_sensor` 数据源 |
| 触摸按钮与动作 | `touchscreen.on_touch` 里的 `if` 热区分支 |
| 控制的 HA 实体 / 机器人话术 | yaml 顶部 `substitutions` |
| 网络 / 密钥 | `secrets.yaml` |
| 硬件参数 / 移植 | 引脚、`display` model、字体路径(风险点见 CLAUDE.md) |

详细的自适应 checklist 见 **[CLAUDE.md](CLAUDE.md)**。

## 安全提示

`secrets.yaml` 含明文口令,**不入库**;`ap` 热点默认密码请按需修改。

## 许可证

基于 ESPHome 开源生态,可自由修改与分发。