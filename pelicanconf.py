AUTHOR = "DCI"
SITENAME = "Distributed CI Blog"
SITEURL = ""

PATH = "content"

TIMEZONE = "EST"

DEFAULT_LANG = "en"

FEED_DOMAIN = SITEURL
CATEGORY_FEED_RSS = 'feeds/{slug}.rss.xml'
FEED_RSS = "feeds/all.rss.xml"
FEED_ALL_ATOM = "feeds/all.atom.xml"
CATEGORY_FEED_ATOM = "feeds/{slug}.atom.xml"

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
