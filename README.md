# Website Permalink

Keep a published page's URL when you rename it. Odoo 18.

Odoo builds product, category and blog post URLs from the name, so renaming one moves its URL and loses its links and search rankings. On rename, this module copies the old slug into `seo_name`, which core Odoo already uses for the URL, so the URL stays put.

## Modules

| Module | What it adds | Installs |
|---|---|---|
| `website_permalink` | The rule, the 301 handling, the save-time dialog | You install this |
| `website_permalink_sale` | URL fields + notice on product and eCommerce category forms | Automatically with eCommerce |
| `website_permalink_blog` | URL fields + notice on blog post forms | Automatically with Blog |

## Behaviour

- Saving a renamed published record opens a dialog: **Keep URL** (default) or **Change URL to match the new name**, with **Redirect the old URL (301)** pre-checked.
- Import, API and server actions never show the dialog and always keep the URL.
- Unpublished records follow their name freely.
- Editing the URL Slug directly adds a 301 from the old URL, unless unchecked.
- Redirect chains collapse to one hop; renaming back removes the reverse redirect.
- Website pages are untouched: their URL is already stored separately.

## Tests

```
odoo-bin -d <db> -i website_sale,website_blog,website_permalink --test-enable \
  --test-tags /website_permalink_sale,/website_permalink_blog --stop-after-init
```
