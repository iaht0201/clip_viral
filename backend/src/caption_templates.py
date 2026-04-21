"""
Caption template definitions for animated subtitles - VERSION 2.0 (Tối ưu tiếng Việt)
Đã fix cắt đuôi + thêm 5 style Việt Nam hot nhất
"""

from typing import Dict, Any, Literal
import logging

logger = logging.getLogger(__name__)

AnimationType = Literal["none", "karaoke", "pop", "fade", "bounce"]

CAPTION_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "default": {
        "name": "Default",
        "description": "Phong cách sạch sẽ, an toàn cho mọi video",
        "font_family": "BeVietnamPro-Bold",
        "font_size": 32,                    # Tăng cho tiếng Việt
        "font_color": "#FFFFFF",
        "highlight_color": "#FFD700",
        "stroke_color": "#000000",
        "stroke_width": 3,
        "background": False,
        "background_color": None,
        "animation": "none",
        "karaoke_enabled": False,
        "emoji_enabled": True,
        "shadow": True,
        "shadow_intensity": 0.7,
        "position_y": 0.78,
        "alignment": "center",
        "max_width_percent": 0.88,
        "line_spacing": 1.08,
    },
    "hormozi": {
        "name": "Hormozi Style",
        "description": "Xanh lá nổi bật - phong cách review chuyên nghiệp",
        "font_family": "BeVietnamPro-Bold",
        "font_size": 38,
        "font_color": "#FFFFFF",
        "highlight_color": "#00FF00",
        "stroke_color": "#000000",
        "stroke_width": 4,
        "background": True,
        "background_color": "#000000AA",
        "animation": "karaoke",
        "karaoke_enabled": True,
        "emoji_enabled": True,
        "shadow": True,
        "shadow_intensity": 0.9,
        "position_y": 0.75,
        "alignment": "center",
        "max_width_percent": 0.85,
        "line_spacing": 1.10,
    },
    "mrbeast": {
        "name": "MrBeast Style",
        "description": "Vàng to + pop animation - viral cực mạnh",
        "font_family": "BeVietnamPro-Bold",
        "font_size": 44,
        "font_color": "#FFFF00",
        "highlight_color": "#FF0000",
        "stroke_color": "#000000",
        "stroke_width": 5,
        "background": False,
        "background_color": None,
        "animation": "pop",
        "karaoke_enabled": False,
        "emoji_enabled": True,
        "shadow": True,
        "shadow_intensity": 1.0,
        "position_y": 0.72,
        "alignment": "center",
        "max_width_percent": 0.82,
        "line_spacing": 1.12,
    },
    "minimal": {
        "name": "Minimal",
        "description": "Sạch sẽ, tinh tế, ít làm phân tâm",
        "font_family": "BeVietnamPro-Bold",
        "font_size": 28,
        "font_color": "#FFFFFF",
        "highlight_color": "#CCCCCC",
        "stroke_color": None,
        "stroke_width": 0,
        "background": True,
        "background_color": "#00000080",
        "animation": "fade",
        "karaoke_enabled": False,
        "emoji_enabled": False,
        "shadow": False,
        "shadow_intensity": 0.0,
        "position_y": 0.80,
        "alignment": "center",
        "max_width_percent": 0.90,
        "line_spacing": 1.05,
    },
    "tiktok": {
        "name": "TikTok Official",
        "description": "Phong cách TikTok chuẩn (hồng + karaoke)",
        "font_family": "TikTokSans-Regular",
        "font_size": 34,
        "font_color": "#FFFFFF",
        "highlight_color": "#FE2C55",
        "stroke_color": "#000000",
        "stroke_width": 3,
        "background": False,
        "background_color": None,
        "animation": "karaoke",
        "karaoke_enabled": True,
        "emoji_enabled": True,
        "shadow": True,
        "shadow_intensity": 0.8,
        "position_y": 0.76,
        "alignment": "center",
        "max_width_percent": 0.87,
        "line_spacing": 1.09,
    },
    "neon": {
        "name": "Neon Glow",
        "description": "Đèn neon cực bắt mắt (dùng cho đêm hoặc gaming)",
        "font_family": "BeVietnamPro-Bold",
        "font_size": 36,
        "font_color": "#00FFFF",
        "highlight_color": "#FF00FF",
        "stroke_color": "#000066",
        "stroke_width": 3,
        "background": False,
        "background_color": None,
        "animation": "karaoke",
        "karaoke_enabled": True,
        "emoji_enabled": True,
        "shadow": True,
        "shadow_intensity": 1.0,
        "position_y": 0.75,
        "alignment": "center",
        "max_width_percent": 0.85,
        "line_spacing": 1.10,
    },
    "podcast": {
        "name": "Podcast Professional",
        "description": "Phong cách podcast sang trọng",
        "font_family": "BeVietnamPro-Bold",
        "font_size": 29,
        "font_color": "#FFFFFF",
        "highlight_color": "#FFB800",
        "stroke_color": "#333333",
        "stroke_width": 2,
        "background": True,
        "background_color": "#1A1A1ACC",
        "animation": "fade",
        "karaoke_enabled": False,
        "emoji_enabled": True,
        "shadow": False,
        "shadow_intensity": 0.0,
        "position_y": 0.79,
        "alignment": "center",
        "max_width_percent": 0.88,
        "line_spacing": 1.07,
    },

    # ====================== 5 TEMPLATE MỚI - ĐẬM CHẤT VIỆT NAM ======================
    "review_vn": {
        "name": "Review Việt Nam",
        "description": "Phong cách review Shopee/Tiki/Lazada hot nhất VN",
        "font_family": "BeVietnamPro-Bold",
        "font_size": 37,
        "font_color": "#FFFFFF",
        "highlight_color": "#00D4FF",       # Xanh dương nổi bật
        "stroke_color": "#000000",
        "stroke_width": 4,
        "background": True,
        "background_color": "#000000BB",
        "animation": "karaoke",
        "karaoke_enabled": True,
        "emoji_enabled": True,
        "shadow": True,
        "shadow_intensity": 0.9,
        "position_y": 0.74,
        "alignment": "center",
        "max_width_percent": 0.86,
        "line_spacing": 1.10,
    },
    "hai_huoc_vn": {
        "name": "Hài Hước Việt Nam",
        "description": "Phong cách hài hước kiểu Độ Mixi, Mr. T, Quang Linh",
        "font_family": "BeVietnamPro-Bold",
        "font_size": 39,
        "font_color": "#FFFFFF",
        "highlight_color": "#FF8800",       # Cam vui vẻ
        "stroke_color": "#000000",
        "stroke_width": 4,
        "background": False,
        "background_color": None,
        "animation": "pop",
        "karaoke_enabled": False,
        "emoji_enabled": True,
        "shadow": True,
        "shadow_intensity": 1.0,
        "position_y": 0.71,
        "alignment": "center",
        "max_width_percent": 0.84,
        "line_spacing": 1.12,
    },
    "ke_chuyen_vn": {
        "name": "Kể Chuyện / Storytime",
        "description": "Phong cách kể chuyện dài, drama, tâm sự",
        "font_family": "BeVietnamPro-Bold",
        "font_size": 31,
        "font_color": "#FFFFFF",
        "highlight_color": "#C26EFF",       # Tím ấm
        "stroke_color": "#000000",
        "stroke_width": 3,
        "background": True,
        "background_color": "#1F0033AA",
        "animation": "fade",
        "karaoke_enabled": False,
        "emoji_enabled": True,
        "shadow": True,
        "shadow_intensity": 0.7,
        "position_y": 0.77,
        "alignment": "center",
        "max_width_percent": 0.89,
        "line_spacing": 1.08,
    },
    "streetfood_vn": {
        "name": "Street Food Việt",
        "description": "Review đồ ăn đường phố - cực bắt mắt",
        "font_family": "BeVietnamPro-Bold",
        "font_size": 36,
        "font_color": "#FFFFFF",
        "highlight_color": "#FFCC00",
        "stroke_color": "#000000",
        "stroke_width": 4,
        "background": True,
        "background_color": "#00000099",
        "animation": "karaoke",
        "karaoke_enabled": True,
        "emoji_enabled": True,
        "shadow": True,
        "shadow_intensity": 0.9,
        "position_y": 0.73,
        "alignment": "center",
        "max_width_percent": 0.87,
        "line_spacing": 1.09,
    },
    "motivational_vn": {
        "name": "Động Lực Việt Nam",
        "description": "Lời khuyên, motivational kiểu Việt (kiểu Nam Vlog, Cris Phan)",
        "font_family": "BeVietnamPro-Bold",
        "font_size": 35,
        "font_color": "#FFFFFF",
        "highlight_color": "#00FF9D",
        "stroke_color": "#000000",
        "stroke_width": 4,
        "background": True,
        "background_color": "#003300BB",
        "animation": "pop",
        "karaoke_enabled": False,
        "emoji_enabled": True,
        "shadow": True,
        "shadow_intensity": 0.95,
        "position_y": 0.75,
        "alignment": "center",
        "max_width_percent": 0.85,
        "line_spacing": 1.11,
    },
}


