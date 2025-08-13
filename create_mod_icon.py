
#!/usr/bin/env python3
"""
Simple script to convert the SVG logo to PNG format for the FS25 mod.
Requires: pip install cairosvg pillow
"""

try:
    import cairosvg
    from PIL import Image
    import io
    
    def convert_svg_to_png():
        # Convert SVG to PNG
        png_data = cairosvg.svg2png(url="FS25_Web_Mod/logo.svg", output_width=256, output_height=256)
        
        # Save as icon.png
        with open("FS25_Web_Mod/icon.png", "wb") as f:
            f.write(png_data)
        
        print("✅ Logo converted successfully! New icon.png created in FS25_Web_Mod/")
        print("📁 The mod now has a DixielandRP branded logo!")
        
    if __name__ == "__main__":
        convert_svg_to_png()
        
except ImportError:
    print("❌ Required packages not found.")
    print("🔧 Install them with: pip install cairosvg pillow")
    print("💡 Alternative: Use an online SVG to PNG converter with the logo.svg file")
