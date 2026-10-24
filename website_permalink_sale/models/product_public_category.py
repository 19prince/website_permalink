from odoo import models


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    def _permalink_url(self):
        # categories have no website_url; this is the route website_sale serves them at
        self.ensure_one()
        return self.id and '/shop/category/%s' % self.env['ir.http']._slug(self)

    def _permalink_trigger_fields(self):
        # the display name, and so every descendant's slug, includes the parent
        # names: moving a category renames it as far as its URL is concerned
        return super()._permalink_trigger_fields() | {'parent_id'}

    def _permalink_dependents(self):
        descendants = self.search([('id', 'child_of', self.ids), ('id', 'not in', self.ids)])
        return super()._permalink_dependents() + [descendants]
