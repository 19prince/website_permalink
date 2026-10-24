from odoo import models


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    def _permalink_live(self):
        # 20 derives is_published from has_published_products, but the category
        # page is reachable either way, so its URL is always worth keeping
        self.ensure_one()
        return True

    def _permalink_trigger_fields(self):
        # the display name includes the parent names, and the URL every
        # ancestor's slug: moving a category renames it as far as URLs go
        return super()._permalink_trigger_fields() | {'parent_id'}

    def _permalink_dependents(self):
        descendants = self.search([('id', 'child_of', self.ids), ('id', 'not in', self.ids)])
        return super()._permalink_dependents() + [descendants]