def get_template(template_name: str) -> Dict[str, Any]:
    """Lấy template, fallback về default nếu không tồn tại"""
    if not template_name:
        return CAPTION_TEMPLATES["default"]
    return CAPTION_TEMPLATES.get(template_name.lower(), CAPTION_TEMPLATES["default"])


def get_all_templates() -> Dict[str, Dict[str, Any]]:
    return CAPTION_TEMPLATES


def get_template_names() -> list:
    return list(CAPTION_TEMPLATES.keys())


def get_template_info() -> list:
    """Dùng cho API / frontend hiển thị danh sách"""
    return [
        {
            "id": name,
            "name": template["name"],
            "description": template["description"],
            "animation": template["animation"],
            "karaoke_enabled": template.get("karaoke_enabled", False),
            "font_family": template["font_family"],
            "font_size": template["font_size"],
            "font_color": template["font_color"],
            "highlight_color": template["highlight_color"],
        }
        for name, template in CAPTION_TEMPLATES.items()
    ]


def get_safe_vertical_position(
    video_height: int, 
    text_height: int, 
    position_y: float,
    template: Dict = None
) -> int:
    """Phiên bản mới - An toàn tuyệt đối cho tiếng Việt + font to + karaoke"""
    if template is None:
        template = {}

    # Padding động theo font size + background + shadow
    font_size = template.get("font_size", 32)
    shadow_intensity = template.get("shadow_intensity", 0.8)
    has_background = template.get("background", False)
    
    min_top_padding = max(40, int(video_height * 0.04))
    
    # Bottom padding: lớn hơn rất nhiều để tránh cắt (đặc biệt tiếng Việt)
    base_bottom = max(160, int(video_height * 0.13))           # tăng từ 0.10 → 0.13
    extra_for_shadow = int(font_size * shadow_intensity * 1.2)
    extra_for_bg = 35 if has_background else 0
    min_bottom_padding = base_bottom + extra_for_shadow + extra_for_bg

    desired_y = int(video_height * position_y - text_height // 2)
    max_y = video_height - min_bottom_padding - text_height

    safe_y = max(min_top_padding, min(desired_y, max_y))
    
    logger.debug(f"Vertical position: {safe_y}px (desired={desired_y}, bottom_padding={min_bottom_padding})")
    return safe_y
