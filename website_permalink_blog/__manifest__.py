{
    "name": "Website Permalink - Blog",
    "summary": "URL controls for website_permalink on Blog forms.",
    "version": "18.0.1.3.1",
    "category": "Website/Website",
    "license": "LGPL-3",
    "author": "19 Prince",
    "website": "https://www.19prince.com",
    "depends": ["website_permalink", "website_blog"],
    "data": ["views/views.xml"],
    "assets": {
        "web.assets_tests": ["website_permalink_blog/static/tests/**/*"],
    },
    "auto_install": True,
    "installable": True,
}
