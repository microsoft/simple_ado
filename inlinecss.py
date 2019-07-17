#!/usr/bin/env python3

"""Inline the CSS for all html files in the supplied folder."""

import os
import sys


def inline(folder):
    """Inline the CSS for all HTML files in the folder."""

    with open(os.path.join(folder, "style.css")) as style_file:
        style = f'<style>\n{style_file.read()}\n</style>'

    for dirpath, _, filenames in os.walk(folder):
        for filename in filenames:
            if not filename.endswith(".html") and not filename.endswith(".htm"):
                continue

            file_path = os.path.join(dirpath, filename)

            with open(file_path) as html_file:
                contents = html_file.read()

            contents = contents.replace('<link rel="stylesheet" href="style.css" type="text/css">', style)

            with open(file_path, 'w') as html_file:
                html_file.write(contents)


if __name__ == "__main__":
    inline(sys.argv[1])