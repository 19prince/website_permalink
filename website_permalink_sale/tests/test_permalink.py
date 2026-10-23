from odoo.tests import Form, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPermalink(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.slug = cls.env['ir.http']._slug
        cls.Rewrite = cls.env['website.rewrite']
        cls.product = cls.env['product.template'].create({'name': 'Old Wheel Name', 'is_published': True})
        cls.old_url = '/shop/old-wheel-name-%s' % cls.product.id

    def _rewrites(self, url_from):
        return self.Rewrite.search([('url_from', '=', url_from)])

    def test_rename_keeps_url(self):
        self.product.name = 'New Wheel Name'
        self.assertEqual(self.product.website_url, self.old_url)
        self.assertEqual(self.product.seo_name, 'old-wheel-name')
        # no redirect at all: the pin used to 301 the new name's URL back to the old one
        self.assertFalse(self.Rewrite.search([('url_to', '=', self.old_url)]))
        self.assertFalse(self._rewrites(self.old_url))

    def test_second_rename_keeps_first_url(self):
        self.product.name = 'Second Name'
        self.product.name = 'Third Name'
        self.assertEqual(self.product.website_url, self.old_url)

    def test_unpublished_url_follows_name(self):
        draft = self.env['product.template'].create({'name': 'Draft', 'is_published': False})
        draft.name = 'Final'
        self.assertFalse(draft.seo_name)
        self.assertEqual(draft.website_url, '/shop/final-%s' % draft.id)

    def test_unrelated_write_does_not_pin(self):
        self.product.description_sale = 'x'
        self.assertFalse(self.product.seo_name)

    def test_change_url_adds_301(self):
        self.product.write({'name': 'New Wheel Name', 'permalink_update_url': True})
        new_url = '/shop/new-wheel-name-%s' % self.product.id
        self.assertEqual(self.product.website_url, new_url)
        rewrite = self._rewrites(self.old_url)
        self.assertEqual((rewrite.url_to, rewrite.redirect_type), (new_url, '301'))

    def test_change_url_after_earlier_pin(self):
        self.product.name = 'Second Name'
        self.product.write({'name': 'Third Name', 'permalink_update_url': True})
        self.assertEqual(self.product.website_url, '/shop/third-name-%s' % self.product.id)
        self.assertTrue(self._rewrites(self.old_url))

    def test_change_url_without_redirect(self):
        self.product.write({'name': 'New Wheel Name', 'permalink_update_url': True, 'permalink_redirect': False})
        self.assertNotEqual(self.product.website_url, self.old_url)
        self.assertFalse(self._rewrites(self.old_url))

    def test_rename_back_does_not_loop(self):
        self.product.write({'name': 'New Wheel Name', 'permalink_update_url': True})
        new_url = self.product.website_url
        self.product.write({'name': 'Old Wheel Name', 'permalink_update_url': True})
        self.assertEqual(self.product.website_url, self.old_url)
        self.assertFalse(self._rewrites(self.old_url))
        self.assertEqual(self._rewrites(new_url).url_to, self.old_url)

    def test_redirect_chain_collapses(self):
        self.product.write({'name': 'Second Name', 'permalink_update_url': True})
        self.product.write({'name': 'Third Name', 'permalink_update_url': True})
        self.assertEqual(self._rewrites(self.old_url).url_to, self.product.website_url)

    def test_slug_edit_adds_301(self):
        self.product.seo_name = 'chosen-url'
        self.assertEqual(self.product.website_url, '/shop/chosen-url-%s' % self.product.id)
        self.assertEqual(self._rewrites(self.old_url).url_to, self.product.website_url)

    def test_import_keeps_url(self):
        xid = self.product.get_external_id()[self.product.id] or '__export__.permalink_test'
        if not self.product.get_external_id()[self.product.id]:
            self.env['ir.model.data'].create({
                'module': '__export__', 'name': 'permalink_test',
                'model': 'product.template', 'res_id': self.product.id})
        result = self.env['product.template'].load(['id', 'name'], [[xid, 'Imported Name']])
        self.assertFalse(result['messages'])
        self.assertEqual(self.product.name, 'Imported Name')
        self.assertEqual(self.product.website_url, self.old_url)

    def test_form_flags_rename(self):
        with Form(self.product) as form:
            self.assertFalse(form.permalink_name_changed)
            form.name = 'New Wheel Name'
            self.assertTrue(form.permalink_name_changed)
            self.assertEqual(form.permalink_url, self.old_url)
        self.assertEqual(self.product.website_url, self.old_url)

    def test_category_rename_keeps_url(self):
        category = self.env['product.public.category'].create({'name': 'Old Category'})
        url_before = category._permalink_url()
        category.name = 'New Category'
        self.assertEqual(category._permalink_url(), url_before)
        category.write({'name': 'Newer Category', 'permalink_update_url': True})
        self.assertEqual(self._rewrites(url_before).url_to, category._permalink_url())
