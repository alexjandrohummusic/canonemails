"""Los 5 diseños seleccionables. Cada tema es un conjunto de tokens visuales;
la MISMA plantilla renderiza TSL (carta) o cross-sell (tarjetas) según el bloque."""
THEMES = {
    "editorial":   {"nombre": "Editorial", "bg": "#f6f4ef", "card": "#ffffff", "ink": "#22201c",
                    "brand": "#3b322a", "accent": "#8a6d3b", "font": "Georgia, 'Times New Roman', serif", "radius": "2px"},
    "minimal":     {"nombre": "Minimal", "bg": "#f4f7fa", "card": "#ffffff", "ink": "#1c2733",
                    "brand": "#0B2545", "accent": "#12B0A0", "font": "Arial, Helvetica, sans-serif", "radius": "6px"},
    "wellness":    {"nombre": "Wellness", "bg": "#f3f8f2", "card": "#ffffff", "ink": "#2f3a33",
                    "brand": "#2e6b57", "accent": "#7bbf9e", "font": "'Trebuchet MS', Verdana, sans-serif", "radius": "14px"},
    "corporativo": {"nombre": "Corporativo", "bg": "#eef1f4", "card": "#ffffff", "ink": "#1a2430",
                    "brand": "#123a5e", "accent": "#1B6E8C", "font": "Arial, Helvetica, sans-serif", "radius": "4px"},
    "bold":        {"nombre": "Bold", "bg": "#111418", "card": "#1c2127", "ink": "#f2f4f7",
                    "brand": "#0B2545", "accent": "#ff5a3c", "font": "'Arial Black', Arial, sans-serif", "radius": "8px"},
}
def get(name: str) -> dict:
    return THEMES.get(name, THEMES["minimal"])
