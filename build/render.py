"""Template script to render Markdown to HTML."""

import os
import re
import sys
import typing

import yaml

from jinja2 import Environment, BaseLoader, Template
from markdown import markdown
from markdown.extensions import Extension
from markdown.extensions.footnotes import FootnoteExtension
from markdown.extensions.md_in_html import MarkdownInHtmlExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.toc import TocExtension
from markdown_astdocs import AstdocsExtension
from markdown_img import ImgExtension
from markdown_insert import InsertExtension
from markdown_script import ScriptExtension
from pymdownx.caret import InsertSupExtension
from pymdownx.emoji import EmojiExtension, gemoji
from pymdownx.highlight import HighlightExtension
from pymdownx.superfences import SuperFencesCodeExtension, fence_div_format
from pymdownx.tilde import DeleteSubExtension
from yaml import Loader

# check extension respective documentations for configuration
exts: list[Extension] = [
    AstdocsExtension(),
    DeleteSubExtension(),
    EmojiExtension(emoji_index=gemoji),
    FootnoteExtension(BACKLINK_TEXT=""),
    HighlightExtension(use_pygments=False),
    ImgExtension(),
    InsertExtension(parent_path=os.path.dirname(os.path.realpath(sys.argv[1]))),
    InsertSupExtension(),
    MarkdownInHtmlExtension(),
    ScriptExtension(),
    SuperFencesCodeExtension(
        custom_fences=[
            {"name": "mermaid", "class": "mermaid", "format": fence_div_format}
        ]
    ),
    TableExtension(),
    TocExtension(),
]

# jinja2 template
jenv: Environment = Environment(loader=BaseLoader())
try:
    tmpl: Template = jenv.from_string(open(sys.argv[2]).read())
except IndexError:
    tmpl: Template = jenv.from_string(open("template.html").read())

# relative path
path: str = "/".join(sys.argv[1].lstrip("./").split("/")[:-1])

# raw markdown content
with open(sys.argv[1]) as f:
    text: str = f.read().strip()

# preprocess: extract front matter
meta: dict[str, typing.Any] = {}
rgxp: re.Pattern = re.compile(r"^---\n(.+?)\n---\n\n", flags=re.DOTALL)
if text.startswith("---"):
    try:
        meta = yaml.load(re.match(rgxp, text).group(1), Loader=Loader)
        text = re.sub(rgxp, "", text, count=1).strip()
    except AttributeError:
        pass

# preprocess: generate metadata if undefined
if "title" not in meta:
    meta["title"] = sys.argv[1].split("/")[-2].replace(".md", "").capitalize()
    meta["title"] = "Home" if meta["title"] == "." else meta["title"]
if "url" not in meta:
    cname = os.environ.get("CNAME", "http://localhost:8000").rstrip("/")
    title = re.sub("[^A-Za-z0-9 ]+", "", meta["title"]).replace(" ", "-").lower()
    meta["url"] = f"{cname}/{title}"

# process: convert the markdown
html: str = markdown(text, extensions=exts)

# postprocess: escape mermaid code blocks
html = re.sub(
    '(<div class="mermaid">.*?</div>)',
    r"<!-- htmlmin:ignore -->\n<!-- prettier-ignore -->\n\1\n<!-- htmlmin:ignore -->",
    html,
    flags=re.DOTALL,
)

# check for the presence of code and/or equations and/or mermaid blocks
pre = True if '<pre class="highlight">' in html else False
eqs = True if re.search(r"\$.*\$", html, flags=re.DOTALL) else False  # false positives
mmd = True if '<div class="mermaid">' in html else False

# render template/output to stdout and log to stderr
sys.stdout.write(
    tmpl.render(path=path, content=html, highlight=pre, katex=eqs, mermaid=mmd, **meta)
)
sys.stderr.write(f'{sys.argv[1].lstrip("./")}\n')
