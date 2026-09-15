#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import deque
import html
import re
import unicodedata
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit
from typing import cast

from PIL import Image
from PIL import ImageDraw


SHADE_RE = re.compile(r"^(?:##\s+)?Shade\s+(\d+):\s+(.*?)\s+(?:-|—)\s+(.*)$")
USE_RE = re.compile(r"^Use:\s*(.*)$")


NAME_TRANSLATIONS = {
    "White": "纯白",
    "Lime": "青柠绿",
    "Kelly": "凯利绿",
    "Aqua": "水蓝绿",
    "Pink": "亮玫粉",
    "Orange": "亮橙",
    "Yellow": "亮黄",
    "Periwinkle": "长春花蓝",
    "Red": "霓虹红",
    "Raspberry": "树莓粉",
    "Grape": "葡萄紫",
    "Azure": "天青蓝",
    "Toffee": "太妃棕",
    "Hazelnut": "榛果棕",
    "Sienna": "赭石棕",
    "Sepia": "棕褐",
    "Pinot": "黑皮诺紫棕",
    "Beaujolais": "博若莱紫",
    "Curcumin": "姜黄橘",
    "Persimmon": "柿橘",
    "Myrtille": "蓝莓紫",
    "Minuit": "午夜蓝",
    "Fôret": "森林绿",
    "Olive": "橄榄绿",
    "Sylph": "海雾银玫",
    "Serenade": "轻吟粉",
    "Murmure": "低语玫瑰",
    "Mélusine": "美露曦涟",
    "Ethos": "气韵粉桃",
    "Luminary": "流光贝金",
    "Triton": "特里同",
    "Oceanic": "海潮蓝绿",
    "Glinting": "闪银光",
    "Siren": "海妖紫蓝",
    "Abyss": "深渊灰紫",
    "Brine": "盐海棕",
    "Beurre": "奶油黄",
    "Croissant": "可颂暖黄",
    "Bisque": "杏饼棕",
    "Saffron": "番红花黄",
    "Brioche": "奶油面包棕",
    "Cantaloup": "蜜瓜橘",
    "Cidre": "苹果酒棕",
    "Flame": "焰橘红",
    "Brûlée": "焦糖炙棕",
    "Nutmeg": "肉豆蔻棕",
    "Mocha": "摩卡深棕",
    "Brick": "砖红棕",
    "Salt": "盐白",
    "Sand": "沙色",
    "Seashell": "贝壳粉",
    "Lilac": "淡紫",
    "Shoreline": "海岸线棕",
    "Fog": "雾灰",
    "Sky": "天蓝",
    "Lupine": "羽扇豆紫",
    "Ghirardelli": "吉拉德利棕",
    "Elk": "麋鹿棕",
    "Bluebells": "风铃草蓝",
    "Iris": "鸢尾紫蓝",
}


DESCRIPTION_TRANSLATIONS = {
    "Bright white with a matte finish.": "明亮纯白色，哑光质地。",
    "Neon yellow green with a matte finish.": "霓虹黄绿色，哑光质地。",
    "Bright green with a matte finish.": "明亮绿色，哑光质地。",
    "Bright aqua with a matte finish.": "明亮水蓝绿色，哑光质地。",
    "Bright fuchsia pink with a matte finish.": "明亮洋红粉色，哑光质地。",
    "Primary orange with a matte finish.": "原色橙，哑光质地。",
    "Primary yellow with a matte finish.": "原色黄，哑光质地。",
    "Cyan blue with a matte finish.": "青蓝色，哑光质地。",
    "Neon red with a matte finish.": "霓虹红色，哑光质地。",
    "Bright raspberry with a matte finish.": "明亮树莓色，哑光质地。",
    "Bright magenta purple with a matte finish.": "明亮洋红紫色，哑光质地。",
    "Cerulean blue with a matte finish.": "天青蓝色，哑光质地。",
    "Warm light brown with a matte finish.": "暖调浅棕色，哑光质地。",
    "Deep taupe brown with a matte finish.": "深灰棕色，哑光质地。",
    "Muted rosy brown with a matte finish.": "柔和玫瑰棕色，哑光质地。",
    "Muted orange-brown with a matte finish.": "柔和橘棕色，哑光质地。",
    "Deep rosy plum with a matte finish.": "深玫瑰李子色，哑光质地。",
    "Eggplant purple with a matte finish.": "茄紫色，哑光质地。",
    "Muted yellow-orange with a matte finish.": "柔和黄橘色，哑光质地。",
    "Deep orange with a matte finish.": "深橘色，哑光质地。",
    "Blue purple with a matte finish.": "蓝紫色，哑光质地。",
    "Deep navy blue with a matte finish.": "深海军蓝色，哑光质地。",
    "Forest green with a matte finish.": "森林绿色，哑光质地。",
    "Olive green with a matte finish.": "橄榄绿色，哑光质地。",
    "Pale vanilla nude with a matte finish.": "香草米白裸色，哑光质地。",
    "Nude rose-brown with a matte finish.": "裸玫瑰棕色，哑光质地。",
    "Sandy taupe with a matte finish.": "沙感灰棕色，哑光质地。",
    "Medium-deep cool taupe brown with a matte finish.": "中深调冷灰棕色，哑光质地。",
    "Deep, cool-toned shale brown with a matte finish": "深冷调页岩棕色，哑光质地。",
    "Bright bubblegum pink with a matte finish.": "明亮泡泡糖粉色，哑光质地。",
    "Midtone, magenta-aubergine with a matte finish.": "中调洋红茄紫色，哑光质地。",
    "Deep, charcoal blue-grey with a matte finish.": "深炭蓝灰色，哑光质地。",
    "Zenith blue with a matte finish.": "天穹蓝色，哑光质地。",
    "Dusty midtone plum-grey with a matte finish.": "雾感中调李子灰色，哑光质地。",
    "Midtoned, cool-toned dove grey with a matte finish.": "中调冷鸽灰色，哑光质地。",
    "Dark charcoal grey-black with a matte finish.": "深炭灰黑色，哑光质地。",
    "Iced silver rosé with a shimmer finish.": "冰银玫瑰色，闪光质地。",
    "Cool-toned light beige with a matte finish.": "冷调浅米色，哑光质地。",
    "Mid-tone clay rose with a matte finish.": "中调陶土玫瑰色，哑光质地。",
    "Patinaed silver-green with a metallic finish.": "铜锈银绿色，金属质地。",
    "Mid-tone, chestnut-blushed brown with a matte finish.": "中调栗棕色，带红晕，哑光质地。",
    "Nude mauve with blue duochromatic flecks.": "裸紫红色，带蓝色双偏光闪片。",
    "Corraline-blushed sienna with a duochromatic finish.": "珊瑚红晕赭色，双偏光质地。",
    "Basalt silver brown with a duochromatic finish.": "玄武岩银棕色，双偏光质地。",
    "Light, cool-toned nude slate with a matte finish.": "浅冷调裸灰蓝石色，哑光质地。",
    "Antiqued gold-green with a shimmer finish.": "古金绿，闪光质地。",
    "Muted kelp green with a matte finish.": "柔和海带绿，哑光质地。",
    "Espresso-bitter brown with a matte finish.": "浓缩苦咖棕，哑光质地。",
    "Champagne rose with a metallic finish.": "香槟玫瑰色，金属光泽。",
    "Soft, mid-tone neutral pink with a matte finish.": "柔和中调中性粉色，哑光质地。",
    "Mid-tone nude rose with a matte finish.": "中调裸玫瑰色，哑光质地。",
    "Midtone sandy nude with blue-green duochromatic flecks.": "中调沙感裸色，带蓝绿双偏光闪片。",
    "Light, muted neutral pink-peach with a matte finish": "浅柔和中性粉桃色，哑光质地。",
    "Nude quartz with a metallic finish.": "裸色石英光感，金属质地。",
    "Second-skin nude, topper with silver duochromatic flecks.": "贴肤裸色叠擦色，带银色双偏光闪片。",
    "Rich navy blue-green with blue duochromatic flecks.": "浓郁海军蓝绿色，带蓝色双偏光闪片。",
    "Nude silver with a metallic finish.": "裸银色，金属光泽。",
    "Violet-blue with turquoise duochromatic flecks.": "紫蓝色，带绿松石双偏光闪片。",
    "Mid-tone greige-purple with a matte finish.": "中调灰米紫色，哑光质地。",
    "Bitter brown-quartz with copper reflectivity and a metallic finish.": "苦棕石英色，带铜色反光，金属质地。",
    "Buttery yellow with warm undertones and a matte finish.": "奶油黄，带暖调底色，哑光质地。",
    "Medium yellow with warm undertones and a matte finish.": "中调暖黄，哑光质地。",
    "Soft brown with warm, yellow-orange undertones and a matte finish.": "柔和棕色，带暖调黄橘底色，哑光质地。",
    "Bright yellow with a satin finish.": "明亮黄色，缎光质地。",
    "Soft brown with warm, yellowish undertones and a matte finish.": "柔和棕色，带偏黄暖调底色，哑光质地。",
    "Tangerine orange with warm, yellow undertones and a matte finish.": "橘橙色，带暖调黄色底色，哑光质地。",
    "Medium brown with warm, yellow undertones and a matte finish.": "中调棕色，带暖调黄色底色，哑光质地。",
    "Burnt orange with warm, red undertones and a matte finish.": "焦橘色，带暖调红色底色，哑光质地。",
    "Medium-dark taupe-brown with warm undertones and a matte finish.": "中深调灰棕色，带暖调底色，哑光质地。",
    "Medium-dark brown with subtle, reddish undertones and a matte finish.": "中深调棕色，带细微红调底色，哑光质地。",
    "Dark brown with subtle, warm undertones and a matte finish.": "深棕色，带细微暖调底色，哑光质地。",
    "Deep muted red with warm undertones and a matte finish.": "深柔雾红色，带暖调底色，哑光质地。",
    "Pale bone matte finish.": "淡骨色，哑光质地。",
    "Cool light beige matte finish.": "冷调浅米色，哑光质地。",
    "Light pink matte finish.": "浅粉色，哑光质地。",
    "Light purple matte finish.": "浅紫色，哑光质地。",
    "Medium cool brown matte finish.": "中等冷调棕色，哑光质地。",
    "Light cool grey matte finish.": "浅冷调灰色，哑光质地。",
    "Light blue matte finish.": "浅蓝色，哑光质地。",
    "Dusty medium purple.": "柔和中紫色。",
    "Chocolate cool matte finish.": "冷调巧克力棕，哑光质地。",
    "Bitter brown matte finish.": "深苦棕，哑光质地。",
    "Deep fresh blue matte finish.": "深清爽蓝，哑光质地。",
    "Deep purple-blue matte finish.": "深紫蓝色，哑光质地。",
}


