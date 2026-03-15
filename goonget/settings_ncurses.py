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

    # Support both old format (plain strings) and new format ({"tag": ..., "active": ...})
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

    # Save all non-empty tags with their active state as objects
    cfg["default_tags"] = [
        {"tag": v.strip(), "active": checked}
        for checked, v in zip(state["tags_checked"], state["tag_values"])
        if v.strip()
    ]

    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=4))



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

TAGS_BOX_Y = SS_BOX_Y + SS_BOX_H + 1
TAG_CB_W   = len("[x] ")

MIN_FIELD = 10  # minimum field width when empty


# ── Pure helpers (no curses, no state) ───────────────────────────────────────

def field(value):
    """Render [ value ] — default MIN_FIELD spacing when empty, 1 space each side when not."""
    if not value:
        return "[ " + " " * MIN_FIELD + " ]"
    return "[ " + value + " ]"

def field_truncated(value, max_width):
    """Like field() but clips to max_width chars, appending ... if clipped."""
    if not value:
        return "[ " + " " * min(MIN_FIELD, max_width) + " ]"
    if len(value) > max_width:
        value = value[:max_width - 3] + "..."
    return "[ " + value + " ]"

def tags_box_h(tags):
    # top border + pad + N rows + button row + pad + bottom border
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


# ── Inline field editor ───────────────────────────────────────────────────────

def inline_edit(stdscr, row, field_x, initial, c_sel):
    """Edit a field in-place. Returns the new string value."""
    buf = list(initial)
    curses.curs_set(1)

    while True:
        value    = "".join(buf)
        rendered = field(value)
        cursor_x = field_x + 2 + len(value)  # skip "[ "

        stdscr.attron(c_sel)
        stdscr.addstr(row, field_x, rendered)
        stdscr.attroff(c_sel)
        stdscr.move(row, cursor_x)
        stdscr.refresh()

        ch = stdscr.getch()

        if ch == 27:  # ESC or bracketed paste
            stdscr.nodelay(True)
            seq = []
            while True:
                nc = stdscr.getch()
                if nc == -1:
                    break
                seq.append(chr(nc) if 0 <= nc < 256 else "")
            stdscr.nodelay(False)
            seq_str = "".join(seq)
            if "[200~" in seq_str:  # bracketed paste — auto confirm
                pasted = seq_str.split("[200~", 1)[-1].split("[201~")[0]
                buf.extend(c for c in pasted if 32 <= ord(c) <= 126)
                break
            else:  # plain ESC — cancel
                buf = list(initial)
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


# ── Main draw ─────────────────────────────────────────────────────────────────

def draw(stdscr, state, colors):
    c_accent, c_normal, c_sel, c_btn = colors
    h, w = stdscr.getmaxyx()
    stdscr.erase()

    # Outer border + title
    stdscr.attron(c_normal); stdscr.border(); stdscr.attroff(c_normal)
    write(stdscr, 0, (w - 20) // 2, " GoonGet — Settings ", c_accent)

    # API box
    draw_box(stdscr, API_BOX_Y, API_BOX_H, "API", c_accent)
    r34_cb = "[x]" if state["selected_api"] == 0 else "[ ]"
    gb_cb  = "[x]" if state["selected_api"] == 1 else "[ ]"
    # max chars the key field can show before hitting the box border (│)
    key_field_start = INNER_X + CHECKBOX_W + len(KEY_LABEL)
    key_max_w = w - 6 - key_field_start - 4  # 4 = "[ " + " ]"
    write(stdscr, RULE34_ROW,   INNER_X, f"{r34_cb} Rule34.xxx", c_normal)
    write(stdscr, RULE34_ROW,   INNER_X + CHECKBOX_W, KEY_LABEL + field_truncated(state["r34_key"], key_max_w), c_normal)
    write(stdscr, GELBOORU_ROW, INNER_X, f"{gb_cb} Gelbooru.com", c_normal)
    write(stdscr, GELBOORU_ROW, INNER_X + CHECKBOX_W, KEY_LABEL + field_truncated(state["gb_key"], key_max_w), c_normal)

    # Slideshow box
    draw_box(stdscr, SS_BOX_Y, SS_BOX_H, "Slideshow", c_accent)
    write(stdscr, SS_ROW, INNER_X, SS_LABEL + field(state["ss_interval"]), c_normal)

    # Default Tags box
    tags = state["tags_checked"]
    draw_box(stdscr, TAGS_BOX_Y, tags_box_h(tags), "Default Tags", c_accent)
    for i, (checked, value) in enumerate(zip(tags, state["tag_values"])):
        cb = "[x]" if checked else "[ ]"
        write(stdscr, tag_row(i), INNER_X, cb + " " + field(value), c_normal)
    write(stdscr, btn_row(tags), INNER_X, "[ + Add Tag ]", c_btn)

    # Hint bar
    hint = " Click checkbox to select   Click field to edit   q Quit "
    write(stdscr, h - 1, max(0, (w - len(hint)) // 2), hint[:w - 1], c_accent)

    stdscr.refresh()


# ── Click handler ─────────────────────────────────────────────────────────────

def on_click(stdscr, mx, my, state, colors):
    _, c_normal, c_sel, _ = colors
    tags = state["tags_checked"]

    if my == RULE34_ROW:
        if mx < INNER_X + CHECKBOX_W:
            state["selected_api"] = 0
        elif mx >= INNER_X + CHECKBOX_W + len(KEY_LABEL):
            state["r34_key"] = inline_edit(stdscr, my, INNER_X + CHECKBOX_W + len(KEY_LABEL), state["r34_key"], c_sel)

    elif my == GELBOORU_ROW:
        if mx < INNER_X + CHECKBOX_W:
            state["selected_api"] = 1
        elif mx >= INNER_X + CHECKBOX_W + len(KEY_LABEL):
            state["gb_key"] = inline_edit(stdscr, my, INNER_X + CHECKBOX_W + len(KEY_LABEL), state["gb_key"], c_sel)

    elif my == SS_ROW and mx >= INNER_X + len(SS_LABEL):
        state["ss_interval"] = inline_edit(stdscr, my, INNER_X + len(SS_LABEL), state["ss_interval"], c_sel)

    elif tag_row(0) <= my < tag_row(len(tags)):
        i = my - tag_row(0)
        if mx < INNER_X + TAG_CB_W:
            tags[i] = not tags[i]
        elif mx >= INNER_X + TAG_CB_W + 1:
            state["tag_values"][i] = inline_edit(stdscr, my, INNER_X + TAG_CB_W + 1, state["tag_values"][i], c_sel)

    elif my == btn_row(tags) and INNER_X <= mx < INNER_X + len("[ + Add Tag ]"):
        state["tags_checked"].append(False)
        state["tag_values"].append("")


# ── Entry point ───────────────────────────────────────────────────────────────

def open_settings(stdscr):
    curses.start_color()
    curses.use_default_colors()
    curses.curs_set(0)
    curses.mousemask(curses.ALL_MOUSE_EVENTS)

    colors = (
        curses.color_pair(1) | curses.A_BOLD,  # c_accent — cyan bold
        curses.color_pair(2),                  # c_normal — white
        curses.color_pair(3),                  # c_sel    — black on cyan
        curses.color_pair(4) | curses.A_BOLD,  # c_btn    — blue bold
    )

    curses.init_pair(1, curses.COLOR_CYAN,  -1)
    curses.init_pair(2, curses.COLOR_WHITE, -1)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(4, curses.COLOR_BLUE,  -1)

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
                if bstate & curses.BUTTON1_CLICKED:
                    on_click(stdscr, mx, my, state, colors)
            except curses.error:
                pass

    return state