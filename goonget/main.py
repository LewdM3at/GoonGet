#!/usr/bin/env python3

import sys
import random
import curses
from .api_calls import fetch_posts
from .display_handler import display_result, display_slideshow
from .help import print_help
from .settings_ncurses import open_settings
from .settings_handler import (
    load_api_credentials,
    get_default_tags, add_default_tag, remove_default_tag, build_tags,
    get_source, set_source, get_current_size, set_size,
    get_slideshow_timer, set_slideshow_timer,
)

def main():
    args = sys.argv[1:]

    # HANDLE SPECIAL TAG COMMANDS
    # open settings page
    if args and args[0] == "--settings":
        curses.wrapper(open_settings)
        return
    # show default tags
    if args and args[0] == "--tags":
        tags = get_default_tags()
        print("Default Tags:", ", ".join(tags) if tags else "(none)")
        return

    # show help page
    if args and args[0] in ("--help", "--h"):
        print_help()
        return

    # result size setting
    if args and args[0].startswith("--size"):
        # Case A: --size (no value)
        if args[0] == "--size" and len(args) == 1:
            current_size = get_current_size()
            print(f"Current size: {current_size}")
            return

        # Case B: --size=AxB
        if "=" in args[0]:
            _, value = args[0].split("=", 1)
            set_size(value)
            print(f"Updated size to: {value}")
            return

        # Case C: --size AxB
        if args[0] == "--size" and len(args) > 1:
            value = args[1]
            set_size(value)
            print(f"Updated size to: {value}")
            return

    # no query → show configured timer
    if args[0] in ("--ss", "--slideshow") and len(args) == 1:
        print(f"Slideshow timer: {get_slideshow_timer()} seconds")
        return

    # flag to use the slideshow
    if args[0] in ("--ss", "--slideshow") and len(args) > 1:
        # API Credentials check
        api_credentials = load_api_credentials()
        # build tags
        final_tags = build_tags(args[1:])
        # get img/gif/video url
        urls = fetch_posts(api_credentials, final_tags)
        # filter out GIFs 
        urls = [u for u in urls if not u.lower().endswith(".gif")]
        display_slideshow(urls)
        return

    # get source
    if args and args[0] == "--source":
        print(f"Current source: {get_source()}")
        return

    # NORMAL MODE
    # API Credentials check
    api_credentials = load_api_credentials()
    # build tags
    final_tags = build_tags(args)
    print(final_tags)
    # get img/gif/video url
    urls = fetch_posts(api_credentials, final_tags)

    if not urls:
        print("No results found.")
        return
    
    # pick one random result 
    result_url = random.choice(urls) 
    display_result(result_url)


if __name__ == "__main__":
    main()