USE_TRANSLATIONS = {
    "The most versatile! This can be mixed with any of the other colors to make pastels, or blended in as a matte opaque color.": "这是一支用途最广的颜色。可与盘中任何颜色混合，调出粉彩效果，也可单独作为高遮盖哑光色使用。",
    "This is a tertiary color, as it’s a yellow-green, Mix with white to make pale lime, or with Clover to intensify the depth of the green. This color is also analogous to both blues and yellows.": "这是一支三次色，属于黄绿色。与白色混合可调出浅青柠色；与更深的绿色混合则可增强绿色深度。它也很适合与蓝色和黄色系搭配使用。",
    "This is a secondary color, mix with white to make pale green, with yellow to make a lighter green, or with blue to make Teal.": "这是一支二次色。与白色混合可调出浅绿色；与黄色混合可做出更轻亮的绿色；与蓝色混合则可得到蓝绿色。",
    "This is a tertiary color, it’s a blue-green. Mix with white to make anything from pastel teal to turquoise.": "这是一支三次色，属于蓝绿色。与白色混合后，可从粉彩蓝绿一路调到绿松石色。",
    "A tertiary color, mix with white to make anything from pastel to bubble gum pink, or use to brighten up blue and green eyes. This can also be used on cheeks, or mix with a blush that’s too light to intensify it. *WARNING* - In the US, this shade contains pigments that the FDA has not approved for use in the eye area.": "这是一支三次色。与白色混合可从粉彩粉一路调到泡泡糖粉；也适合用于提亮蓝色和绿色眼眸。还可作腮红使用，或与过浅的腮红混合增强颜色。 *WARNING* - In the US, this shade contains pigments that the FDA has not approved for use in the eye area.",
    "A secondary color, mix with white to make anything from a pale orange to pastel. Orange is amazing against blue eyes, or use analogous colors with it, like Red and Yellow. *WARNING* - In the US, this shade contains pigments that the FDA has not approved for use in the eye area.": "这是一支二次色。与白色混合可从浅橙调到粉彩橙。橙色尤其能衬托蓝色眼眸，也适合与红色、黄色等邻近色搭配。 *WARNING* - In the US, this shade contains pigments that the FDA has not approved for use in the eye area.",
    "Yellow is a primary color, which makes it ultra versatile. Mix with white to make anything from pastel to buttercup! You can also blend with orange to intensify the yellow, or blend with red to change the depth of the orange.": "黄色是原色，因此非常百搭。与白色混合可从粉彩黄调到奶油黄；也可与橙色混合增强黄色感，或与红色混合改变橙色的深浅层次。",
    "A tertiary color, Mix with white to range from pastel to sky blue, or use with analogous colors like purples or greens.": "这是一支三次色。与白色混合可从粉彩蓝调到天蓝色；也很适合与紫色或绿色等邻近色搭配使用。",
    "A primary color, Mix with white to make multiple shades of pink, or blend out to create purples, browns, oranges and more. *WARNING* - In the US, this shade contains pigments that the FDA has not approved for use in the eye area.": "这是一支原色。与白色混合可调出多种粉色；也可继续混色延展出紫色、棕色、橙色等更多变化。 *WARNING* - In the US, this shade contains pigments that the FDA has not approved for use in the eye area.",
    "This is a tertiary color, it is a red-violet. It’s fantastic against brown or hazel eyes to brighten, but is a super versatile color with almost every eye shade. *WARNING* - In the US, this shade contains pigments that the FDA has not approved for use in the eye area.": "这是一支三次色，属于红紫调。特别适合提亮棕色或榛色眼眸，同时对几乎所有眼色都很百搭。 *WARNING* - In the US, this shade contains pigments that the FDA has not approved for use in the eye area.",
    "This secondary color can be made into pastel simply by mixing with white. This is also super versatile for every eye color to intensify. *WARNING* - In the US, this shade contains pigments that the FDA has not approved for use in the eye area.": "这是一支二次色，与白色混合即可轻松调成粉彩效果。它也适合用于增强各种眼色的表现力。 *WARNING* - In the US, this shade contains pigments that the FDA has not approved for use in the eye area.",
    "This is a primary Blue, Mix with white to make a pastel blue, or use dramatically for anything you can think of. This can be used for liner, lid, crease - the sky's the limit. Blue is also a wonderful color to brighten Brown and Hazel eyes.": "这是一支原色蓝。与白色混合可调出粉彩蓝，也可直接高强度使用，发挥各种创意。可用于眼线、眼皮主色或眼窝加深，几乎没有使用边界。蓝色也很适合提亮棕色和榛色眼眸。",
    "All over base tone for all skin types, highlight for brow bone on medium to deep skin. Use as a mix-in with other brown tones and with greens to create different light variations of khaki.": "适合所有肤色作大面积打底色；中等至深肤色也可用于眉骨提亮。还可与其他棕色或绿色混合，调出不同深浅变化的卡其色。",
    "All over base tone for all skin types. Use as a midtone to add definition.": "适合所有肤色作大面积打底色，也可作为中间色调增加轮廓与层次。",
    "All over tone for all skin types. Use it as a liner to create depth and dimension.": "适合所有肤色作大面积铺色，也可作为眼线色使用，增强深度与立体感。",
    "All-over tone for all skin types. Use it as a liner to create depth and dimension.": "适合所有肤色作大面积铺色，也可作为眼线色使用，增强深度与立体感。",
    "This pale vanilla shade can be used as an all over lid colour or as a base tone beneath complementary shades. It can also be used to highlight the brow bone and inner corners of the eyes on light to medium complexions. Additionally, mix it with any of the other tones to brighten, lighten, and create over 12 new hues. Pair with shades ‘Slate’ and ‘Sandstone’ for a quick and easy cool-toned tantalizing taupe eye look. Apply with a brush for your desired level of intensity.": "可作全眼铺色，或作为互补色下方的打底色。浅至中等肤色可用于眉骨和眼头提亮。也可与盘中其他色调混合，提亮、调浅并延展出 12 种以上新色。与 `Slate`、`Sandstone` 搭配，可快速完成冷调迷人的灰棕眼妆。可用刷具按需叠加显色度。",
    "This nude rose-brown shade can be used to add subtle definition to contours of the face. It can also be used as a nude blush on light to medium complexions. Apply with a brush for your desired level of intensity.": "可用于面部轮廓的轻柔加深，也可在浅至中等肤色上作裸感腮红。可用刷具按需叠加显色度。",
    "This sandy taupe shade can be used to highlight and bring forth the contours of the face. Apply it under the brow bone or in the inner corners of the eyes on all complexions, or down the bridge of the nose and on the cheekbones on medium to deep complexions to add brightness to the face.": "可用于提亮并强化面部轮廓。适合所有肤色用于眉骨和眼头；中等至深肤色也可用于鼻梁和颧骨提亮，让面部更显明亮。",
    "This taupe brown shade can be used as an all-over lid colour for all complexions, focused in the socket and outer corners of the eyes for buildable intensity, or applied along the lash lines to add definition. Pair with shades ‘Drift’ and ‘Pewter’ for a cool-toned, neutral look. Apply with a brush for your desired level of intensity.": "适合所有肤色作全眼铺色，也可集中于眼窝和眼尾逐步加深，或沿睫毛根部勾勒轮廓。与 `Drift`、`Pewter` 搭配，可完成冷调中性色眼妆。可用刷具按需叠加显色度。",
    "This deep, cool-toned shale brown shade can be used as an all over lid colour for all complexions, focused in the socket and outer corners of the eyes for buildable intensity, or applied along the lash lines to add definition. Wear with shades ‘Mauvewood’ and ‘Sediment’ for the perfect, richly pigmented, sooty smokey eye. Apply with a brush for your desired level of intensity.": "适合所有肤色作全眼铺色，也可集中于眼窝和眼尾逐步加深，或沿睫毛根部勾勒轮廓。与 `Mauvewood`、`Sediment` 搭配，可打造浓郁烟灰感的完美烟熏眼妆。可用刷具按需叠加显色度。",
    "This bubblegum pink shade can be used as an all over lid colour, as a base tone beneath complementary shades, or anywhere you want to add brightness and vibrancy. Can also be worn as a blush shade on light complexions. Wear with shades ‘Saltsone’ and ‘Sandstone’’ for soft nude look with a regal rose twist! Apply with a brush for your desired level of intensity.": "可作全眼铺色、互补色下方的打底色，或用于任何需要提亮和增添活力的位置。浅肤色也可当腮红使用。与 `Saltsone`、`Sandstone` 搭配，可完成带高贵玫瑰感的柔和裸妆。可用刷具按需叠加显色度。",
    "This midtone magenta-aubergine shade can be used to add a pop of vibrancy or as a blush shade on all complexions. Blend with the shade ‘Shell’ for a beautiful, gradated look. Apply with a brush for your desired level of intensity.": "可用于增强妆容活力，也适合所有肤色当腮红使用。与 `Shell` 晕染，可呈现柔和渐层效果。可用刷具按需叠加显色度。",
    "This deep, charcoal blue-grey shadow can be used as an all-over lid colour for drama and intensity, or focused in the crease and outer corners of the eyes for a sensual smokey look. Can also be used along the upper and lower lashline as eyeliner or in the brows on dark brows shades. Pair with shades ‘Sediment’ and ‘Sandstone’ for a cool-toned, charcoal effect! Apply with a brush for your desired level of intensity.": "可作全眼铺色，打造戏剧感和高强度妆效；也可集中于眼窝和眼尾，塑造性感烟熏感。还可沿上下睫毛根部当眼线，或用于深色眉毛的眉部修饰。与 `Sediment`、`Sandstone` 搭配，可完成冷调炭灰效果。可用刷具按需叠加显色度。",
    "This zenith blue shade can be used to add a pop of cool-toned saturation to the face. Apply with a brush for your desired level of intensity.": "可用于为面部增加一抹冷调饱和度。可用刷具按需叠加显色度。",
    "This dusty, midtone plum-grey shade can be used to add subtle definition to contours of the face. Apply with a brush for your desired level of intensity.": "可用于面部轮廓的柔和加深，营造雾感层次。可用刷具按需叠加显色度。",
    "This midtone dove grey shade can be used as an all-over lid colour, in the crease and socket for buildable dimension, or beneath of any of the complementary shades in the palette for increased depth and saturation. Pair with shades ‘Saltstone’’ and ‘Sediment’ for the perfect sleek slate shadow look! Apply with a brush your desired level of intensity.": "可作全眼铺色，也可在眼窝和轮廓处逐步加深，或作为盘中互补色下方的打底色，增强深度与饱和度。与 `Saltstone`、`Sediment` 搭配，可完成利落的灰石调眼妆。可用刷具按需叠加显色度。",
    "This dark, charcoal grey-black shadow can be used as an all-over lid colour for drama and intensity, or focused in the crease and outer corners of the eyes for a sensual smokey look. Can also be used along the upper and lower lash line as eyeliner or in the brows on dark brows shades. Pair with shades ‘Drift’ and ‘Sandstone’ for a dramatic, smoldering effect! Apply with a brush for your desired level of intensity.": "可作全眼铺色，打造戏剧感与高强度妆效；也可集中于眼窝和眼尾，塑造性感烟熏感。还可沿上下睫毛根部当眼线，或用于深色眉毛的眉部修饰。与 `Drift`、`Sandstone` 搭配，可完成张力十足的深邃妆效。可用刷具按需叠加显色度。",
    "This iced silver rosé shade can be used as an all-over lid color or along the high points of the face as a highlighter on all complexions. For a brightening, eye-catching effect, apply to the inner corners of the eyes, or layer over complementary hues for extra dimension. Apply with a brush for your desired level of intensity. This shade can also be blended with gloss or balm for a dewy, multi-use glow. Pair with shades ‘Harpia’ and ‘Echo’ for a tide-swept nude wash of creamy oyster and pearl.": "可作全眼铺色，也可用于面部高点提亮，适合所有肤色。想要更明亮吸睛的效果，可用于眼头，或叠加在互补色上增强层次。可用刷具按需叠加显色度。也可与唇蜜或润唇膏混合，做出水润、多用途的光泽感。与 `Harpia`、`Echo` 搭配，可呈现被潮汐洗过般的奶感牡蛎与珍珠裸色妆效。",
    "This cool-toned light beige shade can be used as an all-over lid colour or as a base tone beneath complementary hues. It can also be used to highlight the brow bone and inner corners of the eyes, or as a transitional shade in the socket of the eye. Apply with a brush for your desired level of intensity. Use as a base tone beneath shades ‘Lûlène ’ and ’Tritonia’ for a burnished rose look steeped in tidal shimmer.": "可作全眼铺色，或作为互补色下方的打底色。也可用于眉骨和眼头提亮，或作为眼窝位置的过渡色。可用刷具按需叠加显色度。与 `Lûlène`、`Tritonia` 叠擦，可打造带潮汐微光的焦玫瑰妆效。",
    "This mid-tone clay rose shade can be used as an all-over lid colour, beneath complementary tones for increased depth and saturation, or as a transitional tone in the crease and socket. Apply with a brush for your desired level of intensity. Pair with ‘Echo’ and ‘Tritonia’ for an iridescent tide of muted mauve and soft sand.": "可作全眼铺色，或作为互补色下方的打底加深色，也可用于眼窝和轮廓位置做过渡。可用刷具按需叠加显色度。搭配 `Echo` 与 `Tritonia`，可呈现带虹彩感的柔雾豆沙与细沙调妆感。",
    "Use this patinaed silver-green shade as an all-over lid colour, layered over complementary hues, or in the center of the lid and corners of the eyes for an icy green gleam. Use with a mixing medium for a foiled effect. Apply with a brush for your desired level of intensity. Wear with shades ‘Voile’ and ‘Lûlène’ for a sea-lit cascade of crystalline shimmer.": "可作全眼铺色，叠加在互补色之上，或用于眼皮中央和眼角，营造冰感绿光。搭配调和液可获得更强烈的箔光效果。可用刷具按需叠加显色度。与 `Voile`、`Lûlène` 搭配，可呈现海光照亮般的晶莹闪泽。",
    "Use this mid-tone, chestnut-blushed brown shade as an all-over lid colour on all complexions, in the crease as a transitional shade, or to build out depth and dimension in the outer corners of the eyes. Can be used as a soft eyeliner on all skin tones, in the brows and hairline, or as a subtle contour shade on light to medium complexions. Apply with a brush for your desired level of intensity. Blend with shades ‘Harpia’ and ‘Tideborn’ for a tide-washed trio of shell, sand, and stone.": "可作全眼铺色，适合所有肤色；也可用于眼窝作过渡色，或在眼尾叠加出深度与立体感。适合所有肤色当柔和眼线，也可用于眉部和发际线；浅至中等肤色还可作为自然修容。可用刷具按需叠加显色度。与 `Harpia`、`Tideborn` 搭配，可组成贝壳、细沙与礁石般的潮汐三重奏。",
    "This nude rose duochromatic shade can be worn alone for a wash of brilliant reflectivity or layered over complementary tones to accentuate its duochromatic dimension. For a high-shine, foiled effect, use with a mixing medium. It can also be mixed with a nude gloss for a wet, prismatic look. Apply with a brush for your desired level of intensity. Pair with “Echo” and “Ciel Figé” for a moonlit mutichrome look that shimmers like the midnight sea.": "可单独使用，呈现明亮反光感；也可叠加在互补色之上，强化双偏光层次。搭配调和液可做出更强烈的箔光效果，也可与裸色唇蜜混合，营造湿润棱彩感。可用刷具按需叠加显色度。与 `Echo`、`Ciel Figé` 搭配，可做出月光下般的多变光泽。",
    "Use this coralline-blushed sienna shade as an all-over lid color, in the center of the lid for spell-binding luminosity, or over top similar shades for an incandescent sheen. Use with a mixing medium for a foiled effect. Apply with a brush for your desired level of intensity. Blend with shade ‘Voile’ and ‘Harpia’ for a nude moonlit pool of prismatic perfection.": "可作全眼铺色，或用于眼皮中央打造吸睛光感，也可叠加在相近色之上做出炽亮光泽。搭配调和液可获得箔光效果。可用刷具按需叠加显色度。与 `Voile`、`Harpia` 搭配，可做出如月光映照的裸色棱彩光池。",
    "Use this duochromatic basalt silver brown shade as an all-over lid colour for sea-glass finish, or layered over complementary tones for a wet, tide-lit pop. Use with a mixing medium for a foiled effect. Apply with a brush for your desired level of intensity. Wear with shades ‘Tritonia’ and ‘Empyrée’ for an opaline finish that glints like starlight on water.": "可作全眼铺色，呈现海玻璃般的质感；也可叠加在互补色之上，做出湿润、被潮汐照亮的亮点。搭配调和液可获得箔光效果。可用刷具按需叠加显色度。与 `Tritonia`、`Empyrée` 搭配，可完成如水面星光般闪烁的蛋白石光泽。",
    "This light, cool-toned nude slate shade can be used as an all-over lid colour, a transitional shade to build out the crease and socket, a soft liner, or as a base tone beneath complementary shades for increased depth and saturation. Apply with a brush for your desired level of intensity.": "可作全眼铺色、眼窝过渡色、柔和眼线，或作为互补色下方的打底色，增强深度与饱和度。可用刷具按需叠加显色度。",
    "Use this antiqued gold-green as an all-over lid colour, layered over complementary hues, or in the center of the lid and corners of the eyes for a gilded, sea-glint effect. Apply with a brush for your desired level of intensity. Use with a mixing medium for a foiled effect. Wear with shades ‘Tideborn’ and ‘Nautilus’ for a tide-forged blend of kelp, stone, and bronze.": "可作全眼铺色，叠加在互补色之上，或用于眼皮中央和眼角，打造带金属感的海光效果。可用刷具按需叠加显色度。搭配调和液可做出箔光妆效。与 `Tideborn`、`Nautilus` 搭配，可调出海藻、石色与青铜感交织的潮汐色调。",
    "Use this muted kelp green shade as an all-over lid colour, in the sockets and corners of the eyes for depth and definition, or along the lash line as an eyeliner. Apply with a brush for your desired level of intensity. Blend with shades ‘Cyrene’ and ‘Seirēn’ for a sea-tossed surge of moss, gilt, and tidal frost.": "可作全眼铺色，也可用于眼窝和眼角加深轮廓，或沿睫毛根部当眼线使用。可用刷具按需叠加显色度。与 `Cyrene`、`Seirēn` 搭配，可调出海浪翻涌般的苔绿、金属与潮霜感。",
    "This espresso-bitter brown shade can be used to create depth and dimension in the crease, socket, and lash line. Build up the colour in the outer corners of the eyes for a boldly pigmented finish, or use a mixing medium and liner brush for a graphic finish. Apply with a brush for your desired level of intensity. Pairs perfectly with ‘Ciel Figé’ and ‘Nautilus’ for a tide-washed sheen of kelp green and earthen brown.": "适合用于眼窝、轮廓和睫毛根部加深，增强深邃度与立体感。可在眼尾逐步叠加，做出高饱和显色；也可搭配调和液和眼线刷完成更利落的图形眼线。可用刷具按需叠加显色度。与 `Ciel Figé`、`Nautilus` 搭配，可做出海带绿与大地棕交织的潮痕光泽。",
    "This metallic champagne rose shade can be worn as an all-over lid colour or layered over complementary tones for an elevated everyday look. Use this shade with a mixing medium for a wash of colour or a foiled, high-shine effect. Pair with shades ‘Serenade’ and ‘Triton’ for a shimmering second-skin sheen! Apply with fingertips or a dense brush for your desired level of intensity.": "可作全眼铺色，或叠加在互补色之上，打造更精致的日常妆感。搭配调和液可获得轻透染色感或更强烈的金属箔光效果。与 `Serenade`、`Triton` 搭配，可呈现闪耀贴肤的光泽感。可用指腹或扎实眼影刷按需叠加显色度。",
    "This soft, mid-tone shade can be used as an all-over lid colour or as a base tone beneath complementary hues. It can also be used to highlight the brow bone and inner corners of the eyes, or as a transitional shade in the socket of the eye. Use as a base tone beneath shades ‘Murmur’ and ‘Mélusine’ for a glistening, natural finish. Apply with a brush for your desired level of intensity.": "可作全眼铺色或作为互补色下方的打底色。也可用于眉骨和眼头提亮，或作为眼窝位置的过渡色。搭配 `Murmur` 与 `Mélusine` 作打底，可完成自然通透的微光妆感。可用刷具按需叠加显色度。",
    "This mid-tone nude rose shade can be used as an all-over lid colour, beneath complementary tones for increased depth and saturation, or as a transitional tone in the crease and socket. Mix this hue with other matte shades to create 12 new colours. Can also be worn as a blush on light to medium complexions. Pair with ‘Sylph’ and ‘Mélusine’ for a soft and shimmering romantic nude rose look. Apply with a brush for your desired level of intensity.": "可作全眼铺色、作为互补色下方的打底加深色，或用于眼窝和轮廓位置做过渡。与其他哑光色混合，可调出 12 种新色。浅至中等肤色也可当腮红使用。搭配 `Sylph` 与 `Mélusine`，可完成柔和微闪的浪漫裸玫瑰妆感。可用刷具按需叠加显色度。",
    "This duochromatic sandy nude shade can be worn as an all-over lid colour or layered over complementary tones for an unexpected duochromatic shine. Use this shade with a mixing medium for a wash of colour or a foiled, high-shine effect. Pair with shades ‘Oceanic’ and ‘Glinting’ for an alluring aquatic finish! Apply with fingertips or a dense brush for your desired level of intensity.": "可作全眼铺色，或叠加在互补色之上，呈现意想不到的双偏光闪耀。搭配调和液可获得轻透染色感或更强烈的箔光效果。与 `Oceanic`、`Glinting` 搭配，可完成迷人的水感妆效。可用指腹或扎实眼影刷按需叠加显色度。",
    "This light, muted neutral pink-peach shade can be used as an all-over lid colour or as a base tone beneath complementary hues. It can also be used to highlight the brow bone and inner corners of the eyes or as a transitional shade in the socket of the eye. Use as a base tone beneath shades Sylph’ and ‘Glinting’ for a luminous, shimmering glow. Apply with a brush for your desired level of intensity.": "可作全眼铺色，或作为互补色下方的打底色。也可用于眉骨和眼头提亮，或作为眼窝位置的过渡色。搭配 `Sylph` 与 `Glinting` 作打底，可呈现明亮通透的微闪光泽。可用刷具按需叠加显色度。",
    "This nude quartz metallic shade can be used as an all-over base colour, layered over complementary tones for a burst of high shine shimmer, or used as a liner for smokey, subtle definition. Pairs perfectly with shades ‘Glinting’ and ‘Brine’ for a glimmering grey soft smokey eye! Apply with fingertips or a dense brush for your desired level of intensity or use with a mixing medium for a foiled effect.": "可作全眼打底色，叠加在互补色之上增强高光闪泽，也可作为眼线带出柔和精致轮廓。与 `Glinting`、`Brine` 搭配，适合打造带灰调光泽的柔雾烟熏眼妆。可用指腹或扎实眼影刷上色，也可搭配调和液营造更强烈的箔光效果。",
    "This second-skin nude topper can be worn as an all-over lid colour for a natural veil of luminosity or over any shade in the palette for a radiant wash of reflectivity. It can also be used to highlight the brow bone, inner corners of the eyes, cheekbones, and the bridge of the nose. Pairs perfectly over top of “Serenade”, “Murmure” and “Ethos” for a burst of shimmering brilliance.": "可作全眼铺色，营造自然通透的贴肤光泽，也可叠加在盘中任何颜色之上，增强反光感。还可用于眉骨、眼头、颧骨和鼻梁提亮。叠加在 `Serenade`、`Murmure`、`Ethos` 上，能带出更明亮的闪耀感。",
    "This rich navy blue-green shade can be worn alone for a striking monochromatic look or layered on top of complementary tones for a high-shine shift of shimmering pigment. Can also be used to build out the outer crease of the eye, as a liner, or in conjunction with a mixing medium for a foiled effect. Pair with shades ‘Mélusine’ and ‘Glinting’ for a tidal wave of prismatic pigment. Apply with fingertips or a dense brush for your desired level of intensity.": "可单独使用打造强烈的单色妆效，也可叠加在互补色之上，呈现高光泽偏光变化。也可用于加深眼尾眼窝、作为眼线，或搭配调和液打造金属箔感。与 `Mélusine`、`Glinting` 搭配，可完成如潮汐般的棱彩妆效。可用指腹或扎实眼影刷按需叠加显色度。",
    "This nude silver metallic shade can be used as an all-over base colour, layered over complementary tones for a burst of high shine shimmer, or used as a liner for luminous definition. Pair perfectly with shades ‘Siren’ and ‘Abyss’ for oceanic, crystalline candescence. Apply with fingertips or a dense brush for your desired level of intensity or use with a mixing medium for a foiled effect.": "可作全眼打底色，叠加在互补色之上增强高亮闪泽，也可作为眼线带出清透轮廓。与 `Siren`、`Abyss` 搭配，适合打造海洋感、晶莹感的妆效。可用指腹或扎实眼影刷上色，也可搭配调和液营造更强烈的箔光效果。",
    "This bright viloet-blue duochromatic shade can be used as an all-over lid color or layered on top of complementary tones for a high-shine sheen. Up the ante by mixing this shade with a mixing medium for an ultra-saturated foiled flip! Apply with fingertips or a dense brush for your desired level of intensity. Can also be used as liner. Pair with shades ‘Oceanic’ and ‘Mélusine’ for hypnotic tides of luminosity!": "可作全眼铺色，或叠加在互补色之上，呈现高光泽的偏光亮感。搭配调和液可强化饱和度，做出更强烈的金属箔光变化。也可用作眼线。与 `Oceanic`、`Mélusine` 搭配，可营造迷人的海潮光感。可用指腹或扎实眼影刷按需叠加显色度。",
    "This mid-tone shade can be used as an all-over lid colour, as a transitional shade to build out the crease and socket, as a soft liner, or as a base tone beneath complementary tones for increased depth and saturation. Mix this hue with any of the other matte shades to create 12 new hues. Pairs perfectly with ‘Luminary’ and ‘Brine’ to channel the lure of the deep sea. Apply with a brush for your desired level of intensity.": "可作全眼铺色、眼窝过渡色、柔和眼线色，或作为互补色下方的打底加深色，增强层次与饱和度。与盘中其他哑光色混合，可延展出更多色调。搭配 `Luminary`、`Brine`，能呼应深海般的神秘气息。可用刷具按需叠加显色度。",
    "This bitter brown-quartz metallic shade can be used to create depth and dimension in the crease, socket, and lash line. Build up the colour in the outer corners of the eyes for a boldly pigmented finish or use a mixing medium and liner brush for a graphic finish. Pairs perfectly with ‘Abyss’ and ‘Luminary’ for a richly pigmented smokey siren sheen. Use with a brush to achieve your desired level of intensity.": "可用于加深眼窝、轮廓和睫毛根部，增强整体立体度与深邃感。可在眼尾逐步叠加，打造更浓郁饱和的显色效果；也可搭配调和液和眼线刷完成更利落的图形眼线。与 `Abyss`、`Luminary` 搭配，可塑造高显色的浓郁海妖烟熏光泽。建议使用刷具按需叠加显色度。",
    "All over-lid shade for light to medium skin tones, or a pale yellow for darker ones. Can be used to brighten the inner corner of the eye, or under the brow.": "适合浅至中等肤色作全眼铺色；对深肤色则可作为浅黄色提亮色，也可用于眼头或眉骨提亮。",
    "All over lid shade for medium skin tones, can also be used for inner corner or under brow highlighting.": "适合中等肤色作全眼铺色，也可用于眼头或眉骨提亮。",
    "Use as a base color all over the lid for medium skin tones. Can be used in crease for fair to light medium skin.": "适合中等肤色作全眼打底色；浅肤到浅中等肤色也可用于眼窝加深与过渡。",
    "Can be used as lid or crease for fair skin, or lid for medium to dark.": "浅肤色可用于眼皮或眼窝位置；中等至深肤色可作眼皮主色。",
    "A great everyday lid/crease color for light/mid-toned skins, or this can actually be used as a grey/brown on darker skins.": "适合浅肤和中等肤色作为日常眼皮主色或眼窝过渡色；在深肤色上也可呈现柔和灰棕效果。",
    "A great inner eye highlight for dark skins, or warm all over lid or crease for light to medium. This is also a secret weapon for darkness on the lids - since orange neutralizes blue, try this to brighten up darkness on the lid.": "深肤色可用于眼头提亮；浅至中等肤色可作暖调全眼铺色或眼窝过渡色。它也适合修饰眼皮暗沉，因为橘色能中和蓝调，可用于提亮发暗部位。",
    "A super versatile color! This is an AMAZING brow color for redheads, but also as a lid color for medium tones, or a crease color to build depth and dimension for fair to medium skin.": "非常百搭的颜色。既适合红发人群作眉色，也适合中等肤色作眼皮主色，或用于浅至中等肤色的眼窝加深，增强立体层次。",
    "This can be used for lid or crease. Build depth and dimension, or brighten darker skin tones.": "可用于眼皮或眼窝位置，帮助建立深度与立体感，也能更好衬托较深肤色上的暖调表现。",
    "Use all over the lid and crease on all complexions or as a base tone for deeper complexions.": "适合所有肤色用于眼皮与眼窝的大面积铺陈；对深肤色也可作为打底色使用。",
    "This ultra versatile tone is perfect for a smokey eye on almost all skin tones, and can be used for liner, or for brows for brunettes and black hair.": "这是一支适用于大多数肤色的高适配深色，可用于打造烟熏眼妆，也可作为眼线色；深棕发或黑发人群也可用于眉部。",
    "Use in the crease and outer corner for a dimensional wash of warm burgundy.": "适合用于眼窝与眼尾，铺出带暖酒红调的层次感与晕染效果。",
    "Use to highlight and blend into all other tones to soften shades, use on brow bone to highlight.": "可用作高光，并与其他色号混合以柔和整体色调，也可用于眉骨提亮。",
    "Base tone for light to medium skin tones.": "适合浅至中等肤色的底色。",
    "Base tone for light to medium skin tones. Use as a highlight on brow bone for deeper tones. Mix-in with lighter tones and deeper tones to create variegated base tones in an array of depth.": "适合浅至中等肤色的底色；深肤色可作为眉骨提亮；可与更浅或更深的颜色混合，调出不同深浅层次的底色。",
    "Base tone for all skin tones.": "适合所有肤色的底色。",
    "All over solid tone for all skin types. Base tone, as well as midtone for eyeshadow depth and dimension. Also can be used in brows, and as contour.": "适合所有肤色的大面积实色铺陈；可作底色或中间色调，增强眼影深度与立体感；也可用于眉部与修容。",
    "All over tone for all skin types, use as a soft eyeliner for light to medium tones.": "适合所有肤色的大面积铺色；可作为浅至中等肤色的柔和眼线。",
}


