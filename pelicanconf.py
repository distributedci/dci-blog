AUTHOR = "DCI"
SITENAME = "Distributed CI Blog"
SITEURL = ""

PATH = "content"

TIMEZONE = "EST"

DEFAULT_LANG = "en"

CATEGORY_FEED_RSS = 'feeds/{slug}.rss.xml'
FEED_RSS = "feeds/all.rss.xml"

# Blogroll
LINKS = (("Dashboard", "https://www.distributed-ci.io/"),)

# Social widget
SOCIAL = ()

DEFAULT_PAGINATION = False

# Uncomment following line if you want document-relative URLs when developing
# RELATIVE_URLS = True

THEME = "theme"

PLUGINS = ["readtime"]
MARKDOWN = {
    "extension_configs": {
        "markdown.extensions.admonition": {},
        "markdown.extensions.toc": {},
        "markdown.extensions.codehilite": {"css_class": "highlight"},
    }
}
