from odoo import models


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    def _permalink_live(self):
        # 20 derives is_published from has_published_products, but the category
        # page is reachable either way, so its URL is always worth keeping
        self.ensure_one()
        return True
