from odoo import api, fields, models


class PermalinkPublishedMixin(models.AbstractModel):
    """Sticky "has ever been published" flag.

    Not added to website.published.mixin itself: a stored field on a shared
    mixin only gets a column in tables of modules loaded after this one, and
    blog/eCommerce load first. The bridges mix this into their models instead.
    """
    _name = 'website.permalink.published.mixin'
    _description = 'Website Permalink: publish history'

    permalink_was_published = fields.Boolean(
        'Has Been Published', readonly=True, copy=False,
        help='Set the first time this page is published and never cleared, so its URL '
             'is kept through renames even while it is unpublished.')

    def init(self):
        # backfill on install and every upgrade; only ever sets True, so rerunning is harmless
        if self._abstract or not self._auto:
            return
        self.env.cr.execute(
            f'UPDATE "{self._table}" SET permalink_was_published = TRUE '
            'WHERE is_published AND permalink_was_published IS NOT TRUE')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('is_published') or vals.get('website_published'):
                vals['permalink_was_published'] = True
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('is_published') or vals.get('website_published'):
            vals['permalink_was_published'] = True
        return super().write(vals)