PALETTE_TITLE_PARTS = {
    "big-12-mattes-cool2": {
        "shade_count": "12色",
        "size_label": "大号",
        "cn_name": "哑光冷调盘",
        "en_name": "Matte Cool 2",
    },
    "big-12-mattes-warm": {
        "shade_count": "12色",
        "size_label": "大号",
        "cn_name": "哑光暖调盘",
        "en_name": "Warm Mattes",
    },
    "big-12-mattes-neutral": {
        "shade_count": "12色",
        "size_label": "大号/小号",
        "cn_name": "哑光中性盘",
        "en_name": "Matte Neutral",
    },
    "big-12-mattes-cool-original": {
        "shade_count": "12色",
        "size_label": "大号/小号",
        "cn_name": "哑光冷调盘",
        "en_name": "Mattes Cool Original",
    },
    "big-12-editorial-brights": {
        "shade_count": "12色",
        "size_label": "大号/小号",
        "cn_name": "哑光亮彩盘",
        "en_name": "Editorial Brights",
    },
    "big-12-mattes-dark": {
        "shade_count": "12色",
        "size_label": "大号/小号",
        "cn_name": "哑光深调盘",
        "en_name": "Mattes Dark",
    },
    "middle-35-pro-x1": {
        "shade_count": "35色",
        "size_label": "中号",
        "cn_name": "哑光大盘",
        "en_name": "Grande Pro 1X",
    },
    "middle-4-violetta": {
        "shade_count": "4色",
        "size_label": "中号",
        "cn_name": "紫罗兰盘",
        "en_name": "Petits Fours Violetta",
    },
    "small-12-matte-cool": {
        "shade_count": "12色",
        "size_label": "小号",
        "cn_name": "哑光冷调盘",
        "en_name": "Petites Mattes Cool",
    },
    "small-12-shimmers-paris-nudes": {
        "shade_count": "12色",
        "size_label": "小号",
        "cn_name": "巴黎裸光盘",
        "en_name": "Petites Shimmers Paris Nudes",
    },
    "middle-12-cashmerie-charmeuse-etendu": {
        "shade_count": "12色",
        "size_label": "中号",
        "cn_name": "羊绒魅缎盘",
        "en_name": "Cashmerie Charmeuse Etendu",
    },
    "middle-12-sireneuse-etendu": {
        "shade_count": "12色",
        "size_label": "中号",
        "cn_name": "海妖绮梦盘",
        "en_name": "Sireneuse Etendu",
    },
    "middle-12-sireneuse-nocturne-etendu": {
        "shade_count": "12色",
        "size_label": "中号",
        "cn_name": "海妖夜曲盘",
        "en_name": "Sireneuse Nocturne Etendu",
    },
}


