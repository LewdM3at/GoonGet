import curses
import sys
import json
from pathlib import Path

CONFIG_FILE = Path.home() / ".config" / "goonget" / "config.json"

# ── Config load / save ────────────────────────────────────────────────────────

def load_state():
    """Read config.json and map it to the UI state dict."""
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
        "selected_api": 0 if source == "rule34.xxx" else 1,
        "r34_key":      cfg.get("rule34_api_key", ""),
        "gb_key":       cfg.get("gelbooru_api_key", ""),
        "ss_interval":  str(cfg.get("slideshow_timer", "")),
        "size":         cfg.get("size", ""),
        "tags_checked": tags_checked,
        "tag_values":   tag_values,
    }


def save_state(state):
    """Write the UI state back to config.json, preserving any unrelated keys."""
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text())
        except json.JSONDecodeError:
            cfg = {}
    else:
        cfg = {}

    cfg["source"]           = "rule34.xxx" if state["selected_api"] == 0 else "gelbooru.com"
    cfg["rule34_api_key"]   = state["r34_key"]
    cfg["gelbooru_api_key"] = state["gb_key"]

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

TAGS_BOX_Y = SIZE_BOX_Y + SIZE_BOX_H + 1
TAG_CB_W   = len("[x] ")

MIN_FIELD = 10


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

def tags_box_h(tags):
    return len(tags) + 5

def tag_row(i):
    return TAGS_BOX_Y + 2 + i

def btn_row(tags):
    return TAGS_BOX_Y + 2 + len(tags) + 1


# ── Drawing helpers ───────────────────────────────────────────────────────────

def draw_box(stdscr, y, h, label, c_accent):
    _, w = stdscr.getmaxyx()
    bw      = w - 6
    section = f" {label} "
    top     = "┌─" + section + "─" * (bw - len(section) - 3) + "┐"
    stdscr.attron(c_accent)
    stdscr.addstr(y, BOX_X, top)
    for row in range(1, h - 1):
        stdscr.addstr(y + row, BOX_X,         "│")
        stdscr.addstr(y + row, BOX_X + bw - 1, "│")
    stdscr.addstr(y + h - 1, BOX_X, "└" + "─" * (bw - 2) + "┘")
    stdscr.attroff(c_accent)

def write(stdscr, row, col, text, attr):
    stdscr.attron(attr)
    stdscr.addstr(row, col, text)
    stdscr.attroff(attr)

def write_hint(stdscr, row, field_x, msg, c_hint):
    """Write a small hint message just below a field."""
    stdscr.attron(c_hint)
    stdscr.addstr(row + 1, field_x, msg)
    stdscr.attroff(c_hint)

def clear_hint(stdscr, row, field_x, width):
    """Erase the hint line so it doesn't linger."""
    stdscr.addstr(row + 1, field_x, " " * width)


# ── Inline field editor ───────────────────────────────────────────────────────

