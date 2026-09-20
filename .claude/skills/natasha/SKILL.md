---
name: natasha
description: 为 Natasha Denona 眼影盘创建产品页：下载官网图片、分析图片选取开盒图/色板、按砖块排列切割15片色板、转换 webp、生成含双语色号介绍的完整 README、更新品牌和根目录索引。
user-invocable: true
---

为 Natasha Denona 眼影盘创建完整产品页。

## 步骤

1. **抓取产品页** — 用 WebFetch 获取官网产品 URL，提取：完整色号列表（编号、名称、代码、质地、颜色描述）、产品简介、价格规格、质地说明、认证信息、上色建议。

2. **下载图片** — curl 下载官网产品页全部图片，命名为 `img_1.png`、`img_2.png` 等。查看每张图片，确认：
   - **开盒图**（id）：产品正面展开照，显示所有色号和名称
   - **色板**（icons）：Natasha Denona 经典药片形砖块排列涂抹色板
   - **其他**：手臂试色（arm_swatches）、质地说明（formula_guide）、眼妆分区（eye_diagram）等

3. **分析色板图布局** — 色板图为 **5行×3列砖块排列**，总15片。排列规律：每砖块行对应调色盘的一列（palette column），即：
   - 砖块行1 → 调色盘第1列（色号1、6、11）
   - 砖块行2 → 调色盘第2列（色号2、7、12）
   - 砖块行3 → 调色盘第3列（色号3、8、13）
   - 砖块行4 → 调色盘第4列（色号4、9、14）
   - 砖块行5 → 调色盘第5列（色号5、10、15）

   用 Python/numpy 分析图片内容区域边界（检测非白像素范围），确定 x0/x1/y0/y1，均分为 3列×5行。

4. **切割色板** — Python PIL 按坐标切割15片，文件名用官方编号命名：`01_ShadeName.png`，保存至 `slices/` 目录。

5. **转换图片格式** — 开盒图转为 `id.webp`，其余有用图片转为相应 `.webp`（quality=90）。删除临时 `img_*.png`。

6. **生成 README** — 参考格式：`docs/viseart/small-12-ved06-dawn-edit/README.md`。内容包含：
   - 产品标题、开盒图、品牌简介、价格规格、认证
   - 质地说明表（代码→质地→特点）+ 上色建议
   - formula_guide / arm_swatches / eye_diagram 图片（如有）
   - 色号总览表（编号、名称、代码、质地、颜色描述）
   - 每个色号：英文描述 + 色板切片图 + 用途建议 + 中文翻译和用途

7. **更新品牌 README** — 在 `docs/natasha/README.md` 加入新盘的 `[x]` 链接。

8. **更新根 README** — 确认 `docs/README.md` 包含 Natasha Denona 品牌链接。

## 目录结构

```
docs/natasha/<palette-dir>/
├── README.md
├── id.webp               ← 开盒图
├── arm_swatches.webp     ← 手臂试色（如有）
├── formula_guide.webp    ← 质地说明（如有）
├── eye_diagram.webp      ← 眼妆分区（如有）
└── slices/
    ├── 01_ShadeName.png
    ├── 02_ShadeName.png
    └── ...
```

## 命名规范

调色盘目录名格式：`<色数>-<英文名称小写连字符>`，例如：`tan-15`。
