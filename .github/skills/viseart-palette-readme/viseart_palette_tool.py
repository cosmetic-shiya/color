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


SHADE_RE = re.compile(r"^(?:##\s+)?Shade\s+(\d+):\s+(.*?)\s+(?:-|–|—)\s+(.*)$")
SHADE_DESCRIPTION_ONLY_RE = re.compile(r"^(?:##\s+)?Shade\s+(\d+):\s+(.*\S)\s*$")
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
    "Macaron": "马卡龙杏粉",
    "Brûlée": "焦糖布蕾",
    "Rococo": "洛可可蜜桃",
    "Financier": "费南雪金棕",
    "Mirabelle": "蜜李杏金",
    "Millefeuille": "千层酥",
    "Biscuit": "饼干奶棕",
    "Antoinette": "安托瓦内特奶霜",
    "Confiture": "蜜桃果酱",
    "Pêche II": "蜜桃米杏",
    "Suede": "麂皮香槟",
    "Savarin": "萨瓦兰奶棕",
    "Cognac": "干邑陶棕",
    "Sable": "暖貂巧棕",
    "Ember": "余烬铜橘",
    "Apricot": "杏金微光",
    "Roseus": "柔雾桃粉",
    "Chocolat II": "黑巧深棕",
    "Mahogany": "桃心木紫棕",
    "Cointreau": "君度铜金",
    "Ode to Hannah": "汉娜古金",
    "Byzantine": "拜占庭晶光",
    "Imperial": "帝国灰粉",
    "Tyrian": "提尔帝紫",
    "Reine": "烟熏紫蔚",
    "Elixir": "灵药晶辉",
    "Roseate": "玫瑰裸纱",
    "Lueur": "柔光玫瑰金",
    "Roussillon": "鲁西永陶土",
    "Calisson": "杏仁糖",
    "Soleil": "日曜暖金",
    "Clafoutis": "法式水果塔",
    "Ganache": "甘纳许深棕",
    "Pêche": "蜜桃糖釉",
    "Eglantine": "野蔷薇米杏",
    "Mirth": "欢愉柔棕",
    "Puck": "玫瑰裸棕",
    "Dewdrop": "露珠香槟",
    "Faerie": "仙灵香粉",
    "Orbs": "星珠光纱",
    "Titania": "仙后雾紫",
    "Changeling": "幻形玫偏光",
    "Cupidon": "丘比特粉棕",
    "Perchance": "遐想中棕",
    "Potion": "魔药酒莓",
    "Hawthorne": "山楂冷棕",
    "Neutral Light Wax": "浅中性塑眉蜡",
    "Light Ash": "浅灰调棕",
    "Light Taupe": "浅灰褐",
    "Neutral Ash": "中性灰棕",
    "Neutral Smoke": "中性烟灰棕",
    "Neutral Medium Wax": "中性中调塑眉蜡",
    "Light Auburn": "浅赤褐",
    "Medium Auburn": "中赤褐",
    "Neutral Mink": "中性貂棕",
    "Mink Brunette": "貂棕深褐",
    "Neutral Dark Ash Wax": "深中性灰调塑眉蜡",
    "Platinum": "铂灰",
    "Sterling": "纯银灰",
    "Dark Ash": "深灰调棕",
    "Graphite": "石墨灰",
    "Lune de Miel": "蜜月光",
    "Nacre Blanche": "白珠光",
    "Abricotine Fraîche": "鲜杏粉",
    "Nougatine": "牛轧糖",
    "Fleur d’Or": "金杏花",
    "Abricot Givré": "霜杏辉",
    "Abricot Sauvage": "野杏桃",
    "Bois d’Ambre": "琥珀木",
    "Nectar Brûlé": "焦蜜铜",
    "Abricot Doré": "金杏釉",
    "Cacao Serein": "静夜可可",
    "Ganache Noire": "黑甘纳许",
    "Lunaision": "月雾",
    "Séléné": "月神",
    "Veillée": "守夜灰棕",
    "Éther": "以太米杏",
    "Aube": "晨曦玫瑰",
    "Nocturne": "夜曲",
    "Lunaire": "月辉紫",
    "Étoilée": "星夜枪灰",
    "Rêve": "幻梦钢蓝",
    "Nuit": "夜幕黑莓",
    "Noctis": "暗夜银灰",
    "Envoûté": "迷魅浓咖",
    "Plume": "羽雾粉",
    "Violetine": "紫绒粉",
    "Chimère": "幻魅偏光",
    "Cendrée": "烟灰紫褐",
    "Astraea": "星辉灰棕",
    "Serpentine": "灵蛇幻紫",
    "Iantha": "鸢尾雾紫",
    "Silène Noctiflore": "夜绽灰棕",
    "Gris Fumé": "烟熏灰紫",
    "Fleur de Nuit": "夜之花",
    "Mûre Sauvage": "野黑莓",
    "Nocturna": "夜莓深紫",
    "Pétaline": "花瓣粉",
    "Orchidée": "兰瓣粉",
    "Améthyste": "紫晶古铜",
    "Taupeline": "灰褐雾影",
    "Lilasé": "丁香雾紫",
    "Violine": "紫罗兰调",
    "Opaline": "欧泊偏光",
    "Ipomée": "牵牛花紫",
    "Prisme": "棱镜玫瑰",
    "Sureau": "接骨木雾紫",
    "Charoïte": "查罗石裸灰",
    "Prunelle": "野李深莓",
    "Perle D'or": "珍珠蜜粉",
    "Rosée": "玫露香槟",
    "Soft Pink": "柔粉",
    "Isolde": "浅石裸棕",
    "Lilas": "丁香雾紫",
    "Amande": "杏仁奶霜",
    "Haskap": "哈斯卡普暖棕",
    "Majeste": "焦糖华彩",
    "Pastille": "糖片钴蓝",
    "Vedette": "主秀铜光",
    "Tiramisu": "提拉米苏灰褐",
    "Argenté": "银霜",
    "Argentée": "银霜",
    "Burlesque": "魅舞焦糖",
    "Cordial": "酒心勃艮第",
    "Fondant": "糖霜银玫",
    "Pompidou": "蓬皮杜丁香粉",
    "Dulce": "焦糖古铜",
    "Cambresine": "灰石褐紫",
    "Espresso": "浓缩苦棕",
    "Folies": "幻金",
    "Pigalle": "香草蜜桃",
    "Mousseline": "焦梅绒",
    "Sucré": "糖晶棕",
    "Muscade": "肉豆蔻棕",
    "Jazz": "爵士玫金",
    "Laughter": "裸香槟",
    "Cabaret": "歌舞铜金",
    "Archives": "古典香槟",
    "Pecan": "山核桃棕",
    "Cire": "蜡灰丁香",
    "Veloutine": "丝绒浓咖",
    "Chiffon": "雪纺蜜桃",
    "Crème Brûlée": "焦糖布蕾",
    "Platane": "梧桐裸棕",
    "Latte": "拿铁米棕",
    "Sorrel": "暖肉桂",
    "Groseille": "醋栗石榴",
    "Nue": "裸灰棕",
    "Cacao": "可可深棕",
    "Dahlia": "大丽花洋红",
    "Baie": "莓李灰紫",
    "Pénombre": "暮影钴蓝",
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
    "Light, citron champagne with a shimmer finish.": "浅柠香槟色，闪光质地。",
    "Soft pearl crème with a matte finish.": "柔和珍珠奶霜色，哑光质地。",
    "Light nude pink with a matte finish.": "浅裸粉色，哑光质地。",
    "Light, taupe fawn brown with a matte finish.": "浅灰褐小鹿棕，哑光质地。",
    "Soft, beige-pink crème with a matte finish.": "柔和米粉奶霜色，哑光质地。",
    "Nude plum-rose quartz with silver, pink, and gold duochromatic flecks.": "裸梅玫瑰石英色，带银、粉、金双偏光闪片。",
    "Soft, sugared peach with a satin finish.": "柔和糖霜蜜桃色，缎光质地。",
    "Rosewood taupe with a blue, pink, and gold duochromatic finish.": "玫瑰木灰褐色，带蓝、粉、金双偏光光泽。",
    "Honeyed bronze with a metallic finish.": "蜜糖古铜色，金属质地。",
    "Iced apricot glaze with a satin finish.": "冰杏釉光色，缎光质地。",
    "Midtone brown-plum with a matte finish.": "中调棕梅子色，哑光质地。",
    "Dark cocoa brown with a satin finish.": "深可可棕色，缎光质地。",
    "Muted dusty mauve with a matte finish.": "柔雾灰豆沙色，哑光质地。",
    "Cool, light beige with a matte finish.": "冷调浅米色，哑光质地。",
    "Midtone cool grey taupe with a matte finish.": "中调冷灰棕色，哑光质地。",
    "Midtone neutral beige with a matte finish.": "中调中性米色，哑光质地。",
    "Burgundy rose with a satin shimmer finish.": "酒红玫瑰色，缎闪质地。",
    "Deep violet with a duochromatic finish.": "深紫色，双偏光质地。",
    "Deep gunmetal brown with a satin metallic finish.": "深枪灰棕色，缎金属质地。",
    "Steel French blue with a matte finish.": "钢感法式蓝，哑光质地。",
    "Smoked blackberry with a matte finish.": "烟熏黑莓色，哑光质地。",
    "Deep grey with a crystalline metallic finish.": "深灰色，晶亮金属质地。",
    "Deep espresso brown with a matte finish.": "深浓缩咖棕色，哑光质地。",
    "Light, cool-toned nude pink with a matte finish.": "浅冷调裸粉色，哑光质地。",
    "Light blush pink with a matte finish.": "浅腮红粉色，哑光质地。",
    "White purple-pink with a duochromatic finish.": "白调紫粉色，双偏光质地。",
    "Mid-tone greige-purple with a matte finish.": "中调灰米紫色，哑光质地。",
    "Cool mid-tone taupe brown with a matte finish.": "冷调中灰棕色，哑光质地。",
    "Light purple with flecks of silver, lilac, pink, and green with a duochromatic finish.": "浅紫色，带银色、淡紫、粉色与绿色闪片，双偏光质地。",
    "Mid-tone dusty cool-toned purple with a matte finish.": "中调灰雾冷紫色，哑光质地。",
    "Mid-tone taupe brown with a matte finish.": "中调灰棕色，哑光质地。",
    "Smoked taupe-brown purple with a silver shimmer finish.": "烟熏灰棕紫色，银闪质地。",
    "Light muted lavender with a matte finish.": "浅柔雾薰衣草色，哑光质地。",
    "Mid-tone, cool-toned cacao taupe with a matte finish.": "中调冷可可灰棕色，哑光质地。",
    "Deep elderberry purple brown with a matte finish.": "深接骨木莓紫棕色，哑光质地。",
    "Light petal pink with delicate magenta reflects and a satin finish.": "浅花瓣粉色，带细腻洋红反光，缎光质地。",
    "Bronzed taupe shimmer with warm dimensional depth.": "古铜灰褐闪色，带暖调立体深度。",
    "Light, cool-toned taupe grey with a matte finish.": "浅冷调灰褐灰色，哑光质地。",
    "Muted, cool-toned lilac with a matte finish.": "柔雾冷丁香紫色，哑光质地。",
    "Deep violet with an orchid-blue duochromatic shift and satin finish.": "深紫色，带兰蓝偏光变化，缎光质地。",
    "Sheer, high-shine topper with a blue-magenta duochromatic shift.": "轻透高闪叠擦色，带蓝洋红双偏光变化。",
    "Radiant pink-violet duochrome with prismatic flecks of blue, magenta, and ruby.": "明亮粉紫双偏光色，带蓝色、洋红与红宝石色棱彩闪片。",
    "Nude rose-mauve with blue reflectivity and a satin finish.": "裸玫瑰豆沙色，带蓝调反光，缎光质地。",
    "Cool-toned smoky lilac grey with a matte finish.": "冷调烟熏丁香灰色，哑光质地。",
    "Cool-toned stone nude with a matte finish.": "冷调石感裸色，哑光质地。",
    "Deep elderberry purple-brown with a matte finish.": "深接骨木莓紫棕色，哑光质地。",
    "Light champagne blush pink with a matte finish.": "浅香槟腮红粉色，哑光质地。",
    "Light pink champagne with a high-shine, metallic finish.": "浅粉香槟色，高闪金属质地。",
    "Soft light pink with a matte finish": "柔和浅粉色，哑光质地。",
    "Light stone-brown nude with a matte finish.": "浅石棕裸色，哑光质地。",
    "Light cool taupe with a matte finish.": "浅冷灰褐色，哑光质地。",
    "Silver with a shimmer finish.": "银色，闪光质地。",
    "Metallic satin caramel hue with a duochromatic finish.": "焦糖金属缎光色，双偏光质地。",
    "Iced silver rose with a shimmer finish.": "冰银玫瑰色，闪光质地。",
    "Muted, cool-toned pink lilac with a matte finish.": "柔雾冷丁香粉色，哑光质地。",
    "Warm, midtone burnished bronze with a shimmer finish.": "暖调中调抛光古铜色，闪光质地。",
    "Midtone greige stone hue with a matte finish": "中调灰米石色，哑光质地。",
    "Bitter brown with a matte finish": "深苦棕色，哑光质地。",
    "Light gold with a metallic finish.": "浅金色，金属质地。",
    "Pale vanilla-peach with a matte finish.": "浅香草蜜桃色，哑光质地。",
    "Burnt-plum with a matte finish.": "焦梅子色，哑光质地。",
    "Warm brown with a shimmer finish.": "暖棕色，闪光质地。",
    "A nutmeg brown with a matte finish": "肉豆蔻棕色，哑光质地。",
    "Light rose gold with a duochromatic finish.": "浅玫瑰金色，双偏光质地。",
    "Nude beige satin metallic with a shimmer finish.": "裸米色缎金属光，闪光质地。",
    "Golden bronze with a metallic finish.": "金古铜色，金属质地。",
    "Nude champagne with a metallic satin finish.": "裸香槟色，金属缎光质地。",
    "Sienna brown with a matte finish.": "赭石棕色，哑光质地。",
    "Light bark lilac taupe with a metallic finish.": "浅树皮丁香灰褐色，金属质地。",
    "Espresso bitter brown with a matte finish": "浓缩苦棕色，哑光质地。",
    "Soft cream with a matte finish": "柔和奶霜色，哑光质地。",
    "Nude peach with a matte finish": "裸蜜桃色，哑光质地。",
    "Bright champagne peach with a shimmer finish": "明亮香槟蜜桃色，闪光质地。",
    "Glistening candied peach with a shimmer finish": "闪耀糖渍蜜桃色，闪光质地。",
    "Soft, mid-tone brown with a matte finish.": "柔和中调棕色，哑光质地。",
    "Mid-tone nude rose-brown with a matte finish.": "中调裸玫瑰棕色，哑光质地。",
    "Champagne nude rosé with a shimmer finish.": "香槟裸玫瑰色，闪光质地。",
    "Light champagne pink with a shimmer finish.": "浅香槟粉色，闪光质地。",
    "Second-skin nude topper with reflectivity.": "贴肤裸色提亮叠擦色，带反光感。",
    "Muted purple-grey with a matte finish.": "柔雾紫灰色，哑光质地。",
    "Nude rose with a blue duochrome finish.": "裸玫瑰色，带蓝调双偏光质地。",
    "Light pink-brown with a matte finish.": "浅粉棕色，哑光质地。",
    "Medium brown with a matte finish.": "中调棕色，哑光质地。",
    "Muted burgundy with gold-pink reflectivity.": "柔雾酒红色，带金粉反光。",
    "Cool-toned brown with a matte finish.": "冷调棕色，哑光质地。",
    "Neutral Light wax for light blonde to light brunette hair": "适合浅金发到浅棕发的浅中性色塑眉蜡。",
    "Light ash with a green undertone": "浅灰调棕色，带绿色底调。",
    "Light taupe with a neutral undertone": "浅灰褐色，带中性底调。",
    "Neutral Ash with a green undertone": "中性灰棕色，带绿色底调。",
    "Medium ash with a neutral undertone.": "中调灰棕色，带中性底调。",
    "Neutral Medium wax for blonde to brunette": "适合金发到棕发的中性色中调塑眉蜡。",
    "Light Auburn taupe with a muted red undertone": "浅赤褐灰褐色，带柔和红调底色。",
    "Medium Auburn with a red undertone": "中赤褐色，带红调底色。",
    "Neutral mink with a touch of green and auburn.": "中性貂棕色，带一丝绿色与赤褐调。",
    "Neutral medium brown with a hint of aubergine": "中性中棕色，带一丝茄紫底调。",
    "Blonde to deep tones.": "适合金发到深色发色。",
    "Light charcoal with a cool undertone.": "浅炭灰色，带冷调底色。",
    "Neutral medium charcoal grey ash.": "中性中调炭灰灰棕色。",
    "Mid-toned charcoal grey with a cool undertone.": "中调炭灰色，带冷调底色。",
    "Deep ash with a slight aubergine undertone.": "深灰调色，带轻微茄紫底调。",
    "Muted cantaloupe with a matte finish.": "柔和哈密瓜橘色，哑光质地。",
    "soft buttercream with a matte finish.": "柔和奶油霜色，哑光质地。",
    "Terracotta with a matte finish.": "陶土色，哑光质地。",
    "Caramel nude with a matte finish.": "焦糖裸色，哑光质地。",
    "Tawny beige with a matte finish.": "黄褐米色，哑光质地。",
    "Warm cinnamon with a matte finish.": "暖肉桂色，哑光质地。",
    "Soft garnet with a matte finish.": "柔和石榴红色，哑光质地。",
    "Taupe brown with a matte finish.": "灰褐棕色，哑光质地。",
    "Dark chocolate with a matte finish.": "深巧克力色，哑光质地。",
    "Magenta with a matte finish.": "洋红色，哑光质地。",
    "Dusty plum with a matte finish.": "灰调李子色，哑光质地。",
    "Cobalt blue with a matte finish.": "钴蓝色，哑光质地。",
    "Copper with a metallic finish.": "铜金色，金属质地。",
    "Golden bronze with a metallic finish.": "金铜古铜色，金属质地。",
    "Pale vanilla-peach with a matte finish.": "浅香草蜜桃色，哑光质地。",
    "Rich burgundy with a metallic finish.": "浓郁勃艮第酒红色，金属质地。",
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
    "All over base tone for all skin types. For deep skin, use as highlight on brow bone. Mix this tone into the other matte shades to create a multitude of sorbet type shades.": "适合所有肤色作全眼打底；深肤色也可用于眉骨提亮。还可与其他哑光色混合，调出多种轻甜柔雾的雪葩色调。",
    "Base tone for all skin types, can be used as a highlighter for deeper tones or a midtone for the lightest complexions. This super versatile color can be mixed with of the other tones to add depth and brightness..": "适合所有肤色作底色；深肤色可作提亮色，极浅肤色也可作中间过渡色。这一色非常百搭，可与盘中其他颜色混合，增加深度与明亮感。",
    "This tone can be used as an all over wash of nude shimmer for all complexions, can also be worn as a cheek and brow bone highlighter.": "适合所有肤色作全眼裸闪铺色，也可用作面部与眉骨提亮。",
    "This shade can be worn alone or as a topper over matte hues to add brightness and luminousity! *WARNING* - In the US, this shade contains pigments that the FDA has not approved for use in the eye area.": "可单独使用，或叠加在哑光色上增强明亮度与光泽感。提示：在美国法规下，此色含有未获 FDA 批准用于眼周的色料。",
    "All over solid tone for all skin types. Base tone, as well as midtone for eyeshadow depth and dimension. Also can be used in brows, and as contour.": "适合所有肤色的大面积实色铺陈；可作底色或中间色调，增强眼影深度与立体感；也可用于眉部与修容。",
    "All over tone for all skin types, use as a soft eyeliner for light to medium tones.": "适合所有肤色的大面积铺色；可作为浅至中等肤色的柔和眼线。",
    "Use this citron champagne shade as an all-over lid colour, to highlight the brow bone and inner corners of the eyes, or in the center of the eyes for a burst of luminosity. Wear with shades ‘Nacre Blanche’ and ‘Abricot Givré’ for a softly luminous look, touched with patisserie warmth. Apply with a brush for your desired level of intensity.": "可作全眼铺色，用于眉骨和眼头提亮，或点在眼中位置增强光感。与 `Nacre Blanche` 和 `Abricot Givré` 搭配，可呈现带法式甜点暖意的柔亮妆效。可用刷具按需叠加显色度。",
    "Use this soft pearl crème shade as an all-over lid colour, to highlight the brow bone and inner corners of the eyes, or as an adjustor tone above or below complementary shades. Wear with shades ‘Fleur d’Or’ and ‘Abricot Sauvage’ for a soft, peach-lit eye, kissed by French morning light. Apply with a brush for your desired level of intensity.": "可作全眼铺色，用于眉骨和眼头提亮，或作为互补色上下方的调和色。与 `Fleur d’Or` 和 `Abricot Sauvage` 搭配，可营造法式晨光轻吻般的柔和蜜桃眼妆。可用刷具按需叠加显色度。",
    "This nude light pink shade can be used as an all-over lid colour, to highlight the brow bone and inner corners of the eyes, or as an adjustor tone above or below complementary shades. Pair with shades ‘Nougatine’ and ‘Bois d’Ambre’ for a rosewood nude eye look, reminiscent of diffused Parisian light at dusk. Apply with a brush for your desired level of intensity.": "可作全眼铺色，用于眉骨和眼头提亮，或作为互补色上下方的调和色。与 `Nougatine` 和 `Bois d’Ambre` 搭配，可呈现暮色巴黎般柔散光线中的玫瑰木裸妆感。可用刷具按需叠加显色度。",
    "This light, taupe fawn brown shade can be used as an all-over lid colour, as a base tone beneath complementary shades, or as a transitional shade to build soft depth and dimension. Pair with shades ‘Nectar Brûlé’ and ‘Cacao Serein’ for a decadent trio of cocoa-dusted browns, silken, and richly indulgent. Apply with a brush for your desired level of intensity.": "可作全眼铺色、互补色下方的打底色，或作为过渡色叠出柔和深度与层次。与 `Nectar Brûlé` 和 `Cacao Serein` 搭配，可组成丝滑浓郁的可可棕三重奏。可用刷具按需叠加显色度。",
    "This soft, beige-pink crème shade can be used as an all-over lid colour, to highlight the brow bone and inner corners of the eyes, or as an adjustor tone above or below complementary shades. It can also be used as a blush on light to medium complexions. Pair with shades ‘Abricot Sauvage’ and ‘Abricot Doré’ for a sumptuous trio of peach tones, soft-matte and gently glazed. Apply with a brush for your desired level of intensity.": "可作全眼铺色，用于眉骨和眼头提亮，或作为互补色上下方的调和色；浅至中等肤色也可作腮红使用。与 `Abricot Sauvage` 和 `Abricot Doré` 搭配，可呈现柔雾又微釉感的丰润蜜桃色调。可用刷具按需叠加显色度。",
    "This nude rose quartz shade can be used as an all-over lid colour, placed at the center of the lid for a touch of luminosity, or worn in the inner corners of the eyes for a kiss of brightness. For a high-shine, foiled effect, use with a mixing medium or add to gloss for a dewy, glistening finish. Wear with shades ‘Abricot Sauvage’ and ‘Bois d’Ambre’ for a shimmering velvet peach, second-skin effect.": "可作全眼铺色，点在眼皮中央增强光感，或用于眼头提亮。搭配调和液可获得更强烈的箔光效果，也可混入唇蜜带出水润闪泽。与 `Abricot Sauvage` 和 `Bois d’Ambre` 搭配，可呈现带天鹅绒质感的贴肤蜜桃微闪效果。",
    "This soft, sugared peach shade can be used as an all-over lid colour, to highlight the brow bone and inner corners of the eyes, as a blush on light to medium complexions, or as a highlighter on medium to deep complexions. Pair with shades ‘Abricotine Fraîche’ and ‘Fleur d’Or’ for a decadent look with brûléed peach warmth. Apply with a brush for your desired level of intensity.": "可作全眼铺色，用于眉骨和眼头提亮；浅至中等肤色可作腮红，中等至深肤色可作高光。与 `Abricotine Fraîche` 和 `Fleur d’Or` 搭配，可呈现焦糖蜜桃般的丰润暖感。可用刷具按需叠加显色度。",
    "This duochromatic rosewood shade can be worn alone for a wash of brilliant luminosity or layered over complementary tones to accentuate its duochromatic dimension. For a high-shine, foiled effect, use with a mixing medium. It can also be mixed with a gloss for a wet, prismatic look or used as a highlighter. Pair with shades “Abricot Givré” and “Lune de Miel” for a tantalizing glaze of sugared sweetness. Apply with a brush for your desired level of intensity.": "可单独使用呈现明亮光泽，也可叠加在互补色上强化双偏光层次。搭配调和液可获得更强烈的箔光效果，也可与唇蜜混合营造湿润棱彩感，或作高光使用。与 `Abricot Givré` 和 `Lune de Miel` 搭配，可带出糖釉般诱人的甜润光感。可用刷具按需叠加显色度。",
    "This honeyed bronze shade can be used as an all-over lid colour, to build depth and dimension in the outer corners of the eyes, or as an eyeliner on all complexions. Use with a mixing medium for a foiled effect. Wear with shades ‘Cacao Serein’ and ‘Ganache Noire’ for a shimmering caramelized look, refined with pâtisserie richness. Apply with a brush for your desired level of intensity.": "可作全眼铺色，用于眼尾加深层次，也适合所有肤色作眼线色。搭配调和液可获得箔光效果。与 `Cacao Serein` 和 `Ganache Noire` 搭配，可呈现带法式甜点浓郁感的焦糖微闪妆效。可用刷具按需叠加显色度。",
    "This iced apricot shade can be used as an all-over lid colour, to highlight the brow bone and inner corners of the eyes, as a blush on light to medium complexions, or as a highlighter on medium to deep complexions. Use with a mixing medium for a foiled effect or mix into gloss for a luminous sheen. Pair with shades ‘Abricotine Fraîche’ and ‘Abricot Givré’ for a glacé peach look, cool and softly luminous. Apply with a brush for your desired level of intensity.": "可作全眼铺色，用于眉骨和眼头提亮；浅至中等肤色可作腮红，中等至深肤色可作高光。搭配调和液可获得箔光效果，也可混入唇蜜增添明亮釉泽。与 `Abricotine Fraîche` 和 `Abricot Givré` 搭配，可呈现清凉柔亮的冰蜜桃妆感。可用刷具按需叠加显色度。",
    "This midtone brown-plum shade can be used as an all over lid colour, as a transition shade to build out the crease and socket, as a soft liner, or as a base tone beneath complementary tones for increased depth and saturation. Pair with shades ‘Nectar Brûlé’ and ‘Ganache Noire’ for a rich and sumptuous look inspired by the indulgence of a chocolate ganache dessert. Apply with a brush for your desired level of intensity.": "可作全眼铺色、眼窝过渡色、柔和眼线色，或作为互补色下方的打底加深色，增强深度与饱和度。与 `Nectar Brûlé` 和 `Ganache Noire` 搭配，可呈现如巧克力甘纳许甜点般浓郁丰厚的妆效。可用刷具按需叠加显色度。",
    "This dark cocoa-brown shade can be used to create depth and dimension in the crease, socket, and lash line. Build up the colour in the outer corners of the eyes for a boldly pigmented finish or use with a mixing medium and liner brush for a graphic finish. Pairs perfectly with ‘Nougatine’ and ‘Bois d’Ambre’ for a richly pigmented, duochromatic look. Use a brush for your desired level of intensity.": "适合用于眼窝、轮廓和睫毛根部加深，增强深邃度与立体感。可在眼尾逐步叠加做出高显色效果，也可搭配调和液和眼线刷完成更利落的图形眼线。与 `Nougatine` 和 `Bois d’Ambre` 搭配，可呈现高显色的双偏光深邃妆感。可用刷具按需叠加显色度。",
    "Use this dusty mauve shade as an all-over lid color on all complexions, in the crease and outer corners of the eyes as a transitional mid-tone hue, or a neutral base beneath complementary tones. Can also be used as a blush tone on light to medium complexions. Apply with a brush for your desired level of intensity. Pair with shades ‘Aube’ and ‘Nocturne’ for a rose-toned reverie.": "可作全眼铺色，用于眼窝与眼尾作为中间过渡色，或作为互补色下方的中性色打底；浅至中等肤色也可作腮红。可用刷具按需叠加显色度。与 `Aube` 和 `Nocturne` 搭配，可呈现柔雾玫瑰调妆感。",
    "Use this cool light beige tone as an all-over lid color on all complexions, in the crease and outer corners of the eyes as a transitional mid-tone hue, or a neutral base beneath complementary tones. Apply with a brush for your desired level of intensity. Wear with shades ‘Veillée’ and ‘Nocturne’ for a soft-sculpted, naturally defined look.": "可作全眼铺色，用于眼窝与眼尾作为过渡中间色，或作为互补色下方的中性色打底。可用刷具按需叠加显色度。与 `Veillée` 和 `Nocturne` 搭配，可打造柔和自然的轮廓眼妆。",
    "Use this cool grey taupe shade as an all-over lid color on all complexions, in the crease as a transitional crease shade, or to build out depth and dimension in the outer corners of the eyes. Can be used as a soft eyeliner on all skin tones, in the brows and hairline, or as a subtle contour shade on light to medium complexions. Apply with a brush for your desired level of intensity. Wear as a base tone beneath shades ‘Étoilée’ and ‘Envoûté’ for smoldering depth and drama.": "可作全眼铺色、眼窝过渡色，或用于眼尾叠出深度与立体感。适合所有肤色作柔和眼线，也可用于眉部、发际线；浅至中等肤色还可作自然修容。可用刷具按需叠加显色度。叠在 `Étoilée` 和 `Envoûté` 下方，可强化深邃烟熏感。",
    "Use this midtone neutral beige shade as an all-over lid color on all complexions, in the crease and outer corners of the eyes as a transitional crease shade, or to build out depth and dimension in the outer corners of the eyes. Can be used in the brows, hairline, or as a contour shade on light to medium complexions. Apply with a brush for your desired level of intensity. Pairs perfectly with shades ‘Séléné’ and ‘Étoilée’ for a seamless, effortlessly elevated eye look.": "可作全眼铺色，用于眼窝与眼尾作为过渡色，或叠出柔和层次。也可用于眉部、发际线，浅至中等肤色还可作修容。可用刷具按需叠加显色度。与 `Séléné` 和 `Étoilée` 搭配，可完成自然衔接的精致眼妆。",
    "Wear this burgundy rose shade alone for a striking monochromatic glow, or layer over deeper tones for a veil of rose-lit shimmer. Can also be used as liner or worn as a shimmering blush on medium to deep complexions. Apply with a brush for your desired level of intensity. Blend with shades ‘Éther’ and ‘Nocturne’ to sculpt a multi-dimensional, rich, and rosy look.": "可单独使用打造吸睛单色光泽，也可叠加在深色之上，罩出玫瑰微闪层次。中等至深肤色可作微闪腮红，也可作眼线色。可用刷具按需叠加显色度。与 `Éther` 和 `Nocturne` 搭配，可塑造浓郁立体的玫瑰调妆感。",
    "Wear this champagne rose shade as an all-over lid color on all complexions or layered over complementary tones for a refined wash of reflectivity. Can also be used as a highlighter in the center of the lids or to brighten the inner corners of the eyes. Use this shade with a mixing medium for a foiled effect. Apply with a brush for your desired level of intensity. Pair with shades ‘Séléné’ and ‘Nuit’ for a blackberry-mauve look kissed by twilight’s final glow.": "可作全眼铺色，或叠加在互补色之上，带出细腻反光层次；也可点在眼皮中央或眼头提亮。搭配调和液可获得箔光效果。可用刷具按需叠加显色度。与 `Séléné` 和 `Nuit` 搭配，可呈现暮光亲吻般的黑莓豆沙妆感。",
    "Use this violet duochromatic shade as an all-over lid colour, layered over complementary tones for a high-impact reflective finish, or blended with deeper shades to create a sultry, smoldering effect. Can be used as a liner or with a mixing medium for a foiled appearance. Apply with a brush for your desired level of intensity. Blend with ‘Éther’ and ‘Nuit’ for a multi-chrome, smoked blackberry look with a prismatic shift.": "可作全眼铺色，或叠加在互补色上，打造高冲击反光效果；与深色晕染则能呈现魅惑烟熏感。可作眼线色，也可搭配调和液获得箔光质感。可用刷具按需叠加显色度。与 `Éther` 和 `Nuit` 搭配，可做出带棱彩偏光的黑莓烟熏妆效。",
    "This deep gunmetal brown shade can be used as an all-over lid colour, layered over complementary tones for a reflective finish, or blended with deeper shades to create a smokey, seductive effect. Use this shade with a mixing medium for a foiled appearance. Apply with a brush for your desired level of intensity. Pair with shades “Éther” and “Envoûté” for a soft smokescape in twilight taupe.": "可作全眼铺色，或叠加在互补色之上加强反光，也可与更深色晕染出深邃烟熏效果。搭配调和液可获得箔光质感。可用刷具按需叠加显色度。与 `Éther` 和 `Envoûté` 搭配，可呈现暮色灰棕调的柔烟妆感。",
    "Use this matte steel blue as an all-over lid color, as a richly saturated base beneath complementary tones, or to define the outer corners of the eyes for a cool-toned smokey look. Can also be worn as a bold, graphic liner. Apply with a brush for your desired level of intensity. Pair with shades ‘Séléné’ and ‘Noctis’ for a luminous look evocative of a midnight lagoon.": "可作全眼铺色，或作为互补色下方的高饱和打底色，也可用于眼尾勾勒冷调烟熏轮廓。也适合画出利落图形眼线。可用刷具按需叠加显色度。与 `Séléné` 和 `Noctis` 搭配，可呈现午夜泻湖般的冷光妆感。",
    "Use this smoked blackberry as an all-over lid, as a richly saturated base beneath complementary tones, or to define the outer corners of the eyes for a cool-toned smokey look. Can also be worn as a bold, graphic liner. Apply with a brush for your desired level of intensity. Layer with shades ‘Nocturne’ and “Lunaire”’ for a violet veil of shimmer, smoke, and celestial elegance.": "可作全眼铺色，或作为互补色下方的高饱和打底色，也可用于眼尾勾勒冷调烟熏层次。也适合画出利落图形眼线。可用刷具按需叠加显色度。叠加 `Nocturne` 和 `Lunaire`，可营造紫调微闪与烟雾交织的星夜妆感。",
    "Use this deep grey metallic shade as an all-over lid color, layered over complementary tones for dimensional depth, or in the outer corners of the eyes to line and define. Can also be used with a mixing medium for a foiled effect. Apply with a brush for your desired level of intensity. Layer over shade ‘Veillée’ and blend with shade ‘Envoûté’ to create a steel-toned smokey eye with dramatic depth.": "可作全眼铺色，或叠加在互补色之上增强立体深度，也可用于眼尾与睫毛根部勾勒轮廓。搭配调和液可获得箔光效果。可用刷具按需叠加显色度。叠在 `Veillée` 上并与 `Envoûté` 晕染，可做出钢感烟熏妆效。",
    "Use this deep espresso brown shade as an all-over lid color for all complexions, a transitional crease shade, or to build out depth and dimension in the outer corners of the eyes. This shade can be used to create a deep smokey eye all over the lid, as eyeliner, or to fill in brows and hairlines on complementary hair tones. Can be layered with mattes and shimmers for a multitude of different looks. Apply with a brush for your desired level of intensity. Pair with shades ‘Rêve’ and ‘Noctis’ for a cool-toned, gunmetal gaze where steel meets shadow.": "可作全眼铺色、眼窝过渡色，或用于眼尾加深立体感。也适合铺满眼皮打造深烟熏效果，或作眼线、眉部与发际线修饰。可与哑光和珠光色叠搭，延展出多种妆效。可用刷具按需叠加显色度。与 `Rêve` 和 `Noctis` 搭配，可完成冷调枪灰感的深邃眼妆。",
    "Use this light, cool-toned nude pink as an all-over lid colour on all complexions, in the crease of the eyes as a transitional hue, or as a light base beneath complementary tones. Apply with a brush for your desired level of intensity. Pair with shades ‘Violetine’ and ‘Chimère’ for a crystalline kiss of twilight radiance.": "可作全眼铺色、眼窝过渡色，或作为互补色下方的浅色打底。可用刷具按需叠加显色度。与 `Violetine` 和 `Chimère` 搭配，可呈现暮光亲吻般的晶透微光。",
    "This light, blush matte pink shade can be used as an all-over lid colour, a base tone beneath complementary tones, or to highlight the brow bone. Apply with a brush for your desired level of intensity. Pair with shades ‘Iantha’ and ‘Fleur de Nuit’ for a softly smoked veil of ash and umber.": "可作全眼铺色、互补色下方的打底色，或用于眉骨提亮。可用刷具按需叠加显色度。与 `Iantha` 和 `Fleur de Nuit` 搭配，可呈现柔和烟雾感的灰紫棕妆效。",
    "Use this white, purple-pink duochromatic shade as a luminous lid topper, radiant inner-corner accent, highlight on the high points of the face, or a light-catching gleam at the center of the eye. Use this shade with a mixing medium for a foiled effect, as a liner, or with a swirl of gloss for the perfect pearlized sheen. Apply with a brush for your desired level of intensity. Pair with shades ‘Serpentine’ and ‘Gris Fumé’ for an amethyst prism of shifting luminosity.": "可作眼皮提亮叠擦色、眼头点亮色、面部高光，或点在眼皮中央增强聚光感。搭配调和液可获得箔光效果，也可作眼线，或混入唇蜜做出珍珠般光泽。可用刷具按需叠加显色度。与 `Serpentine` 和 `Gris Fumé` 搭配，可呈现紫水晶棱镜般的变幻光感。",
    "This mid-tone, matte, greige shade can be used as an all-over lid colour, a transitional shade to build out the crease and socket, a soft liner, or as a base tone beneath complementary tones. Apply with a brush for your desired level of intensity. Blend with shades ‘Iantha’ and ‘Gris Fumé’ for a grungy, greige haze of violet ash.": "可作全眼铺色、眼窝过渡色、柔和眼线色，或作为互补色下方的打底色。可用刷具按需叠加显色度。与 `Iantha` 和 `Gris Fumé` 搭配，可做出带紫灰调的颓感烟雾妆。",
    "Use this cool, mid-tone taupe brown as an all-over lid colour on all complexions, blend through the crease as a seamless transition, or deepen at the outer corners to sculpt depth and dimension. It can also be used in the brows, hairline, or as a contour shade on light to medium complexions. Apply with a brush for your desired level of intensity. Blend with shades ‘Silène Noctiflore’ and ‘Mûre Sauvage’ for a smoldering plume of midnight plum.": "可作全眼铺色，在眼窝自然晕染作过渡色，或叠加在眼尾加强深度与立体感。也可用于眉部、发际线，浅至中等肤色还可作修容。可用刷具按需叠加显色度。与 `Silène Noctiflore` 和 `Mûre Sauvage` 搭配，可呈现午夜李子色般的深邃烟熏感。",
    "Use this light purple duochromatic shade as an all-over lid colour on all complexions, layered over complementary shades as a reflective topper, as a radiant inner-corner accent, or for a radiant highlight in the center of the eye. Use this shade with a mixing medium for a foiled effect, as a liner, or with a swirl of gloss for a prismatic, opalescent finish. Apply with a brush for your desired level of intensity. Pair with shades ‘Chimère’ and ‘Nocturna’ for a high-contrast duochromatic play of shadow and light.": "可作全眼铺色，或叠加在互补色之上作为反光提亮层，也可用于眼头或眼皮中央增强光感。搭配调和液可获得箔光效果，也可作眼线，或混入唇蜜营造棱彩蛋白石光泽。可用刷具按需叠加显色度。与 `Chimère` 和 `Nocturna` 搭配，可呈现高对比的明暗偏光效果。",
    "Use this mid-tone dusty cool-toned purple as an all-over lid colour on all complexions, as a transitional shade in the crease of the sockets, or beneath complementary tones to amplify color intensity. Apply with a brush for your desired level of intensity. Blend with shades ‘Fleur de Nuit’ and ‘Mûre Sauvage’ for a velvet veil of aubergine allure.": "可作全眼铺色、眼窝过渡色，或作为互补色下方的打底色以增强显色。可用刷具按需叠加显色度。与 `Fleur de Nuit` 和 `Mûre Sauvage` 搭配，可营造带天鹅绒质感的茄紫妆效。",
    "Use this midtone taupe brown shade as an all-over lid color on all complexions, in the crease and outer corners of the eyes as a transitional shade, or to build depth and dimension in the outer corners of the eyes. It can also be used in the brows, hairline, or as a contour shade on light to medium complexions. Apply with a brush for your desired level of intensity. Combine with shades ‘Astraea’ and ‘Mûre Sauvage’ for a shadowed shroud of violet umber.": "可作全眼铺色、眼窝与眼尾的过渡色，或用于叠出深度与立体感。也可用于眉部、发际线，浅至中等肤色还可作修容。可用刷具按需叠加显色度。与 `Astraea` 和 `Mûre Sauvage` 搭配，可呈现紫棕阴影般的深沉层次。",
    "Use this shimmering taupe-brown purple as an all-over lid colour on all complexions, layered over complementary tones for dimensional depth, or in the outer corners of the eyes to line and define. Can also be used with a mixing medium for a foiled effect. Apply with a brush for your desired level of intensity. Layer over shade ‘Cendrée’ and blend with shade ‘Nocturna’ for a shimmering veil of obsidian smoke.": "可作全眼铺色，或叠加在互补色之上增强立体深度，也可用于眼尾与睫毛根部勾勒轮廓。搭配调和液可获得箔光效果。可用刷具按需叠加显色度。叠在 `Cendrée` 上并与 `Nocturna` 晕染，可做出黑曜烟雾般的闪耀层次。",
    "Use this light, muted lavender shade as an all-over lid colour on all complexions or as a base colour beneath complementary shades. Apply with a brush for your desired level of intensity.": "可作全眼铺色，或作为互补色下方的打底色。可用刷具按需叠加显色度。",
    "Use this light, muted lavender shade as an all-over lid colour on all complexions or as a base colour beneath complementary shades. Apply with a brush for your desired level of intensity. Blend with shades ‘Plume’ and ‘Violetine’ for a specter of luminous lavender light.": "可作全眼铺色，或作为互补色下方的打底色。可用刷具按需叠加显色度。与 `Plume` 和 `Violetine` 搭配，可呈现发光般的柔雾薰衣草妆感。",
    "This mid-tone, cool-toned cacao taupe shade can be used as an all-over lid colour, to build depth and dimension in the outer corners of the eyes, or as a liner to add definition to the lash line. Apply with a brush for your desired level of intensity. Pair with shades ‘Cendrée’ and ‘Nocturna‘ to create a smokescape of sultry depth.": "可作全眼铺色，用于眼尾加深立体感，或作眼线色勾勒睫毛根部。可用刷具按需叠加显色度。与 `Cendrée` 和 `Nocturna` 搭配，可营造深邃魅惑的烟熏妆感。",
    "Use this deep elderberry matte as an all-over lid colour for dramatic depth, as a base tone to accentuate lighter hues, or to create dimension in the socket and outer corners of the eyes. It can also be used as a liner or worn as a contour color on deep complexions. Wear with shades ‘Serpentine’ and ‘Mûre Sauvage’ for a chiaroscuro of plum-lit shimmer and shadow.": "可作全眼铺色打造戏剧化深度，也可作为打底色衬托浅色，或用于眼窝与眼尾塑造立体层次。也可作眼线色，深肤色还可作修容。与 `Serpentine` 和 `Mûre Sauvage` 搭配，可呈现李子色微光与阴影交织的明暗妆效。",
    "Sweep across the lid for a delicate wash of colour, blend through the crease as a transitional tone, or use as a brightening base. Apply with a brush for your desired intensity. Pair with ‘Orchidée’ and ‘Opaline’ for a romantic wash of prismatic pink luminosity.": "可作全眼轻扫铺色、眼窝过渡色，或作为提亮打底色。可用刷具按需叠加显色度。与 `Orchidée` 和 `Opaline` 搭配，可呈现浪漫的棱彩粉光感。",
    "Sweep across the lid for a radiant wash of colour or tap onto the centre of the lid to brighten and enhance dimension. Doubles as a highlight for inner corners or beneath the brow bone. Wear with ‘Pétaline‘ and ‘Améthyste‘ for a petal-soft whisper of rose satin.": "可全眼铺色，或点在眼皮中央提亮并增强立体感；也可用于眼头或眉骨提亮。与 `Pétaline` 和 `Améthyste` 搭配，可呈现花瓣般柔和的玫瑰缎光妆效。",
    "Sweep across the lid for soft warmth and dimension, or blend onto the outer lid to sculpt and define. Use with a mixing medium for a foiled effect. Pairs with ‘Taupeline‘ and ‘Charoïte‘ for a sculptural balance of bronze and stone.": "可全眼铺色，带出柔和暖感与层次，也可晕染在眼尾塑造立体轮廓。搭配调和液可获得箔光效果。与 `Taupeline` 和 `Charoïte` 搭配，可呈现古铜与石灰调平衡的雕塑感妆效。",
    "Blend through the crease to create natural shadow and dimension, or diffuse along the outer lid to ground lighter tones. Wear with Pétaline and Charoïte for subtle structure in a softly balanced matte trio.": "可晕染在眼窝打造自然阴影与立体感，也可铺在眼尾压住浅色，使配色更稳。与 `Pétaline` 和 `Charoïte` 搭配，可完成柔和平衡的哑光三色层次。",
    "Use as an all-over lid colour on all complexions or as a base beneath complementary shades. Blend with ‘Opaline‘ and ‘Prisme‘ for a luminous bouquet of lilac light.": "可作全眼铺色，适合所有肤色，也可作为互补色下方的打底色。与 `Opaline` 和 `Prisme` 搭配，可呈现明亮的丁香花束般光感。",
    "Sweep across the lid for rich dimension, or press along the outer lid and lash line to deepen and define the eye. Use with a mixing medium for a foiled effect. Blend with ‘Ipomée‘ and ‘Prisme‘ for a highly-pigmented purple prismatic pairing.": "可全眼铺色打造浓郁层次，也可压在眼尾和睫毛根部加深轮廓。搭配调和液可获得箔光效果。与 `Ipomée` 和 `Prisme` 搭配，可呈现高显色的紫调棱彩妆效。",
    "Tap over matte or satin shades to create a dimensional prismatic finish. Apply with a fingertip for maximum shine or sweep lightly with a brush for a soft, diffused effect. Use with a mixing medium for a foiled finish. Pair with ‘Améthyste‘ and ‘Prisme‘ for refined reflective depth.": "可叠擦在哑光或缎光色之上，营造立体棱彩效果。用指腹可获得更强闪泽，刷具轻扫则更柔和雾化。搭配调和液可获得箔光妆效。与 `Améthyste` 和 `Prisme` 搭配，可带出细腻的反光深度。",
    "Sweep all over the lid for a vibrant flash of reflective colour, or tap onto the centre to amplify dimension and sparkle. Use with a mixing medium for a foiled finish. Wear with ‘Pétaline‘ and ‘Orchidée‘ for a soft bloom of shimmering pinks.": "可全眼铺色，呈现鲜明反光色彩，也可点在眼皮中央增强层次与闪耀感。搭配调和液可获得箔光妆效。与 `Pétaline` 和 `Orchidée` 搭配，可做出柔和盛放的粉紫微闪妆感。",
    "Sweep across the lid for a softly reflective finish, or blend and build through the crease and lash line for shimmering depth. Use with a mixing medium for a foiled finish. Pairs with ‘Sureau‘ and ‘Charoïte‘ for a softly smouldering kiss of shimmer and shadow.": "可全眼铺色，呈现柔和反光，也可叠加在眼窝和睫毛根部营造闪耀深度。搭配调和液可获得箔光妆效。与 `Sureau` 和 `Charoïte` 搭配，可呈现柔雾微熏的光影层次。",
    "Use as an all-over base, to sculpt the crease and outer corners, or as a softly diffused liner. Layer beneath reflective shades to deepen and intensify a smoky look. Blend with ‘Violine‘ and ‘Prunelle‘ for a sultry smoked violet.": "可作全眼打底色、眼窝与眼尾塑形色，或作为柔雾眼线色。叠在反光色下方可加深并强化烟熏效果。与 `Violine` 和 `Prunelle` 搭配，可呈现魅惑烟熏紫妆感。",
    "Define the crease, deepen the outer corners, or softly contour the eye for natural-looking depth. Blend with ‘Prisme‘ and ‘Prunelle‘ for a softly shadowed mauve-plum eye.": "可用于勾勒眼窝、加深眼尾，或柔和修饰眼部轮廓，打造自然深度。与 `Prisme` 和 `Prunelle` 搭配，可呈现柔雾阴影感的豆沙李子妆效。",
    "Sweep across the lid for dramatic depth, blend into the crease and outer corners to sculpt dimension, or use as a softly diffused liner. Can also be worn as a contour on deeper complexions. Wear with ‘Violine‘ and ‘Opaline‘ for plum-lit shimmer and shadow.": "可全眼铺色打造戏剧化深度，也可晕染在眼窝与眼尾塑造立体层次，或作为柔雾眼线色。深肤色也可作修容。与 `Violine` 和 `Opaline` 搭配，可呈现李子色微光与阴影交织的妆效。",
    "This light blush pink shade can be used as an all-over lid colour or as a base tone beneath complementary tones, it can be used to highlight the brow bone. It can be mixed with any of the other tones to brighten and lighten to create over 12 new hues. Apply with fingertips or a dense brush for your desired level of intensity.": "可作全眼铺色，或作为互补色下方的打底色，也可用于眉骨提亮。还能与盘中其他颜色混合，提亮并调浅，延展出 12 种以上新色。可用指腹或扎实刷具按需叠加显色度。",
    "This high-shine, pink champagne shade can be used as an all-over base tone or layered over complementary tones for a refined wash of reflectivity. Combine with a mixing medium for an ultra-foiled effect. This shade can also be mixed into gloss to add a kiss of brilliance to any lip look.": "可作全眼打底色，或叠加在互补色之上，带出细腻反光层次。搭配调和液可获得更强烈的箔光效果，也可混入唇蜜，为唇妆增添一抹亮泽。",
    "This soft light pink shade can be used as an all-over lid colour or as a base tone beneath complementary shades. It can also be used to highlight the brow bone and inner corners of the eyes. Additionally, it can be mixed with any of the other tones to brighten, lighten to create over 12 new hues.": "可作全眼铺色，或作为互补色下方的打底色。也可用于眉骨和眼头提亮。还能与盘中其他颜色混合，提亮并调浅，延展出 12 种以上新色。",
    "This light stone-brown nude shade can be used as an all-over lid colour, as a transitional shade to build out the crease and socket, as a soft liner, or as a base tone beneath complementary tones for increased depth and saturation. Can also be used in brows on light complexions.": "可作全眼铺色、眼窝过渡色、柔和眼线色，或作为互补色下方的打底色以增强深度与饱和度。浅肤色也可用于眉部修饰。",
    "On light skin tones, this is a taupe, on darker skin tones, this is a grey. Use it on the lid or in the crease.": "在浅肤色上呈现灰褐调，在深肤色上则更偏灰色。可用于眼皮主色或眼窝过渡色。",
    "All over the lid for a flash of shine, or layer it over a matte color to intensify both. For maximum reflection, use a damp brush.": "可全眼铺色，带来一抹闪耀光感，也可叠加在哑光色上，同时增强两者表现。想要最大反光效果，建议使用微湿刷具。",
    "This metallic duochromatic shade can be used as an all-over lid color for all complexions or layer it over any of the matte shades as a topper. This shade can be lightened with any pale satin shimmer tones to create four new shades! All skin tones.": "可作全眼铺色，适合所有肤色，也可叠加在任一哑光色之上作为提亮层。还可与浅色缎光珠光混合，延展出更多新色变化。",
    "Lid to lash base color, to brighten up the inner corner of the eye, and to highlight on the face - try using it on top of the cheekbone, down the nose, and along the jawline.": "可作从眼皮到睫毛根部的打底色，也适合提亮眼头和面部高点，可尝试用于颧骨、鼻梁和下颌线位置。",
    "This shade can be used as an all-over lid tone. Mix with “Beaubourg” or “Archives” for increased depth and luminosity! Can also be worn as blush on light complexions! Mix with any shimmer for a new hue!": "可作全眼铺色。与 `Beaubourg` 或 `Archives` 混合，可增强深度与光泽感；浅肤色也可作腮红使用；再与任意珠光色混合，还能延展出新的色调变化。",
    "This midtone burnished bronze shade can be used as an all-over base colour, layered over complementary tones for additional warmth and dimension, or used as a liner for subtle definition. Can also be worn as a highlighter on medium to deep skin tones. Apply with a dense brush for your desired level of intensity. Use with the Viseart Seamless Eye Primer or other preferred mixing medium for a foiled effect.": "可作全眼打底色，或叠加在互补色之上增加暖感与层次，也可作为眼线色带出柔和轮廓。中等至深肤色也可作高光使用。可用扎实刷具按需叠加显色度；搭配 Viseart Seamless Eye Primer 或其他调和液可获得箔光效果。",
    "This midtone shade can be used as an all-over lid colour, as a transition shade to build out the crease and socket, as a soft liner, or as a base tone beneath complementary tones for increased depth and saturation. Can be used in brows. Mix this hue with other matte shades to create 12 new shades. Apply with fingertips or a dense brush for your desired level of intensity.": "可作全眼铺色、眼窝过渡色、柔和眼线色，或作为互补色下方的打底色以增强深度与饱和度。也可用于眉部修饰。与其他哑光色混合，可延展出 12 种新色。可用指腹或扎实刷具按需叠加显色度。",
    "This espresso matte is used to create a deep, smokey eye all over the lid and as an eyeliner with a damp brush. Hue can be tapped with a brush in brows and muted down with other matte tones for darker to lighter brows, depending on skin tone. Can be layered with all shimmers for a multitude of different looks.": "适合全眼铺色打造深邃烟熏感，也可配合微湿刷具作为眼线色使用。也可轻拍于眉部，并与其他哑光色混合，调出适合不同肤色的深浅眉色；与所有珠光色叠搭也能延展出多种妆效。",
    "Apply a sweep of this hue with a brush or finger for a sexy 'wet skin' effect or pair with any of the other shades in the palette for a glamorous golden finish. Can also be foiled or worn as a highlighter on all complexions.": "可用刷具或指腹扫在眼皮上，打造带光泽的湿润妆感；也可与盘中其他色号搭配，呈现华丽金光效果。还可搭配调和液增强箔光感，或作为适合所有肤色的高光使用。",
    "Use this warm cream shade all over as a base tone on light to medium skin tones. Can be used to brighten the inner corners of the eyes on all complexions. Can also be used to set under-eye concealer on light to medium complexions.": "浅至中等肤色可作全眼打底色；所有肤色都可用于眼头提亮。浅至中等肤色也可用于定妆眼下遮瑕。",
    "This midtone shade can be used as an all over lid colour, as a transition shade to build out the crease and socket, as a soft liner, or as a base tone beneath complementary tones for increased depth and saturation on all complexions. Mix this hue with other matte shades to create 12 new shades. Apply with fingertips or a dense brush for your desired level of intensity.": "可作全眼铺色、眼窝过渡色、柔和眼线色，或作为互补色下方的打底色，以增强深度与饱和度，适合所有肤色。与其他哑光色混合，可延展出 12 种新色。可用指腹或扎实刷具按需叠加显色度。",
    "Use this to brighten the lid or inner corner, or use a damp brush to intensify the metallic tone. This can be used as a highlighter as well for a golden glow.": "可用于提亮眼皮或眼头；搭配微湿刷具可增强金属光泽。也可作为高光，带出金色光感。",
    "All over solid tone for all skin types. Base tone, as well as midtone for eyeshadow depth and dimension. Also can be used in brows, and as a contour.": "适合所有肤色大面积铺色；既可作打底色，也可作为增强眼影深度与立体感的中间色调；同时也可用于眉部与修容。",
    "This rose gold duochromatic hue is used as an all-over lid tone. It can also be mixed with other matte and shimmer hues to create more defined, richly toned shades and used with lighter metallic tones to create a duochromatic look. Use a mixing medium to foil this hue for ultimate shine, or create a mix of hues- can also be used with a damp brush all over lid, or as an eyeliner.": "可作全眼铺色，也可与其他哑光或珠光色混合，调出更浓郁、更有层次的色调；与更浅的金属色搭配，还能做出双偏光效果。搭配调和液可获得更强烈的箔光感，也可用微湿刷具全眼上色或当眼线使用。",
    "This satin shade can be used as an all-over lid tone, as a highlight in the inner corner of the eyes, on the brow bone, and on top of any cream eyeliner, or conversely use a wet brush, or mixing medium to intensify the tone for high definition shine. All skin tones.": "可作全眼铺色，也可用于眼头、眉骨提亮，或叠加在膏状眼线之上。使用微湿刷具或调和液可增强光泽与显色，适合所有肤色。",
    "Use this golden bronze hue as an all-over lid color on all complexions or tap onto the center of the lid for an eye-catching finish. Can be foiled or worn as liner.": "可作全眼铺色，适合所有肤色；也可点在眼皮中央，打造吸睛亮点。可搭配调和液做出箔光效果，也可作为眼线色。",
    "Use this metallic copper as an all-over lid color or layered over your favorite matte or shimmer shades for additional intensity. Tap onto the center of the lid for a pop of color. Can be foiled or worn as liner. Try pairing with shade 'Cabaret' for a warm, smokey finish.": "可作全眼铺色，也可叠加在喜爱的哑光或珠光色之上增强强度。点在眼皮中央可带来更鲜明的亮点；可搭配调和液做出箔光效果，也可作为眼线色。与 `Cabaret` 搭配，可完成温暖的烟熏妆效。",
    "This shade can be used as a wash of color all over the lid, layered over your favorite matte shades- can be used in the inner corners for a pop of luminosity, in the center of the eyelid to accentuate the glow or as a highlighter on tops of the cheekbones, add to the cupids bow and into any lipgloss to add a pearl! Additionally, foil this shade for all day wear with a mixing medium or damp brush to intensify the hue.": "可全眼铺色，或叠加在喜欢的哑光色上；也适合用于眼头提亮、点亮眼皮中央，或作为颧骨高光，还可点在唇峰，甚至混入唇蜜增添珍珠光泽。搭配调和液或微湿刷具可增强显色并获得更持久的箔光效果。",
    "Can be blended all over the lid or in the crease. Smudge it over a darker pencil for a soft smokey eye, or push it into the lash line for subtle definition.": "可用于全眼铺色或眼窝过渡。叠在更深色眼线笔上可做出柔和烟熏感，也可压在睫毛根部带出细致轮廓。",
    "This metallic shade can be worn as an all over lid colour, or layered on top of complementary tones for an everyday nude satin sheen finish. Mix this shade with water for a wash of colour or combine with a mixing medium for a foiled effect. Apply with fingertips or a dense brush for your desired level of intensity.": "可作全眼铺色，也可叠加在互补色之上，打造适合日常的裸感缎光效果。与水混合可获得轻透染色感，搭配调和液则可做出箔光效果。可用指腹或扎实刷具按需叠加显色度。",
    "This espresso bitter brown shade can be used to create depth and dimension in the crease, socket and lash line. Build up the colour in the outer corners of the eyes for a boldly pigmented finish or use a mixing medium and liner brush for a graphic finish. Use a brush for your desired level of intensity.": "适合用于眼窝、轮廓和睫毛根部加深，增强深邃度与立体感。可在眼尾逐步叠加，打造高显色效果；也可搭配调和液和眼线刷完成更利落的图形眼线。可用刷具按需叠加显色度。",
    "This cool-toned light beige shade can be used as an all-over lid colour or as a base tone beneath complementary hues. It can also be used to highlight the brow bone and inner corners of the eyes or as a transitional shade in the socket of the eye. Use as a base tone beneath shades ‘Dewdrop’ and ‘Faerie’ for a luminous, shimmering glow. Apply with a brush for your desired level of intensity.": "可作全眼铺色，或作为互补色下方的打底色；也可用于眉骨和眼头提亮，或作为眼窝过渡色。以它打底再叠加 `Dewdrop` 与 `Faerie`，可呈现明亮透光的微闪妆效。可用刷具按需叠加显色度。",
    "This soft, mid-tone brown shade can be used as an all-over lid colour or as a base tone beneath complementary hues. It can also be used to highlight the brow bone and inner corners of the eyes, or as a transitional shade in the socket of the eye. Use as a base tone beneath shades ‘Faerie’ and ‘Perchance’ for a glistening, natural finish. Apply with a brush for your desired level of intensity.": "可作全眼铺色，或作为互补色下方的打底色；也可用于眉骨和眼头提亮，或作为眼窝过渡色。以它打底再叠加 `Faerie` 与 `Perchance`，可呈现自然透亮的微光妆感。可用刷具按需叠加显色度。",
    "This mid-tone matte rose-brown shade can be used as an all-over lid colour or as a base tone beneath complementary hues. It can also be used as a transitional shade to contour the socket to create depth and dimension. Additionally, this color can be used in the brows or as a contour on light to medium complexions.": "可作全眼铺色，或作为互补色下方的打底色；也可作为眼窝过渡色勾勒轮廓，增强深度与立体感。浅至中等肤色还可用于眉部或修容。",
    "This champagne rosé shade can be used as an all-over lid color or along the high points of the face as a highlighter on all complexions. Apply to the inner corners of the eyes for a or on top of complementary hues in the center of the lid for an eye-catching effect. Combine this shade with a mixing medium for a foiled effect. Apply with a brush for your desired level of intensity. Can also be used as a liner or mixed with gloss for a luminous finish.": "可作全眼铺色，也可用于面部高点提亮，适合所有肤色。点在眼头，或叠在眼皮中央与互补色之上，都能带来更吸睛的光感。搭配调和液可获得箔光效果；也可作眼线，或混入唇蜜增添明亮釉泽。可用刷具按需叠加显色度。",
    "This light champagne pink shade can be used as an all-over lid color or along the high points of the face as a highlighter on all complexions. For a brightening, eye-catching effect, apply to the inner corners of the eyes, or layer over complementary hues for extra dimension. Apply with a brush for your desired level of intensity. This shade can also be blended with gloss or balm for a dewy, multi-use glow.": "可作全眼铺色，也可用于面部高点提亮，适合所有肤色。点在眼头或叠加在互补色之上，可增强明亮度与层次感。可用刷具按需叠加显色度；也可与唇蜜或润唇膏混合，呈现水润多用途光泽。",
    "This sheer, second-skin nude can be swept across the lids for a soft veil of light or layered over any shade in the palette to enhance luminosity. Use it to highlight the brow bone, inner corners of the eyes, cheekbones, or bridge of the nose for a subtle glow. For a radiant, multi-dimensional finish, layer over “Mirth” and “Perchance” to amplify their brilliance with a touch of shimmer. Apply with a brush for your desired level of intensity. Can also be used as a liner or mixed with gloss for a luminous finish.": "可轻扫全眼，带来柔和透光感，也可叠加在盘中任何颜色之上增强明亮度。还可用于眉骨、眼头、颧骨和鼻梁提亮，营造细腻光泽。叠在 `Mirth` 与 `Perchance` 之上，可进一步放大它们的闪耀层次。可用刷具按需叠加显色度；也可作眼线，或混入唇蜜增添亮泽。",
    "This muted purple-grey matte shade can be used as an all-over lid colour, in the crease to contour and create dimension, or as a liner for a soft, diffused effect on all complexions.": "可作全眼铺色，也可用于眼窝塑形、增强立体感，或作为柔雾眼线色，适合所有肤色。",
    "This nude rose duochromatic shade can be worn alone for a wash of brillant reflectivity or layer over complementary tones to accentuate its pearlescent dimension. For a high-shine, foiled effect, pair with a mixing medium. Apply with a brush for your desired level of intensity. Pair with “Faerie” and “Titania” for an ethereal eye look that glimmers with luminosity.": "可单独使用，呈现明亮偏光；也可叠加在互补色上，强化珠光层次。搭配调和液可获得更强烈的箔光效果。可用刷具按需叠加显色度。与 `Faerie` 和 `Titania` 搭配，可完成空灵发光的眼妆效果。",
    "This light pink-brown matte shade can be used as an all-over lid colour or as a base tone beneath complementary hues. It can also be used as a transitional shade to contour the socket to create depth and dimension. Pair with shimmering toppers like “Dewdrop” or deeper mattes such as “Perchance” to create seamless, softly sculpted eye looks.": "可作全眼铺色，或作为互补色下方的打底色；也可用于眼窝过渡，勾勒更柔和的深度与轮廓。搭配 `Dewdrop` 这类珠光提亮色，或 `Perchance` 这类更深哑光色，可完成自然衔接的雕塑感眼妆。",
    "This medium brown shade can be used as an all-over lid colour, as a transitional shade to build out the crease and socket, as a soft liner, or as a base tone beneath complementary tones for increased depth and saturation. Can also be used in brows on medium to deep complexions. Apply with a brush for your desired level of intensity.": "可作全眼铺色、眼窝过渡色、柔和眼线色，或作为互补色下方的打底色以增强深度与饱和度。中等至深肤色也可用于眉部修饰。可用刷具按需叠加显色度。",
    "Use this muted reflective burgundy tone as an all-over lid colour, layered overtop complementary shades, or on its own for a natural, softly shimmering effect on all complexions. This hue can be used in the crease to define the socket, as a liner, or paired with other shades to build depth and create a smouldering, multidimensional eye look.": "可作全眼铺色，叠加在互补色之上，或单独使用，呈现自然柔闪效果，适合所有肤色。也可用于眼窝加深、作为眼线色，或与其他色号搭配，打造带层次感的微熏妆效。",
    "This cool-toned brown shade can be used to create depth and dimension in the crease, socket, and lash line. Build up the colour in the outer corners of the eyes for a boldly pigmented finish or use a mixing medium and liner brush for a graphic finish. Pairs perfectly with ‘Potion’ and ‘Changeling’ for a richly pigmented duochromatic look. Use a brush for your desired level of intensity.": "适合用于眼窝、轮廓与睫毛根部加深，增强深邃度与立体感。可在眼尾逐步叠加，打造高显色效果；也可搭配调和液和眼线刷完成更利落的图形眼线。与 `Potion` 和 `Changeling` 搭配，可呈现高显色的双偏光层次妆效。可用刷具按需叠加显色度。",
    "This nourishing wax pomade can be worn alone to lock hair into place for long-wearing hold. For a more defined brow, layer each pomade over a complimentary powder to imbue the brow with subtle color and create pigmented, buildable intensity for a sculpted look that stays all day. Suitable for light blonde to light brunette hair.": "这款滋养型眉蜡膏可单独使用，帮助毛流定型并提供持久支撑。想让眉形更利落时，可将眉蜡叠加在相配的粉状色之上，为眉毛增添柔和色感，并逐步叠出更清晰立体的塑形效果，整日保持整洁。适合浅金发到浅棕发。",
    "To apply, use short, feathery strokes with an angled brush to outline, define, and fill in sparse areas, gradually building coverage as desired. Suitable for light blonde to light brunette hair with an ashy undertone. Can also be used to enhance the hairline, or as eyeshadow.": "建议使用斜角刷，以短而轻的羽毛状笔触勾勒眉形、填补空隙，并按需要逐步叠加显色度。适合带灰调的浅金发到浅棕发。也可用于修饰发际线，或作眼影使用。",
    "To apply, use short, feathery strokes with an angled brush to outline, define, and fill in sparse areas, gradually building coverage as desired. Suitable for light blonde to light brunette hair with a neutral undertone. Can also be used to enhance the hairline, or as eyeshadow.": "建议使用斜角刷，以短而轻的羽毛状笔触勾勒眉形、填补空隙，并按需要逐步叠加显色度。适合带中性底调的浅金发到浅棕发。也可用于修饰发际线，或作眼影使用。",
    "To apply, use short, feathery strokes with an angled brush to outline, define, and fill in sparse areas, gradually building coverage as desired. Suitable for light to medium brunette hair with an ashy undertone. Can also be used to enhance the hairline, or as eyeshadow.": "建议使用斜角刷，以短而轻的羽毛状笔触勾勒眉形、填补空隙，并按需要逐步叠加显色度。适合带灰调的浅棕到中棕发色。也可用于修饰发际线，或作眼影使用。",
    "To apply, use short, feathery strokes with an angled brush to outline, define, and fill in sparse areas, gradually building coverage as desired. Suitable for medium brunette hair with an ashy undertone. Can also be used to enhance the hairline, or as eyeshadow.": "建议使用斜角刷，以短而轻的羽毛状笔触勾勒眉形、填补空隙，并按需要逐步叠加显色度。适合带灰调的中棕发色。也可用于修饰发际线，或作眼影使用。",
    "This nourishing wax pomade can be worn alone to lock hair into place for long-wearing hold. For a more defined brow, layer each pomade over a complimentary powder to imbue the brow with subtle color and create pigmented, buildable intensity for a sculpted look that stays all day. Suitable for blonde to medium brunette hair.": "这款滋养型眉蜡膏可单独使用，帮助毛流定型并提供持久支撑。想让眉形更利落时，可将眉蜡叠加在相配的粉状色之上，为眉毛增添柔和色感，并逐步叠出更清晰立体的塑形效果，整日保持整洁。适合金发到中棕发。",
    "To apply, use short, feathery strokes with an angled brush to outline, define, and fill in sparse areas, gradually building coverage as desired. Suitable for light auburn hair with a soft red undertone. Can also be used to enhance the hairline, or as eyeshadow.": "建议使用斜角刷，以短而轻的羽毛状笔触勾勒眉形、填补空隙，并按需要逐步叠加显色度。适合带柔和红调的浅赤褐发色。也可用于修饰发际线，或作眼影使用。",
    "To apply, use short, feathery strokes with an angled brush to outline, define, and fill in sparse areas, gradually building coverage as desired. Suitable for medium brunette hair with an auburn undertone. Can also be used to enhance the hairline, or as eyeshadow.": "建议使用斜角刷，以短而轻的羽毛状笔触勾勒眉形、填补空隙，并按需要逐步叠加显色度。适合带赤褐调的中棕发色。也可用于修饰发际线，或作眼影使用。",
    "To apply, use short, feathery strokes with an angled brush to outline, define, and fill in sparse areas, gradually building coverage as desired. Suitable for medium brunette hair with a greenish auburn undertone. Can also be used to enhance the hairline, or as eyeshadow.": "建议使用斜角刷，以短而轻的羽毛状笔触勾勒眉形、填补空隙，并按需要逐步叠加显色度。适合带绿感赤褐底调的中棕发色。也可用于修饰发际线，或作眼影使用。",
    "To apply, use short, feathery strokes with an angled brush to outline, define, and fill in sparse areas, gradually building coverage as desired. Suitable for copper brunette hair with a soft aubergine undertone. Can also be used to enhance the hairline, or as eyeshadow.": "建议使用斜角刷，以短而轻的羽毛状笔触勾勒眉形、填补空隙，并按需要逐步叠加显色度。适合带柔和茄紫底调的铜棕发色。也可用于修饰发际线，或作眼影使用。",
    "This nourishing wax pomade can be worn alone to lock hair into place for long-wearing hold. For a more defined brow, layer each pomade over a complimentary powder to imbue the brow with subtle color and create pigmented, buildable intensity for a sculpted look that stays all day. Suitable for medium brunette to dark hair.": "这款滋养型眉蜡膏可单独使用，帮助毛流定型并提供持久支撑。想让眉形更利落时，可将眉蜡叠加在相配的粉状色之上，为眉毛增添柔和色感，并逐步叠出更清晰立体的塑形效果，整日保持整洁。适合中棕发到深色发。",
    "To apply, use short, feathery strokes with an angled brush to outline, define, and fill in sparse areas, gradually building coverage as desired. Suitable for light ash brown hair with a cool undertone. Can also be used to enhance the hairline, or as eyeshadow.": "建议使用斜角刷，以短而轻的羽毛状笔触勾勒眉形、填补空隙，并按需要逐步叠加显色度。适合带冷调底色的浅灰棕发色。也可用于修饰发际线，或作眼影使用。",
    "To apply, use short, feathery strokes with an angled brush to outline, define, and fill in sparse areas, gradually building coverage as desired. Suitable for medium ash brown hair with a cool undertone. Can also be used to enhance the hairline, or as eyeshadow.": "建议使用斜角刷，以短而轻的羽毛状笔触勾勒眉形、填补空隙，并按需要逐步叠加显色度。适合带冷调底色的中灰棕发色。也可用于修饰发际线，或作眼影使用。",
    "To apply, use short, feathery strokes with an angled brush to outline, define, and fill in sparse areas, gradually building coverage as desired. Suitable for medium charcoal grey hair with a cool undertone. Can also be used to enhance the hairline, or as eyeshadow.": "建议使用斜角刷，以短而轻的羽毛状笔触勾勒眉形、填补空隙，并按需要逐步叠加显色度。适合带冷调底色的中炭灰发色。也可用于修饰发际线，或作眼影使用。",
    "To apply, use short, feathery strokes with an angled brush to outline, define, and fill in sparse areas, gradually building coverage as desired. Suitable for dark, ashy hair with a soft aubergine undertone. Can also be used to enhance the hairline, or as eyeshadow.": "建议使用斜角刷，以短而轻的羽毛状笔触勾勒眉形、填补空隙，并按需要逐步叠加显色度。适合带柔和茄紫底调的深灰发色。也可用于修饰发际线，或作眼影使用。",
    "Use as all over lid color or as a crease color - pop a champagne shimmer over this for an easy daytime look.": "可作全眼铺色或眼窝过渡色；在其上轻叠一层香槟珠光，就能快速完成日间妆容。",
    "Use as all over lid color, or to brighten the inner corner on medium skin tones.": "可作全眼铺色；中等肤色也可用它提亮眼头。",
    "All over lid tone for a smokey chocolate eye, use as a base tone for deeper skin, a crease color to warm up the look, and can be used in brows for redheads. This can also be blended with other tones as a blush.": "可作巧克力烟熏妆的全眼铺色；深肤色可作打底，放在眼窝能提升整体暖感，也适合红发人群作眉色。还可与其他颜色混合作腮红使用。",
    "All over lid shade for medium to dark skin tones, use as a crease colour, and in brows. Shade can be used as a bronzer for lighter skin tones.": "适合中深肤色作全眼铺色，也可用作眼窝色和眉色；浅肤色则可拿来作修容或古铜色使用。",
    "On fair skin, this is a dramatic garnet, on deep skin, use it to warm up the lid or the crease. This can be mixed with a lighter shade for blush. Using this to create depth against green or blue eyes will intensify the color of the eye. *WARNING* - In the US, this shade contains pigments that the FDA has not approved for use in the eye area.": "在浅肤色上，它会呈现鲜明的石榴红调；在深肤色上，则适合用来温暖眼皮或眼窝。也可与浅色混合当作腮红。若用它为绿色或蓝色眼眸增加深度，会让瞳色更突出。提示：在美国法规下，此色含有未获 FDA 批准用于眼周的色料。",
    "Lids, creases, contour, brows - this color does it all on many skin tones.": "无论是眼皮铺色、眼窝加深、面部修容还是眉部塑形，这个颜色在多种肤色上都很实用。",
    "Use this for liner, for a dramatic eye, for brows, for contour on deeper skin types. *WARNING* - In the US, this shade contains pigments that the FDA has not approved for use in the eye area.": "可用于眼线、加深戏剧感眼妆、眉部塑形，也适合深肤色作修容。提示：在美国法规下，此色含有未获 FDA 批准用于眼周的色料。",
    "Use on the lid or crease for drama, use on the lid and pop a metallic color over it, blend out as a blush, mix with white to make a super natural flush on the eyelids or cheeks. *WARNING* - In the US, this shade contains pigments that the FDA has not approved for use in the eye area.": "可用于眼皮或眼窝，营造更强烈的妆感；也可先铺在眼皮上，再叠加金属色增强层次。还能晕染作腮红，或与白色混合，调出眼皮和双颊都适合的自然红晕。提示：在美国法规下，此色含有未获 FDA 批准用于眼周的色料。",
    "This super versatile color works for almost everything - try it wet as a liner, dry for a smokey eye or in the crease for depth. This plum looks good against every eye color! *WARNING* - In the US, this shade contains pigments that the FDA has not approved for use in the eye area.": "这是一支几乎无所不能的多用途色。可湿用作眼线，干用打造烟熏妆，或放在眼窝增加深度。这支李子紫几乎能衬托所有眼色。提示：在美国法规下，此色含有未获 FDA 批准用于眼周的色料。",
    "Use this rich metallic burgundy as an all-over lid color or concentrate the shade in the outer corners of the eyes for a warm smoky finish. Can be foiled or worn as liner.": "可作全眼铺色，也可集中在眼尾位置，打造温暖的烟熏妆效。可搭配调和液做出箔光效果，也可作为眼线色。",
    "Use this for a rich cobalt smokey eye, or a drop of water/mixing medium for a liner. This color also pops a brown or hazel eye.": "可用来打造浓郁的钴蓝烟熏妆，也可加一滴清水或调和液作眼线使用。这一色调尤其能衬托棕色或榛色眼眸。",
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
    "big-12-mattes-neutral-milieu": {
        "shade_count": "12色",
        "size_label": "大号",
        "cn_name": "哑光中性盘",
        "en_name": "Neutral Mattes: Milieu Slimpro",
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
    "middle-4-peche": {
        "shade_count": "4色",
        "size_label": "中号",
        "cn_name": "蜜桃盘",
        "en_name": "Petits Fours Pêche",
    },
    "middle-4-hesperides": {
        "shade_count": "4色",
        "size_label": "中号",
        "cn_name": "赫斯珀里得斯盘",
        "en_name": "Petits Fours Hesperides",
    },
    "middle-4-garnet": {
        "shade_count": "4色",
        "size_label": "中号",
        "cn_name": "石榴石盘",
        "en_name": "Petits Fours Garnet",
    },
    "middle-4-pastille": {
        "shade_count": "4色",
        "size_label": "中号",
        "cn_name": "糖片盘",
        "en_name": "Petits Fours Pastille",
    },
    "middle-4-lilas": {
        "shade_count": "4色",
        "size_label": "中号",
        "cn_name": "丁香盘",
        "en_name": "Petits Fours Lilas",
    },
    "middle-4-isolde": {
        "shade_count": "4色",
        "size_label": "中号",
        "cn_name": "伊索德盘",
        "en_name": "Petits Fours Isolde",
    },
    "middle-4-tyrian": {
        "shade_count": "4色",
        "size_label": "中号",
        "cn_name": "提尔紫盘",
        "en_name": "Petits Fours Tyrian",
    },
    "middle-15-structure-brow-eyeshadow-palette": {
        "shade_count": "15色",
        "size_label": "中号",
        "cn_name": "结构塑眉塑影修容盘",
        "en_name": "15-Pan Structure Brow, Shadow, Hairline & Contour Palette",
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
    "small-12-shimmers-sultry-muse": {
        "shade_count": "12色",
        "size_label": "小号",
        "cn_name": "魅惑微光盘",
        "en_name": "Petites Shimmers Sultry Muse",
    },
    "small-12-mattes-paris-cherubine": {
        "shade_count": "12色",
        "size_label": "小号",
        "cn_name": "巴黎小天使哑光盘",
        "en_name": "Petites Paris Chérubine Mattes",
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
    "middle-12-apricotine-lumiere-etendu": {
        "shade_count": "12色",
        "size_label": "中号",
        "cn_name": "杏光流辉盘",
        "en_name": "Apricotine Lumière Étendu",
    },
    "middle-12-praline-etendu": {
        "shade_count": "12色",
        "size_label": "中号",
        "cn_name": "果仁糖盘",
        "en_name": "Praline Étendu",
    },
    "middle-12-paris-nuit-etoilee-etendu": {
        "shade_count": "12色",
        "size_label": "中号",
        "cn_name": "巴黎星夜盘",
        "en_name": "Paris Nuit Étoilée Étendu",
    },
    "middle-12-violette-nocturne-etendu": {
        "shade_count": "12色",
        "size_label": "中号",
        "cn_name": "紫罗兰夜曲盘",
        "en_name": "Violette Nocturne Étendu",
    },
    "middle-12-violette-lumiere-etendu": {
        "shade_count": "12色",
        "size_label": "中号",
        "cn_name": "紫罗兰流辉盘",
        "en_name": "Violette Lumière Étendu",
    },
    "middle-12-midsommer-lumiere-etendu": {
        "shade_count": "12色",
        "size_label": "中号",
        "cn_name": "仲夏流辉盘",
        "en_name": "Midsommer Lumière Étendu",
    },
    "middle-12-lilas-lumiere-etendu": {
        "shade_count": "12色",
        "size_label": "中号",
        "cn_name": "丁香流辉盘",
        "en_name": "Lilas Lumière Étendu",
    },
    "middle-12-minxette-etendu": {
        "shade_count": "12色",
        "size_label": "中号",
        "cn_name": "狐魅暖棕盘",
        "en_name": "Minxette Étendu",
    },
    "middle-12-lisa-says-gah-x-aqua-etendu": {
        "shade_count": "12色",
        "size_label": "中号",
        "cn_name": "AQUA联名盘",
        "en_name": "Lisa Says Gah x AQUA Étendu",
    },
}


HOMEPAGE_LABELS = {
    "big-12-mattes-cool2": "12色 大号 哑光冷调盘 Matte Cool 2",
    "big-12-mattes-warm": "12色 大号 哑光暖调盘 Warm Mattes",
    "big-12-mattes-neutral": "12色 大号/小号 中性盘 Matte Neutral",
    "big-12-mattes-neutral-milieu": "12色 大号 哑光中性盘 Neutral Mattes: Milieu Slimpro",
    "big-12-mattes-cool-original": "12色 大号/小号 哑光冷调盘 Mattes Cool Original",
    "big-12-editorial-brights": "12色 大号/小号 哑光亮彩盘 Editorial Brights",
    "big-12-mattes-dark": "12色 大号/小号 哑光深调盘 Mattes Dark",
    "middle-35-pro-x1": "35色 中号 哑光大盘 Pro X1",
    "middle-4-violetta": "4色 中号 紫罗兰盘 Petits Fours Violetta",
    "middle-4-peche": "4色 中号 蜜桃盘 Petits Fours Pêche",
    "middle-4-hesperides": "4色 中号 赫斯珀里得斯盘 Petits Fours Hesperides",
    "middle-4-garnet": "4色 中号 石榴石盘 Petits Fours Garnet",
    "middle-4-pastille": "4色 中号 糖片盘 Petits Fours Pastille",
    "middle-4-lilas": "4色 中号 丁香盘 Petits Fours Lilas",
    "middle-4-isolde": "4色 中号 伊索德盘 Petits Fours Isolde",
    "middle-4-tyrian": "4色 中号 提尔紫盘 Petits Fours Tyrian",
    "middle-15-structure-brow-eyeshadow-palette": "15色 中号 结构塑眉塑影修容盘 15-Pan Structure Brow, Shadow, Hairline & Contour Palette",
    "small-12-matte-cool": "12色 小号 哑光冷调盘 Petites Mattes Cool",
    "small-12-shimmers-paris-nudes": "12色 小号 巴黎裸光盘 Petites Shimmers Paris Nudes",
    "small-12-shimmers-sultry-muse": "12色 小号 魅惑微光盘 Petites Shimmers Sultry Muse",
    "small-12-mattes-paris-cherubine": "12色 小号 巴黎小天使哑光盘 Petites Paris Chérubine Mattes",
    "middle-12-cashmerie-charmeuse-etendu": "12色 中号 羊绒魅缎盘 Cashmerie Charmeuse Etendu",
    "middle-12-sireneuse-etendu": "12色 中号 海妖绮梦盘 Sireneuse Etendu",
    "middle-12-sireneuse-nocturne-etendu": "12色 中号 海妖夜曲盘 Sireneuse Nocturne Etendu",
    "middle-12-apricotine-lumiere-etendu": "12色 中号 杏光流辉盘 Apricotine Lumière Étendu",
    "middle-12-praline-etendu": "12色 中号 果仁糖盘 Praline Étendu",
    "middle-12-paris-nuit-etoilee-etendu": "12色 中号 巴黎星夜盘 Paris Nuit Étoilée Étendu",
    "middle-12-violette-nocturne-etendu": "12色 中号 紫罗兰夜曲盘 Violette Nocturne Étendu",
    "middle-12-violette-lumiere-etendu": "12色 中号 紫罗兰流辉盘 Violette Lumière Étendu",
    "middle-12-midsommer-lumiere-etendu": "12色 中号 仲夏流辉盘 Midsommer Lumière Étendu",
    "middle-12-lilas-lumiere-etendu": "12色 中号 丁香流辉盘 Lilas Lumière Étendu",
    "middle-12-minxette-etendu": "12色 中号 狐魅暖棕盘 Minxette Étendu",
    "middle-12-lisa-says-gah-x-aqua-etendu": "12色 中号 AQUA联名盘 Lisa Says Gah x AQUA Étendu",
}


HOMEPAGE_GROUP_HEADINGS = {
    "middle-35-pro-x1": "#### 35色 中号 Pro X",
    "big-12-mattes-neutral": "#### 12色 大号/小号 Pro ",
    "big-12-mattes-neutral-milieu": "#### 12色 大号/小号 Pro ",
    "big-12-mattes-cool-original": "#### 12色 大号/小号 Pro ",
    "big-12-mattes-cool2": "#### 12色 大号/小号 Pro ",
    "big-12-mattes-warm": "#### 12色 大号/小号 Pro ",
    "big-12-mattes-dark": "#### 12色 大号/小号 Pro ",
    "big-12-editorial-brights": "#### 12色 大号/小号 Pro ",
    "middle-4-violetta": "#### 4色 中号 Petites",
    "middle-4-peche": "#### 4色 中号 Petites",
    "middle-4-hesperides": "#### 4色 中号 Petites",
    "middle-4-garnet": "#### 4色 中号 Petites",
    "middle-4-pastille": "#### 4色 中号 Petites",
    "middle-4-lilas": "#### 4色 中号 Petites",
    "middle-4-isolde": "#### 4色 中号 Petites",
    "middle-4-tyrian": "#### 4色 中号 Petites",
    "middle-15-structure-brow-eyeshadow-palette": "#### 15色 中号 Structure",
    "middle-12-cashmerie-charmeuse-etendu": "#### 12色 中号 Etendu",
    "middle-12-sireneuse-etendu": "#### 12色 中号 Etendu",
    "middle-12-sireneuse-nocturne-etendu": "#### 12色 中号 Etendu",
    "middle-12-apricotine-lumiere-etendu": "#### 12色 中号 Etendu",
    "middle-12-praline-etendu": "#### 12色 中号 Etendu",
    "middle-12-paris-nuit-etoilee-etendu": "#### 12色 中号 Etendu",
    "middle-12-violette-nocturne-etendu": "#### 12色 中号 Etendu",
    "middle-12-violette-lumiere-etendu": "#### 12色 中号 Etendu",
    "middle-12-midsommer-lumiere-etendu": "#### 12色 中号 Etendu",
    "middle-12-lilas-lumiere-etendu": "#### 12色 中号 Etendu",
    "middle-12-minxette-etendu": "#### 12色 中号 Etendu",
    "middle-12-lisa-says-gah-x-aqua-etendu": "#### 12色 中号 Etendu",
    "middle-12-soleil-la-plage-etendu": "#### 12色 中号 Etendu",
    "middle-12-visepro-paris-mattes-etendu": "#### 12色 中号 Etendu",
    "middle-12-bon-bon-praline-etendu": "#### 12色 中号 Etendu",
    "small-12-matte-cool": "#### 12色 小号 Petites",
    "small-12-shimmers-paris-nudes": "#### 12色 小号 Petites",
    "small-12-shimmers-sultry-muse": "#### 12色 小号 Petites",
    "small-12-mattes-paris-cherubine": "#### 12色 小号 Petites",
}


HOMEPAGE_SECTION = "### 眼影 Viseart"


PRODUCT_URLS = {
    "small-12-matte-cool": "https://viseartparis.com/en-de/products/petites-mattes-cool",
    "small-12-shimmers-paris-nudes": "https://viseartparis.com/en-de/products/petites-shimmers-paris-nudes?_pos=67&_sid=7a187920b&_ss=r",
    "small-12-shimmers-sultry-muse": "https://viseartparis.com/en-de/products/petites-shimmer-sultry-muse?_pos=78&_sid=7a187920b&_ss=r",
    "small-12-mattes-paris-cherubine": "https://viseartparis.com/en-de/products/paris-cherubine-mattes?_pos=95&_sid=a44f35d0c&_ss=r",
    "middle-4-violetta": "https://viseartparis.com/en-de/products/petits-fours-violetta?_pos=79&_sid=7a187920b&_ss=r",
    "middle-4-peche": "https://viseartparis.com/en-de/products/petits-fours-peche?_pos=4&_sid=91ac4c63a&_ss=r",
    "middle-4-hesperides": "https://viseartparis.com/en-de/products/petits-fours-hesperides?_pos=92&_sid=a44f35d0c&_ss=r",
    "middle-4-garnet": "https://viseartparis.com/en-de/products/petits-four-garnet?_pos=50&_sid=a44f35d0c&_ss=r",
    "middle-4-pastille": "https://viseartparis.com/en-de/products/petits-fours-pastille?_pos=61&_sid=a44f35d0c&_ss=r",
    "middle-4-lilas": "https://viseartparis.com/en-de/products/petits-fours-lilas?_pos=85&_sid=a44f35d0c&_ss=r",
    "middle-4-isolde": "https://viseartparis.com/en-de/products/petits-fours-isolde?_pos=86&_sid=a44f35d0c&_ss=r",
    "middle-4-tyrian": "https://viseartparis.com/en-de/products/petits-fours-tyrian?_pos=87&_sid=a44f35d0c&_ss=r",
    "middle-15-structure-brow-eyeshadow-palette": "https://viseartparis.com/en-de/products/structure-brow-eyeshadow-palette?_pos=10&_sid=a44f35d0c&_ss=r",
    "big-12-mattes-neutral": "https://viseartparis.com/en-de/products/petites-mattes-neutral",
    "big-12-mattes-neutral-milieu": "https://viseartparis.com/en-de/products/neutral-mattes-milieu-slimpro?_pos=23&_sid=a44f35d0c&_ss=r",
    "big-12-mattes-cool-original": "https://viseartparis.com/en-de/collections/visepro/products/visepro-cool-mattes-original",
    "big-12-editorial-brights": "https://viseartparis.com/en-de/products/visepro-editorial-brights?_pos=8&_sid=0596684ea&_ss=r",
    "big-12-mattes-dark": "https://viseartparis.com/en-de/products/visepro-dark-mattes?_pos=6&_sid=cdce64564&_ss=r",
    "big-12-mattes-warm": "https://viseartparis.com/en-de/products/visepro-warm-mattes",
    "middle-12-cashmerie-charmeuse-etendu": "https://viseartparis.com/en-de/products/cashmerie-charmeuse-etendu",
    "middle-12-sireneuse-etendu": "https://viseartparis.com/en-de/products/visepro-sireneuse-etendu",
    "middle-12-sireneuse-nocturne-etendu": "https://viseartparis.com/en-de/products/sireneuse-nocturne-etendu",
    "middle-12-apricotine-lumiere-etendu": "https://viseartparis.com/en-de/products/apricotine-lumiere-etendu?_pos=75&_sid=7a187920b&_ss=r",
    "middle-12-praline-etendu": "https://viseartparis.com/en-de/products/visepro-praline-etendu",
    "middle-12-paris-nuit-etoilee-etendu": "https://viseartparis.com/en-de/products/paris-nuit-etoilee-etendu?_pos=73&_sid=7a187920b&_ss=r",
    "middle-12-violette-nocturne-etendu": "https://viseartparis.com/en-de/products/violette-nocturne-etendu?_pos=70&_sid=7a187920b&_ss=r",
    "middle-12-violette-lumiere-etendu": "https://viseartparis.com/en-de/products/violette-lumiere-etendu?_pos=1&_psq=viol&_psid=7db8d6167&_ss=e",
    "middle-12-midsommer-lumiere-etendu": "https://viseartparis.com/en-de/products/visepro%E2%84%A2-midsommer-lumiere-etendu?_pos=2&_psq=viol&_psid=7db8d6167&_ss=e",
    "middle-12-lilas-lumiere-etendu": "https://viseartparis.com/en-de/products/visepro-lilas-lumiere-etendu?_pos=3&_psq=viol&_psid=7db8d6167&_ss=e",
    "middle-12-minxette-etendu": "https://viseartparis.com/en-de/products/minxette-etendu?_pos=90&_sid=a44f35d0c&_ss=r",
    "middle-12-lisa-says-gah-x-aqua-etendu": "https://viseartparis.com/en-de/products/lisa-says-gah-x-aqua-etendu?_pos=91&_sid=a44f35d0c&_ss=r",
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
        help="Grid size override. Defaults to 2 2 for 4 shades, 4 3 for 12 shades, and 7 5 for 35 shades.",
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
        shade_description_only_match = SHADE_DESCRIPTION_ONLY_RE.match(line)
        if shade_description_only_match:
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
            description = shade_description_only_match.group(2).strip()
            current = {
                "number": shade_description_only_match.group(1),
                "name": infer_shade_name_from_description(description),
                "description": description,
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


def infer_shade_name_from_description(description: str) -> str:
    base = description.strip().rstrip(".")
    if " with " in base:
        base = base.split(" with ", 1)[0]
    base = base.replace(",", " ")
    base = re.sub(r"\s+", " ", base).strip()
    if not base:
        return "Unnamed Shade"
    return base.title()


def infer_grid(shade_count: int) -> tuple[int, int]:
    if shade_count == 12:
        return 4, 3
    if shade_count == 15:
        return 5, 3
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
    return text


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
    target_heading = HOMEPAGE_GROUP_HEADINGS.get(palette_dir.name)
    lines = [
        line
        for line in lines
        if not (line.startswith("- 📄 [") and line.endswith(f"]({relative_path})"))
    ]

    updated_lines: list[str] = []
    inserted = False
    inside_section = False
    inside_target_group = False

    for line in lines:
        stripped = line.strip()

        if inside_target_group and (line.startswith("#### ") or line.startswith("### ")):
            updated_lines.append(entry)
            inserted = True
            inside_target_group = False

        updated_lines.append(line)
        if stripped == HOMEPAGE_SECTION:
            inside_section = True
            continue

        if inside_section and target_heading and line == target_heading:
            inside_target_group = True
            continue

        if inside_section and line.startswith("### "):
            if not inserted:
                if target_heading:
                    updated_lines.insert(len(updated_lines) - 1, target_heading)
                    updated_lines.insert(len(updated_lines) - 1, entry)
                else:
                    updated_lines.insert(len(updated_lines) - 1, entry)
                inserted = True
            inside_section = False

    if inside_target_group and not inserted:
        updated_lines.append(entry)
        inserted = True

    if inside_section and not inserted:
        if target_heading:
            updated_lines.append(target_heading)
        updated_lines.append(entry)
        inserted = True

    if not inserted:
        if updated_lines and updated_lines[-1] != "":
            updated_lines.append("")
        updated_lines.append(HOMEPAGE_SECTION)
        if target_heading:
            updated_lines.append(target_heading)
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
    for existing_file in output_dir.iterdir():
        if existing_file.is_file():
            existing_file.unlink()
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

    if args.product_url and page_data and page_data.shade_text:
        title, shades = parse_shades_from_text(
            page_data.shade_text,
            palette_dir.name,
            fallback_title=default_title_for_palette(palette_dir.name)
            if palette_dir.name in PALETTE_TITLE_PARTS
            else page_data.title,
        )
    elif source_readme.exists():
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