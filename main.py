#!/usr/bin/env python3

import sys
from creds_handler import load_api_credentials
from tag_handler import get_default_tags, add_default_tag, remove_default_tag, build_tags
from api_calls import fetch_posts
from display_handler import display_result

def main():
    args = sys.argv[1:]

    # HANDLE SPECIAL TAG COMMANDS
    # show default tags
    if args and args[0] == "--tags":
        tags = get_default_tags()
        print("Default Tags:", ", ".join(tags) if tags else "(none)")
        return
    # add default tag(s)
    if args and args[0] == "--tags-add" and len(args) > 1: 
        add_default_tag(args[1]) 
        print(f"Added Tag(s): {args[1]}") 
        return

    # Remove tag(s)
    if args and args[0] == "--tags-remove" and len(args) > 1: 
        remove_default_tag(args[1]) 
        print(f"Removed Tag(s): {args[1]}") 
        return

    # NORMAL MODE
    # API Credentials check
    api_credentials = load_api_credentials()

    # build tags
    final_tags = build_tags(args)


    # get img/gif/video url
    result_url = fetch_posts(api_credentials, final_tags)

    if not result_url:
        print("No results found.")
        return
    else:
        display_result(result_url)


if __name__ == "__main__":
    main()