HOMEPAGE_LABELS = {
    "big-12-mattes-cool2": "12色 大号 哑光冷调盘 Matte Cool 2",
    "big-12-mattes-warm": "12色 大号 哑光暖调盘 Warm Mattes",
    "big-12-mattes-neutral": "12色 大号/小号 中性盘 Matte Neutral",
    "big-12-mattes-cool-original": "12色 大号/小号 哑光冷调盘 Mattes Cool Original",
    "big-12-editorial-brights": "12色 大号/小号 哑光亮彩盘 Editorial Brights",
    "big-12-mattes-dark": "12色 大号/小号 哑光深调盘 Mattes Dark",
    "middle-35-pro-x1": "35色 中号 哑光大盘 Pro X1",
    "middle-4-violetta": "4色 中号 紫罗兰盘 Petits Fours Violetta",
    "small-12-matte-cool": "12色 小号 哑光冷调盘 Petites Mattes Cool",
    "small-12-shimmers-paris-nudes": "12色 小号 巴黎裸光盘 Petites Shimmers Paris Nudes",
    "middle-12-cashmerie-charmeuse-etendu": "12色 中号 羊绒魅缎盘 Cashmerie Charmeuse Etendu",
    "middle-12-sireneuse-etendu": "12色 中号 海妖绮梦盘 Sireneuse Etendu",
    "middle-12-sireneuse-nocturne-etendu": "12色 中号 海妖夜曲盘 Sireneuse Nocturne Etendu",
}