def inline_edit(stdscr, row, field_x, initial, c_sel, c_hint):
    """
    Generic inline editor. Shows 'Press Enter to confirm' while editing.
    Returns the new string value.
    """
    buf  = list(initial)
    hint = " Press ENTER to confirm "
    curses.curs_set(1)

    while True:
        _, w  = stdscr.getmaxyx()
        value    = "".join(buf)
        max_w    = w - field_x - 4
        display  = value[-max_w:] if len(value) > max_w else value
        rendered = "[ " + display + " ]"
        cursor_x = min(field_x + 2 + len(display), w - 2)

        stdscr.attron(c_sel)
        stdscr.addstr(row, field_x, rendered)
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
    """
    Size editor: only allows digits and one 'x'.
    Shows 'Press Enter to confirm' while editing,
    switches to an error if the format is wrong on confirm.
    """
    buf = list(initial)
    curses.curs_set(1)

    def allowed(ch, current):
        if ch.isdigit():
            return True
        if ch.lower() == 'x' and 'x' not in current.lower():
            return True
        return False

    hint    = " Press Enter to confirm "
    warning = " ✗ Format must be WxH (e.g. 1920x1080) "
    msg     = hint  # start with the normal hint

    while True:
        value    = "".join(buf)
        rendered = field(value)
        cursor_x = field_x + 2 + len(value)

        stdscr.attron(c_sel)
        stdscr.addstr(row, field_x, rendered)
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
            msg = warning  # swap hint to error, stay in edit mode
        elif ch in (curses.KEY_BACKSPACE, 127, 8):
            if buf:
                buf.pop()
            msg = hint  # reset to normal hint on any edit
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

    stdscr.attron(c_normal); stdscr.border(); stdscr.attroff(c_normal)
    write(stdscr, 0, (w - 20) // 2, " GoonGet — Settings ", c_accent)

    # API box
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

    # Slideshow box
    draw_box(stdscr, SS_BOX_Y, SS_BOX_H, "Slideshow", c_accent)
    write(stdscr, SS_ROW, INNER_X, SS_LABEL, c_normal)
    write(stdscr, SS_ROW, INNER_X + len(SS_LABEL), field(state["ss_interval"]), c_field)

    # Size box
    draw_box(stdscr, SIZE_BOX_Y, SIZE_BOX_H, "Size", c_accent)
    size_display = state["size"] if state["size"] else "Fill"
    write(stdscr, SIZE_ROW, INNER_X, SIZE_LABEL, c_normal)
    write(stdscr, SIZE_ROW, INNER_X + len(SIZE_LABEL), field(size_display), c_field)

    # Default Tags box
    tags = state["tags_checked"]
    draw_box(stdscr, TAGS_BOX_Y, tags_box_h(tags), "Default Tags", c_accent)
    for i, (checked, value) in enumerate(zip(tags, state["tag_values"])):
        cb = "[x]" if checked else "[ ]"
        write(stdscr, tag_row(i), INNER_X, cb, c_check if checked else c_uncheck)
        write(stdscr, tag_row(i), INNER_X + len(cb) + 1, field(value), c_field)
    write(stdscr, btn_row(tags), INNER_X, "[ + Add Tag ]", c_btn)

    hint = " Click checkbox to select   Click field to edit   q Quit "
    write(stdscr, h - 1, max(0, (w - len(hint)) // 2), hint[:w - 1], c_accent)

    stdscr.refresh()


# ── Click handler ─────────────────────────────────────────────────────────────

def on_click(stdscr, mx, my, state, colors):
    c_accent, c_normal, c_sel, _, c_check, c_field, c_uncheck = colors
    c_hint = c_accent  # reuse accent color for hints
    tags   = state["tags_checked"]

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

    elif my == SS_ROW and mx >= INNER_X + len(SS_LABEL):
        state["ss_interval"] = inline_edit(stdscr, my, INNER_X + len(SS_LABEL), state["ss_interval"], c_sel, c_hint)

    elif my == SIZE_ROW and mx >= INNER_X + len(SIZE_LABEL):
        state["size"] = inline_edit_size(stdscr, my, INNER_X + len(SIZE_LABEL), state["size"], c_sel, c_hint)

    elif tag_row(0) <= my < tag_row(len(tags)):
        i = my - tag_row(0)
        if mx < INNER_X + TAG_CB_W:
            tags[i] = not tags[i]
        elif mx >= INNER_X + TAG_CB_W + 1:
            state["tag_values"][i] = inline_edit(stdscr, my, INNER_X + TAG_CB_W + 1, state["tag_values"][i], c_sel, c_hint)

    elif my == btn_row(tags) and INNER_X <= mx < INNER_X + len("[ + Add Tag ]"):
        state["tags_checked"].append(False)
        state["tag_values"].append("")


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
    curses.init_pair(5, curses.COLOR_YELLOW, -1)  # checkbox checked
    curses.init_pair(6, curses.COLOR_GREEN,  -1)  # input fields
    curses.init_pair(7, curses.COLOR_YELLOW, -1)  # checkbox unchecked (dim = orange)

    colors = (
        curses.color_pair(1) | curses.A_BOLD,  # c_accent  — cyan bold
        curses.color_pair(2),                  # c_normal  — white
        curses.color_pair(3),                  # c_sel     — black on cyan
        curses.color_pair(4) | curses.A_BOLD,  # c_btn     — blue bold
        curses.color_pair(5) | curses.A_BOLD,  # c_check   — yellow bold (checked)
        curses.color_pair(6),                  # c_field   — green
        curses.color_pair(7),                  # c_uncheck — yellow dim = orange (unchecked)
    )

    state = load_state()

    sys.stdout.write("\033[?2004h")
    sys.stdout.flush()

    while True:
        draw(stdscr, state, colors)
        key = stdscr.getch()

        if key == ord('q'):
            save_state(state)
            sys.stdout.write("\033[?2004l")
            sys.stdout.flush()
            break

        elif key == curses.KEY_MOUSE:
            try:
                _, mx, my, _, bstate = curses.getmouse()
                if bstate & (curses.BUTTON1_CLICKED | curses.BUTTON1_PRESSED | curses.BUTTON1_RELEASED):
                    on_click(stdscr, mx, my, state, colors)
            except curses.error:
                pass

    return state