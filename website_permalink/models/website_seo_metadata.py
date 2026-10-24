from odoo import api, fields, models


class WebsiteSeoMetadata(models.AbstractModel):
    _inherit = 'website.seo.metadata'

    # form-only helpers: never stored, consumed by write()
    permalink_url = fields.Char('Permalink URL', compute='_compute_permalink_url')
    permalink_name_changed = fields.Boolean(compute='_compute_permalink_changed')
    permalink_slug_changed = fields.Boolean(compute='_compute_permalink_changed')
    permalink_update_url = fields.Boolean(
        'Change URL to match the new name', compute='_compute_permalink_options', readonly=False,
        help='Renaming a page that has been published keeps its URL by default. Pass True in the '
             'same write as the new name to move the URL to match it instead. AI agents and API '
             'clients: ask the user before setting this, since moving a URL affects links and '
             'search rankings.')
    permalink_redirect = fields.Boolean(
        'Redirect old URL (301)', compute='_compute_permalink_options', readonly=False,
        help='When a URL moves (permalink_update_url, or a seo_name edit), a 301 redirect from '
             'the old URL is added unless this is False. AI agents and API clients: ask the user '
             'before passing False.')

    def _permalink_url(self):
        """Public URL this record is served at, or False when it has none.

        Bridges override this for models without website_url (categories).
        """
        self.ensure_one()
        return 'website_url' in self._fields and self.website_url

    def _permalink_live(self):
        """Whether this record's URL has ever been public and so is worth keeping.

        Models without a publish flag (categories) are always live. Checked here
        rather than overridden in website.permalink.published.mixin: models list
        the SEO mixin first, so an override there would never be reached.
        """
        self.ensure_one()
        if 'permalink_was_published' in self._fields:
            return self.is_published or self.permalink_was_published
        # models without a bridge (events, ...): live only while published
        return self.is_published if 'is_published' in self._fields else True

    def _compute_permalink_url(self):
        for rec in self:
            # the saved URL, so the form shows what visitors use until save
            rec.permalink_url = rec._origin.id and rec._origin._permalink_url()

    @api.depends(lambda self: (self._rec_name, 'seo_name') if self._rec_name else ('seo_name',))
    def _compute_permalink_changed(self):
        for rec in self:
            origin = rec._origin
            rec.permalink_name_changed = bool(
                origin.id and rec._rec_name and rec[rec._rec_name] != origin[rec._rec_name]
                and origin._permalink_live())
            rec.permalink_slug_changed = bool(origin.id and rec.seo_name != origin.seo_name)

    @api.depends()
    def _compute_permalink_options(self):
        self.permalink_update_url = False
        self.permalink_redirect = True

    def write(self, vals):
        """Keep a published record's URL when its name changes.

        Core already builds the slug from seo_name when it is set
        (website/models/ir_http.py `_slug`), so pinning the old slug there is
        the whole permalink: no _slug override, and every model with SEO
        metadata is covered.

        Without the form flags (import, API, server actions) the URL is always
        kept, so a bulk rename can never move URLs. When a URL does move, a 301
        from the old one is added unless permalink_redirect is False.
        """
        update_url = vals.pop('permalink_update_url', False)
        redirect = vals.pop('permalink_redirect', True)
        for helper in ('permalink_url', 'permalink_name_changed', 'permalink_slug_changed'):
            vals.pop(helper, None)

        name_fields = {dep.split('.')[0] for dep in self.pool.field_depends[self._fields['display_name']]}
        renaming = bool(name_fields & vals.keys())
        if renaming and update_url and 'seo_name' not in vals:
            vals['seo_name'] = False

        old = {}
        if renaming or 'seo_name' in vals:
            # never-published drafts are skipped: nobody has linked to them yet
            for rec in self:
                if rec.id and rec._permalink_live() and rec._permalink_url():
                    old[rec.id] = (rec._permalink_url(), rec.display_name, rec.seo_name)

        res = super().write(vals)
        if not old:
            return res

        slugify = self.env['ir.http']._slugify
        if 'website_url' in self._fields:
            self.invalidate_recordset(['website_url'])
        rewrites = []
        for rec in self.browse(list(old)):
            old_url, old_name, old_seo_name = old[rec.id]
            if 'seo_name' not in vals and not old_seo_name:
                old_slug = slugify(old_name or '')
                if old_slug and old_slug != slugify(rec.display_name or ''):
                    # this re-enters write() as a slug edit; without the flag it would
                    # 301 the brand-new name's URL (never served) to the pinned one
                    rec.write({'seo_name': old_slug, 'permalink_redirect': False})
                    if 'website_url' in self._fields:
                        rec.invalidate_recordset(['website_url'])
            new_url = rec._permalink_url()
            if redirect and new_url and new_url != old_url:
                rewrites.append({
                    'name': 'Permalink: %s' % rec.display_name,
                    'url_from': old_url,
                    'url_to': new_url,
                    'redirect_type': '301',
                    'website_id': 'website_id' in rec._fields and rec.website_id.id,
                })
        if rewrites:
            Rewrite = self.env['website.rewrite'].sudo()
            # a URL that is live again must not keep redirecting away (rename back = loop)
            Rewrite.search([('url_from', 'in', [r['url_to'] for r in rewrites])]).unlink()
            # collapse chains: anything pointing at a URL that just moved now points at its new home
            for r in rewrites:
                Rewrite.search([('url_to', '=', r['url_from'])]).write({'url_to': r['url_to']})
            Rewrite.create(rewrites)
        return res