HOMEPAGE_SECTION = "### 眼影 Viseart"


PRODUCT_URLS = {
    "small-12-matte-cool": "https://viseartparis.com/en-de/products/petites-mattes-cool",
    "small-12-shimmers-paris-nudes": "https://viseartparis.com/en-de/products/petites-shimmers-paris-nudes?_pos=67&_sid=7a187920b&_ss=r",
    "middle-4-violetta": "https://viseartparis.com/en-de/products/petits-fours-violetta?_pos=79&_sid=7a187920b&_ss=r",
    "big-12-mattes-neutral": "https://viseartparis.com/en-de/products/petites-mattes-neutral",
    "big-12-mattes-cool-original": "https://viseartparis.com/en-de/collections/visepro/products/visepro-cool-mattes-original",
    "big-12-editorial-brights": "https://viseartparis.com/en-de/products/visepro-editorial-brights?_pos=8&_sid=0596684ea&_ss=r",
    "big-12-mattes-dark": "https://viseartparis.com/en-de/products/visepro-dark-mattes?_pos=6&_sid=cdce64564&_ss=r",
    "big-12-mattes-warm": "https://viseartparis.com/en-de/products/visepro-warm-mattes",
    "middle-12-cashmerie-charmeuse-etendu": "https://viseartparis.com/en-de/products/cashmerie-charmeuse-etendu",
    "middle-12-sireneuse-etendu": "https://viseartparis.com/en-de/products/visepro-sireneuse-etendu",
    "middle-12-sireneuse-nocturne-etendu": "https://viseartparis.com/en-de/products/sireneuse-nocturne-etendu",
}


CDN_IMAGE_RE = re.compile(r"https://viseartparis\.com/cdn/shop/[^\"' )]+")
SHADE_BLOCK_RE = re.compile(
    r'<span class="metafield-multi_line_text_field">(.*?)</span>', re.DOTALL
)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.DOTALL | re.IGNORECASE)
GALLERY_IMG_RE = re.compile(
    r'<img[^>]+src="([^"]*(?:/cdn/shop/files/)[^"]+)"[^>]+alt="([^"]*)"',
    re.IGNORECASE,
)


