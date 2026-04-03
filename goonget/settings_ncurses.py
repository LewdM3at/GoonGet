import curses
import sys
import json
from pathlib import Path

CONFIG_FILE = Path.home() / ".config" / "goonget" / "config.json"

# ── Config load / save ────────────────────────────────────────────────────────

def load_state():
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text())
        except json.JSONDecodeError:
            cfg = {}
    else:
        cfg = {}

    source       = cfg.get("source", "rule34.xxx")
    default_tags = cfg.get("default_tags", [])

    tags_checked = []
    tag_values   = []
    for t in default_tags:
        if isinstance(t, dict):
            tag_values.append(t.get("tag", ""))
            tags_checked.append(t.get("active", True))
        else:
            tag_values.append(str(t))
            tags_checked.append(True)

    if not tag_values:
        tag_values   = [""]
        tags_checked = [False]

    return {
        "selected_api":    0 if source == "rule34.xxx" else 1,
        "r34_key":         cfg.get("rule34_api_key", ""),
        "gb_key":          cfg.get("gelbooru_api_key", ""),
        "ss_interval":     str(cfg.get("slideshow_timer", "")),
        "size":            cfg.get("size", ""),
        "show_src_links":  cfg.get("show_source_links", False),
        "tags_checked":    tags_checked,
        "tag_values":      tag_values,
        "tag_scroll":      0,
    }


def save_state(state):
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text())
        except json.JSONDecodeError:
            cfg = {}
    else:
        cfg = {}

    cfg["source"]             = "rule34.xxx" if state["selected_api"] == 0 else "gelbooru.com"
    cfg["rule34_api_key"]     = state["r34_key"]
    cfg["gelbooru_api_key"]   = state["gb_key"]
    cfg["show_source_links"]  = state["show_src_links"]

    if state["ss_interval"].strip().isdigit():
        cfg["slideshow_timer"] = int(state["ss_interval"].strip())

    size = state["size"].strip()
    cfg["size"] = size if _valid_size(size) else "Fill"

    cfg["default_tags"] = [
        {"tag": v.strip(), "active": checked}
        for checked, v in zip(state["tags_checked"], state["tag_values"])
        if v.strip()
    ]

    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=4))


# ── Layout constants ──────────────────────────────────────────────────────────

BOX_X   = 3
INNER_X = BOX_X + 2

API_BOX_Y    = 2
API_BOX_H    = 7
CHECKBOX_W   = len("[ ] Gelbooru.com   ")
KEY_LABEL    = "API Key: "
RULE34_ROW   = API_BOX_Y + 2
GELBOORU_ROW = API_BOX_Y + 4

SS_BOX_Y = API_BOX_Y + API_BOX_H + 1
SS_BOX_H = 5
SS_ROW   = SS_BOX_Y + 2
SS_LABEL = "Interval (s): "

SIZE_BOX_Y = SS_BOX_Y + SS_BOX_H + 1
SIZE_BOX_H = 5
SIZE_ROW   = SIZE_BOX_Y + 2
SIZE_LABEL = "Size (WxH): "

INFO_BOX_Y   = SIZE_BOX_Y + SIZE_BOX_H + 1
INFO_BOX_H   = 5
INFO_ROW     = INFO_BOX_Y + 2
SRC_LINK_CB  = "[ ] Show source links"

TAGS_BOX_Y       = INFO_BOX_Y + INFO_BOX_H + 1
TAG_CB_W         = len("[x] ")
TAGS_VISIBLE_MAX = 15

MIN_FIELD = 10
MIN_W     = 60
MIN_H     = TAGS_BOX_Y + 7  # enough to show box + at least 1 tag + blank row + button

# ── Dynamic tags helpers (add blank row before Add button) ───────────────────

def tags_visible(stdscr):
    """How many tag rows fit in the terminal, capped at TAGS_VISIBLE_MAX."""
    h, _ = stdscr.getmaxyx()
    available = h - TAGS_BOX_Y - 5
    return max(1, min(TAGS_VISIBLE_MAX, available))

def tags_box_h(n_visible):
    # top border + n tag rows + blank spacer row + add-button row + bottom border
    return n_visible + 4

def tag_row(screen_i):
    return TAGS_BOX_Y + 2 + screen_i

