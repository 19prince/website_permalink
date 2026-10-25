# Website Permalink

Keep a published page's URL when you rename it. Odoo 19.

Branches: [`18.0`](https://github.com/19prince/website_permalink/tree/18.0), [`19.0`](https://github.com/19prince/website_permalink/tree/19.0), [`20.0`](https://github.com/19prince/website_permalink/tree/20.0). Use the branch that matches your Odoo version.

Odoo builds product, category and blog post URLs from the name, so renaming one moves its URL and loses its links and search rankings. On rename, this module copies the old slug into `seo_name`, which core Odoo already uses for the URL, so the URL stays put.

## Which module do I install?

**Install `Website Permalink` only.** The other two are add-ons that install themselves when they are needed. You never install them by hand.

| Module | Install it? | What it does |
|---|---|---|
| **Website Permalink** (`website_permalink`) | **Yes. This is the one you install.** | The rules: keeps URLs on rename, adds 301s when a URL moves, shows the pop-up on save. Needs only the Website app. |
| Website Permalink - eCommerce (`website_permalink_sale`) | No, automatic | Adds the URL fields and rename notice to product and eCommerce category forms. Installs itself when Website Permalink **and** eCommerce are both installed. |
| Website Permalink - Blog (`website_permalink_blog`) | No, automatic | Adds the URL fields and rename notice to blog post forms. Installs itself when Website Permalink **and** Blog are both installed. |

### Why three modules

Products live in the eCommerce app and blog posts in the Blog app. If one module covered both, every database would have to install both apps, even a shop with no blog. Splitting them means each add-on only appears where its app exists. This is Odoo's standard "bridge module" pattern.

### What you get in each setup

| Your database has | Installed after you install Website Permalink | Covered |
|---|---|---|
| Website only | Website Permalink | Rules only (no forms to add fields to) |
| Website + Blog | Website Permalink + Blog add-on | Blog posts |
| Website + eCommerce | Website Permalink + eCommerce add-on | Products, eCommerce categories |
| Website + Blog + eCommerce | All three | Blog posts, products, eCommerce categories |

Install Blog or eCommerce later and its add-on installs itself then. To remove everything, uninstall **Website Permalink**; the add-ons go with it.

## Installation

### Odoo.sh / on-premise

1. Copy the three folders (`website_permalink/`, `website_permalink_blog/`, `website_permalink_sale/`) into your addons path. On Odoo.sh, commit them to the branch that backs your build.
2. In developer mode, go to **Apps > Update Apps List**.
3. In Apps, remove the **Apps** filter, search **"permalink"**, and install **Website Permalink**. The add-ons follow on their own.
4. Hard refresh the backend (Cmd/Ctrl+Shift+R) so the rename pop-up loads.

Nothing changes on install: every URL stays what it is today. The module only acts on the next rename.

### Odoo Online (SaaS)

Odoo Online doesn't allow custom Python modules, so this can't be installed there.

### Uninstalling

URLs stay where they are. Pinned slugs live in Odoo's own URL Slug field (`seo_name`) and redirects stay under **Website > Configuration > Redirects**. After uninstalling, renames move URLs again, as in standard Odoo.

## Behaviour

- Saving a renamed published record opens a dialog: **Keep URL** (default) or **Change URL to match the new name**, with **Redirect the old URL (301)** pre-checked.
- Import, API and server actions never show the dialog and always keep the URL.
- Pages never published follow their name freely. Once a page has been published (blog posts and products track this), its URL is kept even while unpublished. Other models keep it only while published.
- Editing the URL Slug directly adds a 301 from the old URL, unless unchecked.
- Redirect chains collapse to one hop; renaming back removes the reverse redirect.
- Website pages are untouched: their URL is already stored separately.

## For AI agents and API clients

Renames through the API, imports or an MCP server never show the dialog, so the URL is always kept. Before you rename a published page, product or category:

1. **Ask the user** whether the URL should stay or change to match the new name.
2. To change it, send `permalink_update_url: true` in the same `write` as the new name.
3. A 301 redirect from the old URL is added automatically. Send `permalink_redirect: false` only if the user explicitly says not to redirect.

```python
record.write({'name': 'New Title', 'permalink_update_url': True})  # URL follows the new name, old URL 301s
record.write({'name': 'New Title'})                                # URL kept (default)
```

## Known limitations

- **Moving a page to another website in the same save as a rename.** The 301 is created on the new website only. The old website gets no redirect for that URL; Odoo's ID-based lookup still finds the page if it is still visible there.
- **Moving a blog post to a different blog.** On standard Odoo a post URL contains its blog (`/blog/news-1/my-post-5`), so moving the post to another blog changes its URL (`/blog/journal-2/my-post-5`). The module does not treat that as a rename: no dialog and no 301, though Odoo's ID-based lookup still lands old links on the post. With [Odoo Blog Flat URLs](https://github.com/19prince/Odoo-Blog-Flat-URLs) installed this cannot happen: posts are served at `/blog/my-post-5`, with no blog in the URL, so moving a post between blogs leaves its URL alone (and renaming a blog never touches post URLs either).
- **Performance is not benchmarked.** Each language has its own URL (`/shop/chair-12`, `/fr/shop/chaise-12`), so a rename reads and pins the URL once per installed language, and renaming a blog or a parent category also checks every post or subcategory under it. On a single-language site this is one read per page, as before. Large blog renames or bulk renames by import on multi-language sites may be noticeably slower; measure before rolling out to a big catalog.

## Tests

```
odoo-bin -d <db> -i website_sale,website_blog,website_permalink --test-enable \
  --test-tags /website_permalink_sale,/website_permalink_blog --stop-after-init
```

## License

LGPL-3. See [LICENSE](LICENSE).

## About 19 Prince

[19 Prince](https://www.19prince.com) helps businesses on Odoo drive more demand with the tool they already own. More free modules: [19prince.com/resources](https://www.19prince.com/resources).
