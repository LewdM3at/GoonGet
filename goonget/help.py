def print_help():
    print("""
GoonGet — Command Line Usage

Usage:
  goonget | gg <tag1> <tag2> <tag3> ... <tag_n>
      Fetch content using the provided tags. You can pass multiple tags.
      "-" prefix means exclude.
      !!! for character tags like character_(context), you must either pass the tag in quotation marks or replace parathesis with
          a dot in front of the context (see examples down below).

  goonget | gg --tags
      Show the list of default tags currently stored on your system.

  goonget | gg --tags-add <tag>
      Add a tag to your default tag list.

  goonget | gg --tags-remove <tag>
      Remove a tag from your default tag list.

  goonget | gg --size
      Show the current size of the image to be rendered in terminal.

  goonget | gg --size=AxB
  goonget | gg --size AxB
      Set the size of the render of the result in terminal.

  goonget | gg --help, --h
      Show this help page.

Examples:
  goonget ................................... Search for random posts
  goonget overwatch ......................... Search for posts with the tag "overwatch"
  goonget blonde big_boobs .................. Search for posts with the tags "blonde" and "big_boobs"
  goonget "mercy_(overwatch)" -futanari ..... Search for posts with the tag "mercy_(overwatch) excluding posts with the tag "futanari"
  goonget mercy_.overwatch -futanari ........ Search for posts with the tag "mercy_(overwatch) excluding posts with the tag "futanari"
  goonget --tags ............................ Shows the list of default tag(s) stored in the config file
  goonget --tags-add -ai_generated .......... Adds the tag "-ai_generated" to the list of default tag(s)
  goonget --tags-remove -ai_generated ....... Removes the tag "-at_generated" from the list of default tag(s)
  goonget --size ............................ Show the current size of the image to be rendered in terminal.
  goonget --size=20x40 ...................... Set the size of the render of the result in terminal to 20 x 40.
  goonget --size 20x40 ...................... Set the size of the render of the result in terminal to 20 x 40.
  goonget --size Fill ...................... Set the size of the render of the result in terminal to Fill (default).


Notes:
  • Default tags are automatically included in every search.
  • Tags passed directly on the command line DO NOT override or add to defaults.
""")