def btn_row(n_visible):
    # leave one blank row between last tag and the button
    return TAGS_BOX_Y + 2 + n_visible + 1


# ── Pure helpers ──────────────────────────────────────────────────────────────

def field(value):
    if not value:
        return "[ " + " " * MIN_FIELD + " ]"
    return "[ " + value + " ]"

def field_truncated(value, max_width):
    if not value:
        return "[ " + " " * min(MIN_FIELD, max_width) + " ]"
    if len(value) > max_width:
        value = value[:max_width - 3] + "..."
    return "[ " + value + " ]"

def _valid_size(value: str) -> bool:
    import re
    return bool(re.fullmatch(r"\d+x\d+", value.strip(), re.IGNORECASE))


# ── Drawing helpers ───────────────────────────────────────────────────────────

def draw_box(stdscr, y, h, label, c_accent):
    _, w = stdscr.getmaxyx()
    bw      = w - 6
    section = f" {label} "
    top     = "┌─" + section + "─" * (bw - len(section) - 3) + "┐"
    stdscr.attron(c_accent)
    try:
        stdscr.addstr(y, BOX_X, top)
        for row in range(1, h - 1):
            stdscr.addstr(y + row, BOX_X,          "│")
            stdscr.addstr(y + row, BOX_X + bw - 1, "│")
        stdscr.addstr(y + h - 1, BOX_X, "└" + "─" * (bw - 2) + "┘")
    except curses.error:
        pass
    stdscr.attroff(c_accent)

def write(stdscr, row, col, text, attr):
    try:
        stdscr.attron(attr)
        stdscr.addstr(row, col, text)
        stdscr.attroff(attr)
    except curses.error:
        pass

def write_hint(stdscr, row, field_x, msg, c_hint):
    try:
        stdscr.attron(c_hint)
        stdscr.addstr(row + 1, field_x, msg)
        stdscr.attroff(c_hint)
    except curses.error:
        pass

def clear_hint(stdscr, row, field_x, width):
    try:
        stdscr.addstr(row + 1, field_x, " " * width)
    except curses.error:
        pass


# ── Too-small screen ──────────────────────────────────────────────────────────

