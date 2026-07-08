# mdforge

Converts Markdown files to PDF. That's it.

I got tired of setting up Pandoc + LaTeX every time I wanted a decent looking
PDF from a markdown file. The LaTeX dependency alone is like 2GB and half the
time something breaks because of a missing `.sty` package. So I wrote this
instead. One script, pip install the deps, done.

## Install

```bash
pip install -r requirements.txt
```

You need Python 3.10+.

## Usage

```bash
# convert a file
python mdcreate.py build notes.md

# choose a theme
python mdcreate.py build notes.md -t academic

# rebuild automatically when you save
python mdcreate.py watch draft.md

# get HTML instead of PDF
python mdcreate.py html notes.md
```

If your markdown has a `title` in the frontmatter, the output file gets named
after it (slugified). So a doc with `title: My Cool Project` becomes
`my-cool-project.pdf` instead of `notes.pdf`.

Title, author and date show up in the PDF header. If there's no frontmatter
it just uses the filename.

## Themes

Five built-in themes. Run `python mdcreate.py themes` to list them.

- **clean** - sans-serif, light, good default
- **academic** - serif, wider margins, centered title. looks like a paper
- **dark** - dark background. mostly useful for HTML export
- **minimal** - system font, tight spacing, no frills
- **newsletter** - editorial look with serif and gold accents

I might add custom theme loading from a CSS file at some point but honestly
these cover 90% of what I need.

## What it does under the hood

1. Reads the `.md` file and splits out any YAML frontmatter
2. Converts markdown to HTML with markdown2 (tables, code blocks, footnotes, etc)
3. Runs the HTML through a Jinja2 template with the selected theme CSS
4. Pygments handles syntax highlighting for code blocks
5. WeasyPrint renders the final HTML to PDF

## Known issues

- WeasyPrint can be annoying to install on some systems because of the cairo/pango
  dependencies. On Ubuntu you might need `apt install libpango-1.0-0 libpangocairo-1.0-0`.
  On Mac `brew install pango` usually does it.
- The watch mode sometimes triggers twice on a single save depending on your editor.
  It deduplicates by file hash so the PDF only rebuilds once, but you might see a
  brief flicker.
- Dark theme looks great in HTML but PDFs with dark backgrounds use a lot of ink
  if you print them (obviously).

## License

MIT. Do whatever you want with it.