@dataclass
class Shade:
    number: int
    name: str
    description: str
    use: str
    warning: str = ""


@dataclass
class SliceContext:
    source_kind: str
    has_occluded_top_row_risk: bool = False


@dataclass
class ProductPageData:
    title: str | None
    shade_text: str | None
    gallery_images: list[tuple[str, str]]


def default_title_for_palette(folder_name: str) -> str:
    parts = PALETTE_TITLE_PARTS.get(folder_name)
    if not parts:
        return folder_name
    return (
        f"Viseart {parts['shade_count']} {parts['size_label']} "
        f"{parts['cn_name']} {parts['en_name']}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Slice Viseart palette icons and generate a bilingual README skeleton."
    )
    parser.add_argument("palette_dir", type=Path, help="Palette folder under docs/viseart")
    parser.add_argument(
        "--source-readme",
        type=Path,
        help="File containing the English shade descriptions. Defaults to README.md in the palette folder.",
    )
    parser.add_argument(
        "--reference-icons",
        type=Path,
        help="Optional reference icons image with the same visual structure.",
    )
    parser.add_argument(
        "--grid",
        type=int,
        nargs=2,
        metavar=("COLS", "ROWS"),
        help="Grid size override. Defaults to 4 3 for 12 shades and 7 5 for 35 shades.",
    )
    parser.add_argument(
        "--slice-ext",
        choices=("png", "jpg"),
        help="Output slice extension. Defaults to the source icons extension if png/jpg, else png.",
    )
    parser.add_argument(
        "--slice-name-mode",
        choices=("number", "number-name"),
        default="number-name",
        help="Whether slice files use 01.png or 01_Name.png style naming.",
    )
    parser.add_argument(
        "--rewrite-readme",
        action="store_true",
        help="Rewrite README.md with generated sections.",
    )
    parser.add_argument(
        "--update-docs-index",
        action="store_true",
        help="Update docs/README.md to include this palette on the Pages homepage.",
    )
    parser.add_argument(
        "--homepage-label",
        help="Optional label text to use in docs/README.md instead of the default mapped label.",
    )
    parser.add_argument(
        "--download-product-assets",
        action="store_true",
        help="Download an id image from the mapped or provided product page when local assets are missing.",
    )
    parser.add_argument(
        "--product-url",
        help="Optional Viseart product page URL to fetch images from.",
    )
    parser.add_argument(
        "--crop-bbox",
        type=int,
        nargs=4,
        metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"),
        help="Optional manual crop box override for slicing difficult source images.",
    )
    parser.add_argument(
        "--first-row-mask-px",
        type=int,
        default=0,
        help="Optional number of pixels to paint black at the top of first-row slices when the lid occludes the top edge.",
    )
    parser.add_argument(
        "--trim-to-pan-boxes",
        action="store_true",
        help="Trim each slice to the detected visible pan area instead of keeping the full grid cell.",
    )
    parser.add_argument(
        "--pan-border-px",
        type=int,
        default=2,
        help="Black border in pixels to add around each detected pan crop when using --trim-to-pan-boxes.",
    )
    return parser.parse_args()


def sanitize_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    safe = re.sub(r"[^A-Za-z0-9]+", "_", ascii_only).strip("_")
    return safe or "Shade"


def detect_file(folder: Path, candidates: list[str]) -> Path:
    for candidate in candidates:
        path = folder / candidate
        if path.exists():
            return path
    matches = []
    for pattern in candidates:
        matches.extend(folder.glob(pattern))
    if matches:
        return sorted(matches)[0]
    raise FileNotFoundError(f"Could not find any of: {candidates} in {folder}")


def product_url_for_palette(palette_dir: Path, explicit_url: str | None) -> str | None:
    if explicit_url:
        return explicit_url
    return PRODUCT_URLS.get(palette_dir.name)


def clean_html_text(value: str) -> str:
    text = value.replace("<br />", "\n")
    text = text.replace("<br/>", "\n")
    text = text.replace("<br>", "\n")
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = text.replace("\u2028", "\n")
    text = text.replace("\xa0", " ")
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_product_image_url(url: str) -> str:
    clean = html.unescape(url)
    if clean.startswith("//"):
        return f"https:{clean}"
    if clean.startswith("/"):
        return f"https://viseartparis.com{clean}"
    return clean


def prefer_full_size_image_url(image_url: str) -> str:
    if "width=750" in image_url:
        return image_url
    if "width=" in image_url:
        return re.sub(r"width=\d+", "width=750", image_url)
    separator = "&" if "?" in image_url else "?"
    return f"{image_url}{separator}width=750"


def extract_gallery_images(html_text: str) -> list[tuple[str, str]]:
    images: list[tuple[str, str]] = []
    seen: set[str] = set()
    for raw_url, raw_alt in GALLERY_IMG_RE.findall(html_text):
        url = normalize_product_image_url(raw_url)
        if "/cdn/shop/files/" not in url or "/preview_images/" in url:
            continue
        alt = clean_html_text(raw_alt)
        if url in seen:
            continue
        seen.add(url)
        images.append((url, alt))
    return images


def is_true_icons_board(alt_text: str, image_url: str) -> bool:
    combined = f"{alt_text} {image_url}".lower()
    swatch_hints = (
        "single shades",
        "swatch",
        "swatches",
        "open palette",
        "open palettes",
        "single shadow",
        "single shadows",
    )
    board_hints = (
        "shade description",
        "printed descriptions",
        "shade board",
        "icons",
        "numbered shade",
        "shade numbers",
    )
    if any(hint in combined for hint in swatch_hints) and not any(
        hint in combined for hint in board_hints
    ):
        return False
    return any(hint in combined for hint in board_hints)


def preferred_gallery_images(gallery_images: list[tuple[str, str]]) -> tuple[str | None, str | None]:
    if not gallery_images:
        return None, None

    cover_url = gallery_images[0][0]
    icons_url = None

    for url, _alt in gallery_images:
        url_lower = url.lower()
        if "final_open" in url_lower or "web_final_open" in url_lower or "final-open" in url_lower:
            cover_url = url
            break

    for url, alt in gallery_images:
        alt_lower = alt.lower()
        if alt_lower.startswith("open ") or "open palette" in alt_lower or "open palettes" in alt_lower:
            cover_url = url
            break

    for url, alt in gallery_images:
        alt_lower = alt.lower()
        url_lower = url.lower()
        if is_true_icons_board(alt_lower, url_lower):
            icons_url = url
            break

    return cover_url, icons_url


def inferred_download_path(target_dir: Path, stem: str, image_url: str) -> Path:
    path = urlsplit(image_url).path
    suffix = Path(path).suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
        suffix = ".jpg"
    return target_dir / f"{stem}{suffix}"


def download_product_image(image_url: str, target_dir: Path, stem: str) -> Path:
    image_url = prefer_full_size_image_url(image_url)
    target_path = inferred_download_path(target_dir, stem, image_url)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(image_url, target_path)
    return target_path


def fetch_product_page_data(product_url: str) -> ProductPageData:
    with urllib.request.urlopen(product_url) as response:
        html_text = response.read().decode("utf-8", errors="ignore")

    title = None
    title_match = H1_RE.search(html_text)
    if title_match:
        title = clean_html_text(title_match.group(1))

    shade_text = None
    for block in SHADE_BLOCK_RE.findall(html_text):
        cleaned = clean_html_text(block)
        if "Shade 1:" in cleaned and "Use:" in cleaned:
            shade_text = cleaned
            break

    return ProductPageData(
        title=title,
        shade_text=shade_text,
        gallery_images=extract_gallery_images(html_text),
    )


def download_primary_product_image(product_url: str, target_path: Path) -> Path:
    with urllib.request.urlopen(product_url) as response:
        html = response.read().decode("utf-8", errors="ignore")

    gallery_images = extract_gallery_images(html)
    if gallery_images:
        cover_url, _ = preferred_gallery_images(gallery_images)
        if cover_url:
            cover_url = prefer_full_size_image_url(cover_url)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(cover_url, target_path)
            return target_path

    matches = CDN_IMAGE_RE.findall(html)
    unique_matches: list[str] = []
    for match in matches:
        clean = match.replace("&amp;", "&")
        if clean not in unique_matches:
            unique_matches.append(clean)

    if not unique_matches:
        raise ValueError(f"No product images found at {product_url}")

    image_url = prefer_full_size_image_url(unique_matches[0])
    target_path.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(image_url, target_path)
    return target_path


def parse_shades_from_text(
    source_text: str,
    folder_name: str,
    fallback_title: str | None = None,
) -> tuple[str, list[Shade]]:
    source_text = re.sub(r"(?<!\n)Shade\s*\n+\s*(\d+:)", r"\nShade \1", source_text)
    source_text = re.sub(r"(Use:\s+[^\n]+?)Shade\s*\n+\s*(\d+:)", r"\1\n\nShade \2", source_text)
    lines = source_text.splitlines()
    title = fallback_title or default_title_for_palette(folder_name)
    for line in lines:
        if line.startswith("# "):
            heading_title = line[2:].strip()
            if heading_title == folder_name and folder_name in PALETTE_TITLE_PARTS:
                title = default_title_for_palette(folder_name)
            else:
                title = heading_title
            break

    shades: list[Shade] = []
    current: dict[str, str] | None = None
    warning_lines: list[str] = []

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        shade_match = SHADE_RE.match(line)
        if shade_match:
            if current is not None:
                shades.append(
                    Shade(
                        number=int(current["number"]),
                        name=current["name"],
                        description=current["description"],
                        use=current.get("use", ""),
                        warning=" ".join(warning_lines).strip(),
                    )
                )
            current = {
                "number": shade_match.group(1),
                "name": shade_match.group(2).strip(),
                "description": shade_match.group(3).strip(),
            }
            warning_lines = []
            continue
        use_match = USE_RE.match(line)
        if use_match and current is not None:
            current["use"] = use_match.group(1).strip()
            continue
        if line.startswith("*WARNING*") and current is not None:
            warning_lines.append(line)

    if current is not None:
        shades.append(
            Shade(
                number=int(current["number"]),
                name=current["name"],
                description=current["description"],
                use=current.get("use", ""),
                warning=" ".join(warning_lines).strip(),
            )
        )
    if not shades:
        raise ValueError("No shade entries found in the source text")
    return title, shades


