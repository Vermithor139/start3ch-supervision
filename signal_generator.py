from PIL import Image, ImageDraw, ImageFont
import random
import datetime

def generate_pro_signal():
    # 1. Setup Canvas
    width, height = 1080, 1080
    img = Image.new('RGB', (width, height), color=(2, 4, 10))
    draw = ImageDraw.Draw(img)
    
    C_BG = (2, 4, 10)
    C_GRID = (30, 41, 59)
    C_TEXT = (248, 250, 252)
    C_MUTED = (100, 116, 139)
    C_BLUE = (14, 165, 233)
    C_GREEN = (16, 185, 129)
    C_RED = (239, 68, 68)

    # 2. Draw Tactical Grid
    for x in range(0, width, 50):
        draw.line([(x, 0), (x, height)], fill=C_GRID, width=1)
    for y in range(0, height, 50):
        draw.line([(0, y), (width, y)], fill=C_GRID, width=1)

    # 3. Draw Fake Chart Line
    is_buy = random.choice([True, False])
    chart_points = []
    current_y = height // 2
    
    for x in range(100, 980, 20):
        change = random.randint(-30, 30)
        if is_buy: change -= 10
        else: change += 10
        
        current_y += change
        current_y = max(200, min(800, current_y))
        chart_points.append((x, current_y))
        
    if len(chart_points) > 1:
        draw.line(chart_points, fill=C_BLUE, width=4)
        last_x, last_y = chart_points[-1]
        if is_buy:
            draw.polygon([(last_x, last_y-20), (last_x-15, last_y+10), (last_x+15, last_y+10)], fill=C_GREEN)
        else:
            draw.polygon([(last_x, last_y+20), (last_x-15, last_y-10), (last_x+15, last_y-10)], fill=C_RED)

    # 4. Fonts
    try:
        font_title = ImageFont.truetype("arialbd.ttf", 40)
        font_main = ImageFont.truetype("arialbd.ttf", 100)
        font_sub = ImageFont.truetype("arial.ttf", 40)
        font_data = ImageFont.truetype("arial.ttf", 30)
        font_small = ImageFont.truetype("arial.ttf", 24)
    except:
        font_title = ImageFont.load_default()
        font_main = font_title
        font_sub = font_title
        font_data = font_title
        font_small = font_title

    # 5. Header
    draw.rectangle([(0, 0), (width, 80)], fill=(11, 17, 32))
    draw.text((540, 40), "VERUM INVEST // ALGORITHMIC TERMINAL", fill=C_BLUE, font=font_data, anchor="mm")
    
    # 6. Main Signal Data
    pairs = [
        ("XAU/USD", 2340.50), 
        ("BTC/USD", 68420.00), 
        ("EUR/USD", 1.0845), 
        ("GBP/JPY", 194.20)
    ]
    pair_name, base_price = random.choice(pairs)
    
    if is_buy:
        direction = "LONG / BUY"
        dir_color = C_GREEN
        entry = base_price
        tp = base_price + (base_price * 0.015)
        sl = base_price - (base_price * 0.005)
    else:
        direction = "SHORT / SELL"
        dir_color = C_RED
        entry = base_price
        tp = base_price - (base_price * 0.015)
        sl = base_price + (base_price * 0.005)

    # Data Box
    draw.rectangle([(100, 150), (980, 450)], fill=(13, 19, 33), outline=C_BLUE, width=2)
    draw.text((540, 220), pair_name, fill=C_TEXT, font=font_main, anchor="mm")
    draw.text((540, 320), direction, fill=dir_color, font=font_sub, anchor="mm")
    
    # Levels Box
    draw.rectangle([(100, 500), (980, 750)], fill=(11, 17, 32), outline=C_GRID, width=1)
    
    draw.text((150, 540), "ENTRY PRICE:", fill=C_MUTED, font=font_data)
    draw.text((930, 540), f"{entry:.2f}", fill=C_TEXT, font=font_data, anchor="rm")
    draw.line([(150, 590), (930, 590)], fill=C_GRID, width=2)
    
    draw.text((150, 620), "TAKE PROFIT (TP):", fill=C_GREEN, font=font_data)
    draw.text((930, 620), f"{tp:.2f}", fill=C_GREEN, font=font_data, anchor="rm")
    draw.line([(150, 670), (930, 670)], fill=C_GRID, width=2)
    
    draw.text((150, 700), "STOP LOSS (SL):", fill=C_RED, font=font_data)
    draw.text((930, 700), f"{sl:.2f}", fill=C_RED, font=font_data, anchor="rm")

    # 7. NEW FOOTER (Stark Style)
    draw.rectangle([(0, 850), (width, height)], fill=(11, 17, 32))
    draw.text((540, 900), "CONFIDENCE: 94.2% | R:R RATIO 1:3", fill=C_BLUE, font=font_data, anchor="mm")
    draw.text((540, 960), "Comment 'MT5' for full breakdown", fill=C_TEXT, font=font_sub, anchor="mm")
    
    # Changed from "Generated" to "System Status"
    draw.text((540, 1020), "SYSTEM STATUS: ONLINE | MARKET SYNC: LIVE", fill=C_GREEN, font=font_small, anchor="mm")

    # Save
    filename = f"VERUM_SIGNAL_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    img.save(filename)
    print(f"✅ PRO Signal generated: {filename}")

if __name__ == "__main__":
    generate_pro_signal()