# CLAUDE.md — AI 适配指南

本文件写给即将接手本仓库的 AI 代理(如 Claude Code)。目标:让 AI 无需追问即可理解项目语义,并把"E1003 智能屏展示"平移到**任意新场景**(新 UI、新实体、新交互)。

## 1. 项目是什么

ESPHome 固件项目,跑在 reTerminal E1003 墨水屏(1872×1404,IT8951,16 级灰度)+ XIAO ESP32-S3 上:

- **静态 UI** = 设计稿 PNG 转成的位图(4bpp PackBits RLE)
- **动态部分** = 少量数值叠加(时钟 / SHT4x 温湿度 / HA 灯光亮度),带脏标记局部刷新
- **交互** = GT911 触摸热区 → 蜂鸣反馈 + 调用 HA 服务

## 2. 运行时数据流

```
设计稿 original.png
  → tools/png_to_h.py(缩放 1872×1404、转 16 级灰度、WHITE_CLIP、PackBits RLE)
  → assets/dashboard_static_v4.h(编译期 include)
  → yaml display(it8951).lambda 解码位图
      ├ 首次:GC16 全屏刷 = 静态图 + draw_clock / draw_environment / draw_light / draw_last_update
      └ 之后:仅当 ui_time_dirty / ui_env_dirty / ui_light_dirty 置位时,走 DU 局部刷新
触摸 → touchscreen(gt911).on_touch → x_ui = 1872 - touch.x(视觉坐标)→ 匹配 if 热区
      → 蜂鸣(50% 亮度 80ms)→ homeassistant.service 调用
时间 → PCF8563 RTC(update_interval: never),由 homeassistant time 平台 on_time_sync 写入
```

## 3. 关键文件职责

| 文件 | 职责 | AI 改新场景时关注点 |
|------|------|---------------------|
| `*.yaml` | 唯一业务代码:硬件、sensor、touch、display lambda | 绝大多数改动都在这 |
| `assets/dashboard_static_v4.h` | 静态位图(PackBits RLE,由 `png_to_h.py` 生成) | 换 UI 就重生成它,勿手改 |
| `tools/png_to_h.py` | PNG → .h;`TARGET_WIDTH/HEIGHT`、`WHITE_CLIP` 可调 | 换图/换分辨率时改 |
| `secrets.example.yaml` | 密钥模板 | 新环境复制为 `secrets.yaml` |
| `run_esphome.bat` | Windows 干净 PATH 启动 ESPHome `run/main/compile` 子命令 | 跨平台可绕过 |

## 4. substitutions 目录(改新场景基本只动这里)

| 变量 | 含义 | 新场景怎么改 |
|------|------|--------------|
| `device_name` / `friendly_name` | ESPHome 设备名 / HA 显示名 | 换新设备名 |
| `ha_light_entity` | 灯光卡绑定的 HA 灯实体 | 换成目标灯实体,或整卡删除 |
| `reachy_*` | Reachy 机器人控制区:服务名 $(`reachy_service`)与各按钮话术 | 换成你自己的 HA 服务/话术;不需要交互式服务可整体删除对应 `touchscreen` 分支 |

## 5. 适配新场景 checklist

### A. 换显示内容
1. 准备新场景设计稿(建议 4:3 或由脚本等比缩放);
2. `python tools/png_to_h.py <你的图> assets/dashboard_static_v4.h`(留意 `WHITE_CLIP` 与输出名);
3. 若目标显示模式下 16 级灰度 / 全程 GC16 不合适,调 `display` 的 `grayscale` / `dithering` / `full_update_every`;
4. 新增动态叠加区:仿照 `draw_clock` 写 `draw_xxx`,并接好"数据变化 → 置脏 → DU 局部更新"三件套(看第 6 节)。

### B. 换触摸交互
- 在 `touchscreen.on_touch` 中仿照现有 `if` 分支增加/删减热区;坐标为**视觉坐标**(已做 `x_ui = 1872 - touch.x`);
- 把 `homeassistant.service` 换成目标服务与参数;不需要蜂鸣就把 `light.turn_on`(buzzer)段删除。

### C. 换数据源
- 更多 HA 实体:`sensor` / `text_sensor` 用 `platform: homeassistant` 加,`internal: true` 即可;
- 叠加进 UI:在 lambda 里新增 `draw_xxx`,在对应 `on_value` 里置对应脏标记。

### D. 移植/换硬件
- 换主控:改 `esp32` 的 `board`、`psram`;换屏:改 `display` 的 `model`、`spi` 引脚、`transform`、`png_to_h.py` 的 `TARGET_*`;
- 字体:当前硬编码 Windows 路径 `C:/Windows/Fonts/arial.ttf` / `arialbd.ttf`,跨平台必须换成仓库内字体文件或 `gfonts` 引用;
- 触摸坐标镜像规则(`1872 - x`)随分辨率变化,换屏务必重算热区。

### E. 构建与烧录
```bash
run_esphome.bat compile  esphome-reterminal-e1003-workspace-v4.yaml   # 验证编译
run_esphome.bat run       esphome-reterminal-e1003-workspace-v4.yaml   # 串口烧录 + 看日志
# 生成 API 加密密钥(填到 secrets.yaml):
#   python -c "import secrets,base64;print(base64.b64encode(secrets.token_bytes(32)).decode())"
```

## 6. 常见坑(最容易改错的地方)

- **触摸 X 镜像**:原始 `touch.x` 与视觉相反,热区一律在 `x = 1872 - touch.x` 之后比较;
- **脏标记三件套**:新增动态区域时必须同时准备 (1) 数值来源的 `on_value` 置脏 (2) `interval`/触发处发起 `it8951.update` (3) lambda 里 `draw_*` 消费并把脏位清零——漏了任一环数据不刷新;
- **DU vs GC16**:纯黑白的时钟/数字适合 DU 快刷;大面积灰度内容(如静态图)用 GC16,首次上电必须全刷;
- **`.esphome/` 缓存**:改了 yaml 之后旧校验缓存是常见"改了没生效"的来源,可删掉重建;
- **密钥**:`secrets.yaml` 不入库;AP 热点密码与 OTA 密码用新值;
- **版本**:ESPHome ≥ 2026.7.0(`substitutions` + IT8951 模式参数依赖新语法)。

## 7. 范围外(仓库不提供)

- Home Assistant 侧的 `script.reachy_cmd`(机器人控制脚本)由使用者自行定义;
- 设计稿制作、HA 集成安装、物理接线。