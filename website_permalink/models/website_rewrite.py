from odoo import fields, models


class WebsiteRewrite(models.Model):
    _inherit = 'website.rewrite'

    permalink_managed = fields.Boolean(
        'Managed by Website Permalink', readonly=True, copy=False,
        help='Created by Website Permalink. Only these rules are retargeted or removed when '
             'the same page moves again; rules added by hand are never touched.')

    def init(self):
        # rules from versions before this flag existed carry the module's name prefix
        self.env.cr.execute(
            "UPDATE website_rewrite SET permalink_managed = TRUE "
            "WHERE name LIKE 'Permalink: %%' AND redirect_type = '301' "
            "AND permalink_managed IS NOT TRUE")

    def _permalink_record(self, rewrites):
        """Create the module's 301s and keep its earlier ones consistent.

        Maintenance stays inside the module's own rules on the same website
        (or the same all-websites scope): Odoo serves rules per website
        (website/models/ir_http.py `_serve_redirect`), so touching another
        website's rule, or one an administrator wrote, would change what that
        website serves.
        """
        Rewrite = self.sudo()
        managed = [('permalink_managed', '=', True)]
        moved_to = {(r['url_to'], r['website_id']) for r in rewrites}
        moved_from = {(r['url_from'], r['website_id']): r['url_to'] for r in rewrites}

        # a URL that is live again must not keep redirecting away (rename back = loop)
        stale = Rewrite.search(managed + [('url_from', 'in', [url for url, _w in moved_to])])
        stale.filtered(lambda r: (r.url_from, r.website_id.id or False) in moved_to).unlink()

        # collapse chains: an earlier rule pointing at a URL that just moved follows it
        chained = Rewrite.search(managed + [('url_to', 'in', [url for url, _w in moved_from])])
        for rule in chained:
            target = moved_from.get((rule.url_to, rule.website_id.id or False))
            if target:
                rule.url_to = target

        return Rewrite.create([dict(r, permalink_managed=True) for r in rewrites])
