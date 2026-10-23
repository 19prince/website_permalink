from odoo import models


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    def _permalink_url(self):
        # categories have no website_url; this is the route website_sale serves them at
        self.ensure_one()
        return self.id and '/shop/category/%s' % self.env['ir.http']._slug(self)
