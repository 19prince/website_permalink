{
    "name": "Website Permalink - Blog",
    "summary": "Add-on, installs automatically with Website Permalink + Blog. URL fields on blog post forms.",
    "version": "18.0.1.4.0",
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