def parse_shades(source_path: Path) -> tuple[str, list[Shade]]:
    source_text = source_path.read_text(encoding="utf-8")
    return parse_shades_from_text(source_text, source_path.parent.name)


def infer_grid(shade_count: int) -> tuple[int, int]:
    if shade_count == 12:
        return 4, 3
    if shade_count == 4:
        return 2, 2
    if shade_count == 35:
        return 7, 5
    raise ValueError(f"No default grid for {shade_count} shades. Use --grid COLS ROWS.")


def content_bbox(image: Image.Image, threshold: int = 245) -> tuple[int, int, int, int]:
    rgb = image.convert("RGB")
    width, height = rgb.size
    xs: list[int] = []
    ys: list[int] = []

    for y in range(height):
        for x in range(width):
            red, green, blue = cast(tuple[int, int, int], rgb.getpixel((x, y)))
            if red < threshold or green < threshold or blue < threshold:
                xs.append(x)
                ys.append(y)

    if not xs or not ys:
        return (0, 0, width, height)

    pad = 4
    left = max(0, min(xs) - pad)
    top = max(0, min(ys) - pad)
    right = min(width, max(xs) + 1 + pad)
    bottom = min(height, max(ys) + 1 + pad)
    return (left, top, right, bottom)


def scaled_reference_bbox(reference: Image.Image, target: Image.Image) -> tuple[int, int, int, int]:
    ref_left, ref_top, ref_right, ref_bottom = content_bbox(reference)
    ref_width, ref_height = reference.size
    target_width, target_height = target.size

    left_ratio = ref_left / ref_width
    top_ratio = ref_top / ref_height
    right_ratio = (ref_width - ref_right) / ref_width
    bottom_ratio = (ref_height - ref_bottom) / ref_height

    left = int(target_width * left_ratio)
    top = int(target_height * top_ratio)
    right = target_width - int(target_width * right_ratio)
    bottom = target_height - int(target_height * bottom_ratio)
    return (left, top, right, bottom)