def draw_too_small(stdscr):
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    lines = [
        "Terminal too small!",
        f"Minimum size: {MIN_W}x{MIN_H}",
        f"Current size: {w}x{h}",
        "Please resize your terminal.",
        "",
        "Press q to quit.",
    ]
    for i, line in enumerate(lines):
        y = h // 2 - len(lines) // 2 + i
        x = max(0, (w - len(line)) // 2)
        try:
            stdscr.addstr(y, x, line)
        except curses.error:
            pass
    stdscr.refresh()


# ── Inline field editor ───────────────────────────────────────────────────────

def inline_edit(stdscr, row, field_x, initial, c_sel, c_hint):
    buf  = list(initial)
    hint = " Press ENTER to confirm "
    curses.curs_set(1)

    while True:
        _, w     = stdscr.getmaxyx()
        value    = "".join(buf)
        max_w    = w - field_x - 4
        display  = value[-max_w:] if len(value) > max_w else value
        rendered = "[ " + display + " ]"
        cursor_x = min(field_x + 2 + len(display), w - 2)

        stdscr.attron(c_sel)
        try:
            stdscr.addstr(row, field_x, rendered)
        except curses.error:
            pass
        stdscr.attroff(c_sel)
        write_hint(stdscr, row, field_x, hint, c_hint)
        stdscr.move(row, cursor_x)
        stdscr.refresh()

        ch = stdscr.getch()

        if ch == 27:
            stdscr.nodelay(True)
            seq = []
            while True:
                nc = stdscr.getch()
                if nc == -1:
                    break
                seq.append(chr(nc) if 0 <= nc < 256 else "")
            stdscr.nodelay(False)
            seq_str = "".join(seq)
            if "[200~" in seq_str:
                pasted = seq_str.split("[200~", 1)[-1].split("[201~")[0]
                buf.extend(c for c in pasted if 32 <= ord(c) <= 126)
                break
            else:
                buf = list(initial)
                break
        elif ch in (10, 13):
            break
        elif ch in (curses.KEY_BACKSPACE, 127, 8):
            if buf:
                buf.pop()
        elif 32 <= ch <= 126:
            buf.append(chr(ch))

    clear_hint(stdscr, row, field_x, len(hint))
    curses.curs_set(0)
    return "".join(buf)


def inline_edit_size(stdscr, row, field_x, initial, c_sel, c_hint):
    buf = list(initial)
    curses.curs_set(1)

    def allowed(ch, current):
        if ch.isdigit():
            return True
        if ch.lower() == 'x' and 'x' not in current.lower():
            return True
        return False

    hint    = " Press Enter to confirm "
    warning = " ✗ Format must be WxH (e.g. 1920x1080). Leave empty for Fill."
    msg     = hint

    while True:
        value    = "".join(buf)
        rendered = field(value)
        cursor_x = field_x + 2 + len(value)

        stdscr.attron(c_sel)
        try:
            stdscr.addstr(row, field_x, rendered)
        except curses.error:
            pass
        stdscr.attroff(c_sel)
        write_hint(stdscr, row, field_x, msg.ljust(len(warning)), c_hint)
        stdscr.move(row, cursor_x)
        stdscr.refresh()

        ch = stdscr.getch()

        if ch == 27:
            stdscr.nodelay(True)
            seq = []
            while True:
                nc = stdscr.getch()
                if nc == -1:
                    break
                seq.append(chr(nc) if 0 <= nc < 256 else "")
            stdscr.nodelay(False)
            if "[200~" not in "".join(seq):
                buf = list(initial)
                break
        elif ch in (10, 13):
            if not value or _valid_size(value):
                break
            msg = warning
        elif ch in (curses.KEY_BACKSPACE, 127, 8):
            if buf:
                buf.pop()
            msg = hint
        elif 32 <= ch <= 126:
            c = chr(ch)
            if allowed(c, value):
                buf.append(c)
                msg = hint

    clear_hint(stdscr, row, field_x, len(warning))
    curses.curs_set(0)
    return "".join(buf)


# ── Main draw ─────────────────────────────────────────────────────────────────

def draw(stdscr, state, colors):
    c_accent, c_normal, c_sel, c_btn, c_check, c_field, c_uncheck = colors
    h, w = stdscr.getmaxyx()
    stdscr.erase()

    stdscr.attron(c_normal)
    stdscr.border()
    stdscr.attroff(c_normal)
    write(stdscr, 0, (w - 20) // 2, " GoonGet — Settings ", c_accent)

    # ── API box ───────────────────────────────────────────────────────────────
    draw_box(stdscr, API_BOX_Y, API_BOX_H, "API", c_accent)
    r34_cb = "[x]" if state["selected_api"] == 0 else "[ ]"
    gb_cb  = "[x]" if state["selected_api"] == 1 else "[ ]"
    key_field_start = INNER_X + CHECKBOX_W + len(KEY_LABEL)
    key_max_w = w - 6 - key_field_start - 4
    write(stdscr, RULE34_ROW,   INNER_X, r34_cb, c_check if state["selected_api"] == 0 else c_uncheck)
    write(stdscr, RULE34_ROW,   INNER_X + len(r34_cb) + 1, "Rule34.xxx", c_normal)
    write(stdscr, RULE34_ROW,   INNER_X + CHECKBOX_W, KEY_LABEL, c_normal)
    write(stdscr, RULE34_ROW,   INNER_X + CHECKBOX_W + len(KEY_LABEL), field_truncated(state["r34_key"], key_max_w), c_field)
    write(stdscr, GELBOORU_ROW, INNER_X, gb_cb, c_check if state["selected_api"] == 1 else c_uncheck)
    write(stdscr, GELBOORU_ROW, INNER_X + len(gb_cb) + 1, "Gelbooru.com", c_normal)
    write(stdscr, GELBOORU_ROW, INNER_X + CHECKBOX_W, KEY_LABEL, c_normal)
    write(stdscr, GELBOORU_ROW, INNER_X + CHECKBOX_W + len(KEY_LABEL), field_truncated(state["gb_key"], key_max_w), c_field)

    # ── Slideshow box ─────────────────────────────────────────────────────────
    draw_box(stdscr, SS_BOX_Y, SS_BOX_H, "Slideshow", c_accent)
    write(stdscr, SS_ROW, INNER_X, SS_LABEL, c_normal)
    write(stdscr, SS_ROW, INNER_X + len(SS_LABEL), field(state["ss_interval"]), c_field)

    # ── Size box ──────────────────────────────────────────────────────────────
    draw_box(stdscr, SIZE_BOX_Y, SIZE_BOX_H, "Size", c_accent)
    size_display = state["size"] if state["size"] else "Fill"
    write(stdscr, SIZE_ROW, INNER_X, SIZE_LABEL, c_normal)
    write(stdscr, SIZE_ROW, INNER_X + len(SIZE_LABEL), field(size_display), c_field)

    # ── Additional Information box ────────────────────────────────────────────
    draw_box(stdscr, INFO_BOX_Y, INFO_BOX_H, "Additional Information", c_accent)
    src_cb = "[x]" if state["show_src_links"] else "[ ]"
    write(stdscr, INFO_ROW, INNER_X, src_cb, c_check if state["show_src_links"] else c_uncheck)
    write(stdscr, INFO_ROW, INNER_X + len(src_cb) + 1, "Show source links", c_normal)

    # ── Tags box (scrollable) ─────────────────────────────────────────────────
    tags      = state["tags_checked"]
    tag_vals  = state["tag_values"]
    t_scroll  = state["tag_scroll"]
    n_vis     = tags_visible(stdscr)
    box_h     = tags_box_h(n_vis)
    total     = len(tags)

    draw_box(stdscr, TAGS_BOX_Y, box_h, "Default Tags", c_accent)

    # Scroll indicators on box borders
    if t_scroll > 0:
        write(stdscr, TAGS_BOX_Y, BOX_X + (w - 6) // 2, " ▲ ", c_accent)
    if t_scroll + n_vis < total:
        write(stdscr, TAGS_BOX_Y + box_h - 1, BOX_X + (w - 6) // 2, " ▼ ", c_accent)

    # Visible tag rows
    for screen_i in range(n_vis):
        data_i = screen_i + t_scroll
        if data_i >= total:
            break
        checked = tags[data_i]
        value   = tag_vals[data_i]
        cb      = "[x]" if checked else "[ ]"
        row     = tag_row(screen_i)
        write(stdscr, row, INNER_X,                cb,          c_check if checked else c_uncheck)
        write(stdscr, row, INNER_X + TAG_CB_W + 1, field(value), c_field)

    # Add button always sits at bottom of box
    write(stdscr, btn_row(n_vis), INNER_X, "[ + Add Tag ]", c_btn)

    # ── Hint bar ──────────────────────────────────────────────────────────────
    hint = " Click checkbox to select   Click field to edit   ↑↓ Scroll tags   q Quit "
    write(stdscr, h - 1, max(0, (w - len(hint)) // 2), hint[:w - 1], c_accent)

    stdscr.refresh()


# ── Click handler ─────────────────────────────────────────────────────────────

def on_click(stdscr, mx, my, state, colors):
    c_accent, c_normal, c_sel, _, c_check, c_field, c_uncheck = colors
    c_hint   = c_accent
    n_vis    = tags_visible(stdscr)
    t_scroll = state["tag_scroll"]
    tags     = state["tags_checked"]

    # API box
    if my == RULE34_ROW:
        if mx < INNER_X + CHECKBOX_W:
            state["selected_api"] = 0
        else:
            state["r34_key"] = inline_edit(stdscr, my, INNER_X + CHECKBOX_W + len(KEY_LABEL), state["r34_key"], c_sel, c_hint)

    elif my == GELBOORU_ROW:
        if mx < INNER_X + CHECKBOX_W:
            state["selected_api"] = 1
        else:
            state["gb_key"] = inline_edit(stdscr, my, INNER_X + CHECKBOX_W + len(KEY_LABEL), state["gb_key"], c_sel, c_hint)

    # Slideshow box
    elif my == SS_ROW and mx >= INNER_X + len(SS_LABEL):
        state["ss_interval"] = inline_edit(stdscr, my, INNER_X + len(SS_LABEL), state["ss_interval"], c_sel, c_hint)

    # Size box
    elif my == SIZE_ROW and mx >= INNER_X + len(SIZE_LABEL):
        state["size"] = inline_edit_size(stdscr, my, INNER_X + len(SIZE_LABEL), state["size"], c_sel, c_hint)

    # Additional Information box
    elif my == INFO_ROW and mx < INNER_X + len(SRC_LINK_CB):
        state["show_src_links"] = not state["show_src_links"]

    # Tags: individual rows
    elif tag_row(0) <= my < tag_row(n_vis):
        screen_i = my - tag_row(0)
        data_i   = screen_i + t_scroll
        if data_i >= len(tags):
            return
        if mx < INNER_X + TAG_CB_W:
            tags[data_i] = not tags[data_i]
        elif mx >= INNER_X + TAG_CB_W + 1:
            state["tag_values"][data_i] = inline_edit(
                stdscr, my, INNER_X + TAG_CB_W + 1,
                state["tag_values"][data_i], c_sel, c_hint
            )

    # Add tag button
    elif my == btn_row(n_vis) and INNER_X <= mx < INNER_X + len("[ + Add Tag ]"):
        state["tags_checked"].append(False)
        state["tag_values"].append("")
        # Auto-scroll to show the new tag
        total = len(state["tags_checked"])
        if total > n_vis:
            state["tag_scroll"] = total - n_vis


def scroll_tags(state, stdscr, direction):
    """Scroll tags up (-1) or down (+1), clamped to valid range."""
    n_vis = tags_visible(stdscr)
    total = len(state["tags_checked"])
    max_scroll = max(0, total - n_vis)
    state["tag_scroll"] = max(0, min(state["tag_scroll"] + direction, max_scroll))


# ── Entry point ───────────────────────────────────────────────────────────────

def open_settings(stdscr):
    curses.start_color()
    curses.use_default_colors()
    curses.curs_set(0)
    curses.mousemask(curses.ALL_MOUSE_EVENTS)

    curses.init_pair(1, curses.COLOR_CYAN,   -1)
    curses.init_pair(2, curses.COLOR_WHITE,  -1)
    curses.init_pair(3, curses.COLOR_BLACK,  curses.COLOR_CYAN)
    curses.init_pair(4, curses.COLOR_BLUE,   -1)
    curses.init_pair(5, curses.COLOR_YELLOW, -1)
    curses.init_pair(6, curses.COLOR_GREEN,  -1)
    curses.init_pair(7, curses.COLOR_YELLOW, -1)

    colors = (
        curses.color_pair(1) | curses.A_BOLD,
        curses.color_pair(2),
        curses.color_pair(3),
        curses.color_pair(4) | curses.A_BOLD,
        curses.color_pair(5) | curses.A_BOLD,
        curses.color_pair(6),
        curses.color_pair(7),
    )

    state = load_state()

    sys.stdout.write("\033[?2004h")
    sys.stdout.flush()

    while True:
        h, w = stdscr.getmaxyx()

        if w < MIN_W or h < MIN_H:
            draw_too_small(stdscr)
            key = stdscr.getch()
            if key == ord('q'):
                sys.stdout.write("\033[?2004l")
                sys.stdout.flush()
                break
            continue

        draw(stdscr, state, colors)
        key = stdscr.getch()

        if key == ord('q'):
            save_state(state)
            sys.stdout.write("\033[?2004l")
            sys.stdout.flush()
            break

        elif key == curses.KEY_RESIZE:
            # Clamp scroll in case terminal got smaller
            n_vis  = tags_visible(stdscr)
            total  = len(state["tags_checked"])
            state["tag_scroll"] = max(0, min(state["tag_scroll"], total - n_vis))

        elif key == curses.KEY_UP:
            scroll_tags(state, stdscr, -1)

        elif key == curses.KEY_DOWN:
            scroll_tags(state, stdscr, 1)

        elif key == curses.KEY_MOUSE:
            try:
                _, mx, my, _, bstate = curses.getmouse()
                # Mouse wheel scroll (button 4 = up, button 5 = down)
                if bstate & curses.BUTTON4_PRESSED:
                    scroll_tags(state, stdscr, -1)
                elif bstate & curses.BUTTON5_PRESSED:
                    scroll_tags(state, stdscr, 1)
                elif bstate & (curses.BUTTON1_CLICKED | curses.BUTTON1_PRESSED | curses.BUTTON1_RELEASED):
                    on_click(stdscr, mx, my, state, colors)
            except curses.error:
                pass

    return state