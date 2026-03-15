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

  goonget | gg --size
      Show the current size of the image to be rendered in terminal.

  goonget | gg --slideshow, --ss
      Show the current timer for slideshow, how long each image stay displayed in seconds.

  goonget | gg --slideshow, --ss <tag1> <tag2> <tag3> ... <tag_n>
      Fetch the results and display them in slideshow mode.
      Exit the slideshow mode by pressing Enter.

  goonget | gg --source
      Show the current source, from which website GoonGet should fetch the images.

  goonget | gg --help, --h
      Show this help page.

Examples:
  goonget ................................... Search for random posts
  goonget --settings ........................ Open the settings page for GoonGet
  goonget overwatch ......................... Search for posts with the tag "overwatch"
  goonget blonde big_boobs .................. Search for posts with the tags "blonde" and "big_boobs"
  goonget "mercy_(overwatch)" -futanari ..... Search for posts with the tag "mercy_(overwatch) excluding posts with the tag "futanari"
  goonget mercy_.overwatch -futanari ........ Search for posts with the tag "mercy_(overwatch) excluding posts with the tag "futanari"
  goonget --ss k/da_series .................. Search for posts with the tag "k/da_series" and show the results in a slideshow.
  goonget --ss .............................. Show the current timer setting for slideshow mode.
  goonget --tags ............................ Show the list of default tag(s) stored in the config file
  goonget --size ............................ Show the current size of the image to be rendered in terminal.
  goonget --source .......................... Show the current source website.


Notes:
  • Default tags are automatically included in every search.
  • Tags passed directly on the command line DO NOT override or add to defaults.
""")
