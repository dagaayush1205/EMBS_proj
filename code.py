            current = word
            if len(lines) == max_lines - 1:
                break
    if current:
        remaining = ' '.join(words[len(' '.join(lines + [current]).split()):])
        if remaining and len(lines) == max_lines - 1:
            current += ' ' + remaining
        lines.append(current)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
    last = lines[-1] if lines else ''
    if font.size(last)[0] > max_width:
        while last and font.size(last + '…')[0] > max_width:
            last = last[:-1]
        lines[-1] = last.rstrip() + '…'
    return lines


def main():
    pygame.init()
    # Set SDL display size to screen's current mode when possible.
    info = pygame.display.Info()
    w = info.current_w if 300 <= info.current_w <= 1920 else 480
    h = info.current_h if 200 <= info.current_h <= 1080 else 320
    # Render on virtual 480x320 canvas; scale to actual LCD resolution.
    try:
        screen = pygame.display.set_mode((w, h), pygame.FULLSCREEN)
    except pygame.error:
        screen = pygame.display.set_mode((480, 320))
    pygame.display.set_caption('Pi • Daily Pulse')
    pygame.mouse.set_visible(False)
    canvas = pygame.Surface((480, 320))
    font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    bold_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    def font(sz, bold=False):
        p = bold_path if bold else font_path
        return pygame.font.Font(p if os.path.isfile(p) else None, sz)
    label = font(12, True)
    body = font(15)
    small = font(11)
    number = font(24, True)
    tempfont = font(43, True)
    timefont = font(22, True)
    clock = pygame.time.Clock()
    threading.Thread(target=refresh_loop, daemon=True).start()
    start = time.monotonic()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q)):
                pygame.quit()
                return
        with lock:
            state = {'weather': data['weather'], 'markets': dict(data['markets']),
                     'news': list(data['news']), 'updated': dict(data['updated'])}
        canvas.fill(BG)
        now = datetime.now(TIMEZONE)
        fitted_text(canvas, 'DAILY PULSE', label, CYAN, 17, 14, 190)
        canvas.blit(timefont.render(now.strftime('%H:%M'), True, WHITE), (383, 8))
        canvas.blit(small.render(now.strftime('%a, %d %b'), True, MUTED), (17, 36))

        def card(x, y, cw, ch):
            rect = pygame.Rect(x, y, cw, ch)
            pygame.draw.rect(canvas, CARD, rect, border_radius=12)
            pygame.draw.rect(canvas, CARD_EDGE, rect, width=1, border_radius=12)

        # Weather pane
        card(12, 60, 222, 115)
        fitted_text(canvas, f'WEATHER  •  {CITY.upper()}', label, CYAN, 24, 72, 195)
        weather = state['weather']
        if weather:
            canvas.blit(tempfont.render(f"{weather['temperature_2m']:.0f}°", True, WHITE), (24, 91))
            fitted_text(canvas, description(weather.get('weather_code')), body, MUTED, 117, 105, 105)
            fitted_text(canvas, f"Humidity {weather.get('relative_humidity_2m', '?')}%", small, MUTED, 25, 154, 180)
        else:
            fitted_text(canvas, 'Loading weather…', body, MUTED, 24, 116, 193)

        # Markets pane
        card(244, 60, 224, 115)
        fitted_text(canvas, 'INDIAN MARKETS', label, CYAN, 256, 72, 195)
        for i, name in enumerate(('NIFTY 50', 'SENSEX')):
            y = 94 + 38 * i
            fitted_text(canvas, name, small, MUTED, 256, y, 100)
            market = state['markets'].get(name)
            if market:
                fitted_text(canvas, f"{market['price']:,.0f}", number, WHITE, 256, y + 11, 119)
                pct = market['change']
                color = GREEN if pct >= 0 else RED
                fitted_text(canvas, f"{pct:+.2f}%", small, color, 376, y + 18, 82)
            else:
                fitted_text(canvas, 'Loading…', body, MUTED, 256, y + 11, 190)

        # Headline pane
        card(12, 185, 456, 105)
        fitted_text(canvas, 'TOP HEADLINES', label, YELLOW, 24, 197, 210)
        headlines = state['news']
        if headlines:
            index = int((time.monotonic() - start) / NEWS_SCROLL_SECONDS) % len(headlines)
            fitted_text(canvas, f'{index + 1}/{len(headlines)}', small, MUTED, 430, 198, 32)
            lines = wrap_text(headlines[index], body, 420, 3)
            for j, line in enumerate(lines[:3]):
                fitted_text(canvas, line, body, WHITE, 24, 221 + j * 20, 420)
        else:
            fitted_text(canvas, 'Fetching the latest headlines…', body, MUTED, 24, 226, 410)

        # Footer: show freshness and market caveat.
        mt = state['updated'].get('markets')
        age = f"Market data {mt.strftime('%H:%M')}" if mt else 'Connecting…'
        fitted_text(canvas, age + '  •  May be delayed', small, MUTED, 17, 302, 440)

        if screen.get_size() == (480, 320):
            screen.blit(canvas, (0, 0))
        else:
            screen.blit(pygame.transform.smoothscale(canvas, screen.get_size()), (0, 0))
        pygame.display.flip()
        clock.tick(2)


if __name__ == '__main__':
    main()


