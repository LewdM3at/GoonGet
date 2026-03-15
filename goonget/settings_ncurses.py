import curses


def open_settings(stdscr):
    curses.start_color()
    curses.use_default_colors()
    curses.curs_set(0)
    curses.mousemask(curses.ALL_MOUSE_EVENTS)

    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_WHITE, -1)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_CYAN)

    C_ACCENT = curses.color_pair(1) | curses.A_BOLD
    C_NORMAL = curses.color_pair(2)
    C_SEL    = curses.color_pair(3)

    # Enable bracketed paste in the terminal
    import sys
    sys.stdout.write("\033[?2004h")
    sys.stdout.flush()

    # State
    selected_api  = 0  # 0 = Rule34, 1 = Gelbooru
    r34_api_key   = ""
    gb_api_key    = ""

    BOX_Y        = 2
    BOX_X        = 3
    BOX_H        = 7
    RULE34_ROW   = BOX_Y + 2
    GELBOORU_ROW = BOX_Y + 4

    # Fixed label column so both "API Key:" fields line up
    CHECKBOX_W   = len("[ ] Gelbooru.com   ")  # widest label + gap before API Key:
    KEY_LABEL    = "API Key: "

    def get_dims():
        h, w = stdscr.getmaxyx()
        BOX_W   = w - 6
        INNER_X = BOX_X + 2
        field_x = INNER_X + CHECKBOX_W + len(KEY_LABEL) + 1   # +1 for opening [
        FIELD_W = (BOX_X + BOX_W - 1) - field_x - 2           # right margin of 2
        return h, w, BOX_W, INNER_X, field_x, FIELD_W

    def draw():
        h, w, BOX_W, INNER_X, field_x, FIELD_W = get_dims()
        stdscr.erase()

        # Outer border
        stdscr.attron(C_NORMAL)
        stdscr.border()
        stdscr.attroff(C_NORMAL)

        # Main title
        title = " GoonGet — Settings "
        stdscr.attron(C_ACCENT)
        stdscr.addstr(0, (w - len(title)) // 2, title)
        stdscr.attroff(C_ACCENT)

        # ── API box — all borders in cyan ─────────────────────────────────────
        section = " API "
        top = "┌─" + section + "─" * (BOX_W - len(section) - 3) + "┐"
        stdscr.attron(C_ACCENT)
        stdscr.addstr(BOX_Y, BOX_X, top)
        for row in range(1, BOX_H - 1):
            stdscr.addstr(BOX_Y + row, BOX_X, "│")
            stdscr.addstr(BOX_Y + row, BOX_X + BOX_W - 1, "│")
        stdscr.addstr(BOX_Y + BOX_H - 1, BOX_X, "└" + "─" * (BOX_W - 2) + "┘")
        stdscr.attroff(C_ACCENT)

        # ── Rule34 row ────────────────────────────────────────────────────────
        r34_cb = "[x]" if selected_api == 0 else "[ ]"
        stdscr.attron(C_NORMAL)
        stdscr.addstr(RULE34_ROW, INNER_X, f"{r34_cb} Rule34.xxx")
        stdscr.addstr(RULE34_ROW, INNER_X + CHECKBOX_W, KEY_LABEL)
        display = r34_api_key[-FIELD_W:] if len(r34_api_key) > FIELD_W else r34_api_key
        stdscr.addstr(RULE34_ROW, field_x - 1, "[" + display.ljust(FIELD_W) + "]")
        stdscr.attroff(C_NORMAL)

        # ── Gelbooru row ──────────────────────────────────────────────────────
        gb_cb = "[x]" if selected_api == 1 else "[ ]"
        stdscr.attron(C_NORMAL)
        stdscr.addstr(GELBOORU_ROW, INNER_X, f"{gb_cb} Gelbooru.com")
        stdscr.addstr(GELBOORU_ROW, INNER_X + CHECKBOX_W, KEY_LABEL)
        display = gb_api_key[-FIELD_W:] if len(gb_api_key) > FIELD_W else gb_api_key
        stdscr.addstr(GELBOORU_ROW, field_x - 1, "[" + display.ljust(FIELD_W) + "]")
        stdscr.attroff(C_NORMAL)

        # Hint
        hint = " Click checkbox to select   Click key field to edit   q Quit "
        stdscr.attron(C_ACCENT)
        stdscr.addstr(h - 1, max(0, (w - len(hint)) // 2), hint[:w - 1])
        stdscr.attroff(C_ACCENT)

        stdscr.refresh()

    def edit_key(row_y, current_key):
        """Inline editor. Returns new key value. Auto-confirms on bracketed paste."""
        h, w, BOX_W, INNER_X, field_x, FIELD_W = get_dims()
        buf = list(current_key)
        curses.curs_set(1)
        in_paste = False

        def refresh_field():
            display   = "".join(buf)
            visible   = display[-FIELD_W:] if len(display) > FIELD_W else display
            field_str = visible.ljust(FIELD_W)
            stdscr.attron(C_SEL)
            stdscr.addstr(row_y, field_x, field_str)
            stdscr.attroff(C_SEL)
            cursor_x = field_x + min(len(visible), FIELD_W - 1)
            stdscr.move(row_y, cursor_x)
            stdscr.refresh()

        while True:
            refresh_field()
            ch = stdscr.getch()

            # Bracketed paste start: ESC [ 2 0 0 ~  (arrives as separate chars)
            if ch == 27:
                stdscr.nodelay(True)
                seq = [ch]
                while True:
                    nc = stdscr.getch()
                    if nc == -1:
                        break
                    seq.append(nc)
                stdscr.nodelay(False)

                seq_str = "".join(chr(c) if 0 <= c < 256 else "" for c in seq)

                if "\x1b[200~" in seq_str:
                    # Extract pasted content between markers
                    inner = seq_str.replace("\x1b[200~", "").replace("\x1b[201~", "")
                    buf.extend(c for c in inner if 32 <= ord(c) <= 126)
                    # Auto-confirm after paste
                    break
                else:
                    # Plain Escape — cancel
                    buf = list(current_key)
                    break

            elif ch in (10, 13):
                break
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                if buf:
                    buf.pop()
            elif 32 <= ch <= 126:
                buf.append(chr(ch))

        curses.curs_set(0)
        return "".join(buf)

    # Main loop
    while True:
        draw()
        key = stdscr.getch()

        if key == ord('q'):
            # Disable bracketed paste before exiting
            import sys
            sys.stdout.write("\033[?2004l")
            sys.stdout.flush()
            break

        elif key == curses.KEY_MOUSE:
            try:
                _, mx, my, _, bstate = curses.getmouse()
                if bstate & curses.BUTTON1_CLICKED:
                    h, w, BOX_W, INNER_X, field_x, FIELD_W = get_dims()

                    if my == RULE34_ROW:
                        if mx < INNER_X + CHECKBOX_W:
                            selected_api = 0
                        elif mx >= field_x - 1:
                            r34_api_key = edit_key(RULE34_ROW, r34_api_key)

                    elif my == GELBOORU_ROW:
                        if mx < INNER_X + CHECKBOX_W:
                            selected_api = 1
                        elif mx >= field_x - 1:
                            gb_api_key = edit_key(GELBOORU_ROW, gb_api_key)

            except curses.error:
                pass