def fitted_bbox(bbox: tuple[int, int, int, int], cols: int, rows: int) -> tuple[int, int, int, int]:
    left, top, right, bottom = bbox
    width = right - left
    height = bottom - top
    fitted_width = (width // cols) * cols
    fitted_height = (height // rows) * rows
    left += (width - fitted_width) // 2
    top += (height - fitted_height) // 2
    return (left, top, left + fitted_width, top + fitted_height)


def fitted_cover_bbox_from_bottom_rows(
    bbox: tuple[int, int, int, int], cols: int, rows: int
) -> tuple[int, int, int, int]:
    left, top, right, bottom = bbox
    width = right - left
    height = bottom - top
    fitted_width = (width // cols) * cols
    left += (width - fitted_width) // 2
    right = left + fitted_width

    if rows != 3:
        fitted_height = (height // rows) * rows
        top = bottom - fitted_height
        return (left, top, right, bottom)

    lower_two_rows_top = top + height // 3
    lower_two_rows_height = bottom - lower_two_rows_top
    row_height = (lower_two_rows_height // 2)
    if row_height <= 0:
        return fitted_bbox((left, top, right, bottom), cols, rows)

    full_top = bottom - row_height * rows
    return (left, full_top, right, bottom)


def palette_bbox_from_cover(image: Image.Image, threshold: int = 80) -> tuple[int, int, int, int]:
    rgb = image.convert("RGB")
    outer_left, outer_top, outer_right, outer_bottom = content_bbox(rgb)
    _, height = rgb.size
    content_width = outer_right - outer_left

    row_activity: list[tuple[int, int]] = []
    for y in range(outer_top, outer_bottom):
        active_pixels = 0
        for x in range(outer_left, outer_right):
            red, green, blue = cast(tuple[int, int, int], rgb.getpixel((x, y)))
            average = (red + green + blue) // 3
            if average < 245:
                active_pixels += 1
        row_activity.append((y, active_pixels))

    upper_rows = row_activity[: max(2, len(row_activity) // 3)]
    strongest_drop_y = outer_top
    strongest_drop = 0
    for index in range(1, len(upper_rows)):
        prev_y, prev_count = upper_rows[index - 1]
        curr_y, curr_count = upper_rows[index]
        drop = prev_count - curr_count
        if drop > strongest_drop:
            strongest_drop = drop
            strongest_drop_y = curr_y

    if strongest_drop == 0:
        return fitted_bbox((outer_left, outer_top, outer_right, outer_bottom), 4, 3)

    top = max(0, strongest_drop_y - 42)
    bottom = min(height, outer_bottom - 8)
    return (outer_left, top, outer_right, bottom)


def translate_description(text: str) -> str:
    normalized = " ".join(text.split())
    if normalized in DESCRIPTION_TRANSLATIONS:
        return DESCRIPTION_TRANSLATIONS[normalized]
    if text in DESCRIPTION_TRANSLATIONS:
        return DESCRIPTION_TRANSLATIONS[text]
    return text


def translate_use(text: str) -> str:
    normalized = " ".join(text.split())
    if normalized.startswith(
        "All over solid tone for all skin types. Base tone, as well as midtone for eyeshadow depth and dimension. Also can be used in brows, and as a contour."
    ):
        return "适合所有肤色大面积铺色；既可作打底色，也可作为增强眼影深度与立体感的中间色调；同时也可用于眉部与修容。"
    if normalized in USE_TRANSLATIONS:
        return USE_TRANSLATIONS[normalized]
    if text in USE_TRANSLATIONS:
        return USE_TRANSLATIONS[text]

    replacements = [
        ("All over-lid shade", "全眼铺色"),
        ("all-over lid shade", "全眼铺色"),
        ("All-over lid shade", "全眼铺色"),
        ("Base tone", "底色"),
        ("base tone", "底色"),
        ("transitional shade", "过渡色"),
        ("inner corner", "眼头"),
        ("inner corners", "眼头"),
        ("brow bone", "眉骨"),
        ("highlight", "提亮"),
        ("smokey eye", "烟熏妆"),
        ("soft eyeliner", "柔和眼线"),
        ("outer corners", "眼尾"),
        ("creases", "眼窝"),
        ("crease", "眼窝"),
        ("blush", "腮红"),
        ("contour", "修容"),
        ("brows", "眉部"),
        ("mix", "混合"),
        ("lighten", "提亮"),
        ("soften", "柔和"),
    ]
    result = text
    for source, target in replacements:
        result = re.sub(source, target, result, flags=re.IGNORECASE)
    return result


def detect_visible_pan_bbox(tile: Image.Image, ignore_top_px: int = 0) -> tuple[int, int, int, int] | None:
    rgb = tile.convert("RGB")
    width, height = rgb.size
    visited: set[tuple[int, int]] = set()
    best_bbox: tuple[int, int, int, int] | None = None
    best_area = 0

    def is_pan_pixel(x: int, y: int) -> bool:
        red, green, blue = cast(tuple[int, int, int], rgb.getpixel((x, y)))
        avg = (red + green + blue) // 3
        return 18 < avg < 250

    for y in range(ignore_top_px, height):
        for x in range(width):
            point = (x, y)
            if point in visited:
                continue
            visited.add(point)
            if not is_pan_pixel(x, y):
                continue

            queue = deque([point])
            min_x = max_x = x
            min_y = max_y = y
            area = 0

            while queue:
                current_x, current_y = queue.popleft()
                area += 1
                min_x = min(min_x, current_x)
                max_x = max(max_x, current_x)
                min_y = min(min_y, current_y)
                max_y = max(max_y, current_y)

                for next_x, next_y in (
                    (current_x + 1, current_y),
                    (current_x - 1, current_y),
                    (current_x, current_y + 1),
                    (current_x, current_y - 1),
                ):
                    if not (0 <= next_x < width and 0 <= next_y < height):
                        continue
                    next_point = (next_x, next_y)
                    if next_point in visited:
                        continue
                    visited.add(next_point)
                    if is_pan_pixel(next_x, next_y):
                        queue.append(next_point)

            bbox = (min_x, min_y, max_x + 1, max_y + 1)
            bbox_width = bbox[2] - bbox[0]
            bbox_height = bbox[3] - bbox[1]
            if bbox_width < width * 0.28 or bbox_height < height * 0.28:
                continue
            if area > best_area:
                best_area = area
                best_bbox = bbox

    return best_bbox


def crop_tile_to_pan(tile: Image.Image, border_px: int, ignore_top_px: int = 0) -> Image.Image:
    bbox = detect_visible_pan_bbox(tile, ignore_top_px=ignore_top_px)
    if not bbox:
        return tile

    cropped = tile.crop(bbox)
    if border_px <= 0:
        return cropped

    framed = Image.new("RGB", (cropped.width + border_px * 2, cropped.height + border_px * 2), (0, 0, 0))
    framed.paste(cropped.convert("RGB"), (border_px, border_px))
    return framed


def build_readme(
    title: str,
    cover_name: str,
    shades: list[Shade],
    slice_names: list[str],
    slice_context: SliceContext,
) -> str:
    blocks = [f"# {title}", f"![id]({cover_name})", ""]
    if slice_context.source_kind == "id":
        blocks.append(
            "> 提示：本页切片来自官网开盖图 `id`，并非独立的带描述色板图 `icons`。"
        )
        if slice_context.has_occluded_top_row_risk:
            blocks.append(
                "> 第一排色块可能会受到盖子边缘轻微遮挡；如果后续拿到带描述色板图，应优先用 `icons` 重新切图。"
            )
        blocks.append("")
    for shade, slice_name in zip(shades, slice_names):
        chinese_name = NAME_TRANSLATIONS.get(shade.name, shade.name)
        chinese_description = translate_description(shade.description)
        chinese_use = translate_use(shade.use)
        blocks.append(f"## Shade {shade.number}: {shade.name} — {shade.description}")
        blocks.append(f"![Shade {shade.number} {shade.name}](./slices/{slice_name})")
        blocks.append("")
        blocks.append(f"Use: {shade.use}")
        blocks.append("")
        blocks.append(
            f"##### 色号 {shade.number}：{chinese_name} ({shade.name}) —— {chinese_description}"
        )
        blocks.append(f"用途：{chinese_use}")
        if shade.warning:
            blocks.append("")
            blocks.append(shade.warning)
            blocks.append("提示：在美国法规下，此色含有未获 FDA 批准用于眼周的色料。")
        blocks.append("")
    return "\n".join(blocks).strip() + "\n"


def derive_homepage_label(palette_dir: Path, title: str, explicit_label: str | None) -> str:
    if explicit_label:
        return explicit_label.strip()
    if palette_dir.name in HOMEPAGE_LABELS:
        return HOMEPAGE_LABELS[palette_dir.name]
    return title.removeprefix("Viseart ").strip()


def update_docs_index(repo_root: Path, palette_dir: Path, homepage_label: str) -> Path:
    docs_readme = repo_root / "docs" / "README.md"
    lines = docs_readme.read_text(encoding="utf-8").splitlines()
    relative_path = f"./viseart/{palette_dir.name}/README.md"
    entry = f"- 📄 [{homepage_label}]({relative_path})"

    if entry in lines:
        return docs_readme

    updated_lines: list[str] = []
    inserted = False
    inside_section = False

    for line in lines:
        updated_lines.append(line)
        if line.strip() == HOMEPAGE_SECTION:
            inside_section = True
            continue

        if inside_section and line.startswith("### "):
            updated_lines.insert(len(updated_lines) - 1, entry)
            inserted = True
            inside_section = False

    if inside_section and not inserted:
        updated_lines.append(entry)
        inserted = True

    if not inserted:
        if updated_lines and updated_lines[-1] != "":
            updated_lines.append("")
        updated_lines.append(HOMEPAGE_SECTION)
        updated_lines.append(entry)

    docs_readme.write_text("\n".join(updated_lines).rstrip() + "\n", encoding="utf-8")
    return docs_readme


def save_slices(
    icons_path: Path,
    output_dir: Path,
    shades: list[Shade],
    cols: int,
    rows: int,
    reference_icons: Path | None,
    slice_ext: str,
    slice_name_mode: str,
    use_cover_palette_bbox: bool,
    crop_bbox: tuple[int, int, int, int] | None,
    first_row_mask_px: int,
    trim_to_pan_boxes: bool,
    pan_border_px: int,
) -> list[str]:
    image = Image.open(icons_path)
    if crop_bbox:
        bbox = crop_bbox
    elif use_cover_palette_bbox:
        bbox = palette_bbox_from_cover(image)
    elif reference_icons:
        reference = Image.open(reference_icons)
        bbox = scaled_reference_bbox(reference, image)
    else:
        bbox = content_bbox(image)
    if use_cover_palette_bbox:
        bbox = fitted_cover_bbox_from_bottom_rows(bbox, cols, rows)
    else:
        bbox = fitted_bbox(bbox, cols, rows)

    left, top, right, bottom = bbox
    content = image.crop((left, top, right, bottom))
    cell_width = content.width // cols
    cell_height = content.height // rows
    first_row_offset = cell_height // 5 if use_cover_palette_bbox and rows == 3 else 0

    output_dir.mkdir(parents=True, exist_ok=True)
    names: list[str] = []

    for index, shade in enumerate(shades):
        row = index // cols
        col = index % cols
        crop_left = col * cell_width
        crop_top = row * cell_height
        crop_right = crop_left + cell_width
        crop_bottom = crop_top + cell_height
        if first_row_offset and row == 0:
            crop_top = min(content.height - cell_height, crop_top + first_row_offset)
            crop_bottom = crop_top + cell_height
        tile = content.crop((crop_left, crop_top, crop_right, crop_bottom))
        if trim_to_pan_boxes:
            tile = crop_tile_to_pan(
                tile,
                border_px=pan_border_px,
                ignore_top_px=first_row_mask_px if row == 0 else 0,
            )
        elif first_row_mask_px and row == 0:
            draw = ImageDraw.Draw(tile)
            draw.rectangle((0, 0, tile.width, min(first_row_mask_px, tile.height)), fill=(0, 0, 0))

        prefix = f"{shade.number:02d}"
        if slice_name_mode == "number-name":
            filename = f"{prefix}_{sanitize_name(shade.name)}.{slice_ext}"
        else:
            filename = f"{prefix}.{slice_ext}"

        save_path = output_dir / filename
        if slice_ext == "jpg":
            tile.convert("RGB").save(save_path, quality=95)
        else:
            tile.save(save_path)
        names.append(filename)
    return names


def main() -> None:
    args = parse_args()
    palette_dir = args.palette_dir.resolve()
    repo_root = palette_dir.parents[2]
    source_readme = (args.source_readme or palette_dir / "README.md").resolve()
    product_url = product_url_for_palette(palette_dir, args.product_url)

    page_data: ProductPageData | None = None
    if product_url:
        page_data = fetch_product_page_data(product_url)

    if source_readme.exists():
        try:
            title, shades = parse_shades(source_readme)
        except ValueError:
            if not page_data or not page_data.shade_text:
                raise
            title, shades = parse_shades_from_text(
                page_data.shade_text,
                palette_dir.name,
                fallback_title=default_title_for_palette(palette_dir.name)
                if palette_dir.name in PALETTE_TITLE_PARTS
                else page_data.title,
            )
    else:
        if not page_data or not page_data.shade_text:
            raise FileNotFoundError(
                f"No local shade text found at {source_readme} and no parsable product page data available"
            )
        title, shades = parse_shades_from_text(
            page_data.shade_text,
            palette_dir.name,
            fallback_title=default_title_for_palette(palette_dir.name)
            if palette_dir.name in PALETTE_TITLE_PARTS
            else page_data.title,
        )

    cols, rows = tuple(args.grid) if args.grid else infer_grid(len(shades))

    if args.download_product_assets:
        try:
            cover_path = detect_file(palette_dir, ["id.png", "id.jpg", "id.jpeg", "id.webp"])
        except FileNotFoundError:
            if not product_url:
                raise ValueError("No local id image and no product URL available for download")
            if page_data and page_data.gallery_images:
                cover_url, _ = preferred_gallery_images(page_data.gallery_images)
                if cover_url:
                    cover_path = download_product_image(cover_url, palette_dir, "id")
                else:
                    cover_path = download_primary_product_image(product_url, palette_dir / "id.jpg")
            else:
                cover_path = download_primary_product_image(product_url, palette_dir / "id.jpg")

        try:
            detect_file(palette_dir, ["icons.png", "icons.jpg", "icons.jpeg", "icons.webp"])
        except FileNotFoundError:
            if page_data and page_data.gallery_images:
                _, icons_url = preferred_gallery_images(page_data.gallery_images)
                if icons_url:
                    download_product_image(icons_url, palette_dir, "icons")
    else:
        cover_path = detect_file(palette_dir, ["id.png", "id.jpg", "id.jpeg", "id.webp"])

    use_cover_palette_bbox = False
    try:
        icons_path = detect_file(palette_dir, ["icons.png", "icons.jpg", "icons.jpeg", "icons.webp"])
    except FileNotFoundError:
        icons_path = cover_path
        use_cover_palette_bbox = True

    slice_context = SliceContext(
        source_kind="id" if use_cover_palette_bbox else "icons",
        has_occluded_top_row_risk=use_cover_palette_bbox,
    )

    if args.slice_ext:
        slice_ext = args.slice_ext
    else:
        source_ext = icons_path.suffix.lower().lstrip(".")
        slice_ext = source_ext if source_ext in {"png", "jpg"} else "png"

    slice_names = save_slices(
        icons_path=icons_path,
        output_dir=palette_dir / "slices",
        shades=shades,
        cols=cols,
        rows=rows,
        reference_icons=args.reference_icons.resolve() if args.reference_icons else None,
        slice_ext=slice_ext,
        slice_name_mode=args.slice_name_mode,
        use_cover_palette_bbox=use_cover_palette_bbox,
        crop_bbox=tuple(args.crop_bbox) if args.crop_bbox else None,
        first_row_mask_px=args.first_row_mask_px,
        trim_to_pan_boxes=args.trim_to_pan_boxes,
        pan_border_px=args.pan_border_px,
    )

    readme_body = build_readme(title, cover_path.name, shades, slice_names, slice_context)
    if args.rewrite_readme:
        (palette_dir / "README.md").write_text(readme_body, encoding="utf-8")
        print(f"Rewrote README: {palette_dir / 'README.md'}")
    else:
        print(readme_body)

    if args.update_docs_index:
        homepage_label = derive_homepage_label(palette_dir, title, args.homepage_label)
        docs_readme = update_docs_index(repo_root, palette_dir, homepage_label)
        print(f"Updated docs index: {docs_readme}")

    print(f"Generated {len(slice_names)} slices in {palette_dir / 'slices'}")


if __name__ == "__main__":
    main()