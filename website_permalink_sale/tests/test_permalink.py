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

    def test_publish_flag_is_sticky(self):
        draft = self.env['product.template'].create({'name': 'Draft', 'is_published': False})
        self.assertFalse(draft.permalink_was_published)
        draft.is_published = True
        draft.is_published = False
        self.assertTrue(draft.permalink_was_published)

    def test_unpublished_after_publish_keeps_url(self):
        self.product.is_published = False
        self.product.name = 'Renamed While Hidden'
        self.product.is_published = True
        self.assertEqual(self.product.website_url, self.old_url)

    def test_form_flags_rename_of_unpublished_live_page(self):
        self.product.is_published = False
        with Form(self.product) as form:
            form.name = 'Renamed While Hidden'
            self.assertTrue(form.permalink_name_changed)

    def test_form_ignores_rename_of_never_published_draft(self):
        draft = self.env['product.template'].create({'name': 'Draft', 'is_published': False})
        with Form(draft) as form:
            form.name = 'Final'
            self.assertFalse(form.permalink_name_changed)

    def test_unload_guard_field(self):
        # the browser blocks unload on a pending rename only when this names a field
        self.assertEqual(self.product.permalink_guard_field, 'name')
        draft = self.env['product.template'].create({'name': 'Draft', 'is_published': False})
        self.assertFalse(draft.permalink_guard_field)

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


@tagged('post_install', '-at_install')
class TestPermalinkRedirectScope(TransactionCase):
    """Redirect upkeep stays inside the module's own rules on the same website."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Rewrite = cls.env['website.rewrite']
        cls.site_a = cls.env['website'].search([], limit=1)
        cls.site_b = cls.env['website'].create({'name': 'Site B'})
        cls.product = cls.env['product.template'].create({
            'name': 'Old Name', 'is_published': True, 'website_id': cls.site_a.id})
        cls.old_url = '/shop/old-name-%s' % cls.product.id
        cls.new_url = '/shop/new-name-%s' % cls.product.id

    def _manual(self, url_from, url_to, website, redirect_type='301'):
        return self.Rewrite.create({
            'name': 'Manual', 'url_from': url_from, 'url_to': url_to,
            'redirect_type': redirect_type, 'website_id': website.id})

    def test_change_url_leaves_other_rules_alone(self):
        other_site_from_new = self._manual(self.new_url, '/elsewhere', self.site_b)
        other_site_to_old = self._manual('/campaign', self.old_url, self.site_b)
        same_site_manual_to_old = self._manual('/promo', self.old_url, self.site_a)
        same_site_rewrite = self._manual(self.new_url, '/landing', self.site_a, '308')

        self.product.write({'name': 'New Name', 'permalink_update_url': True})

        self.assertEqual(self.product.website_url, self.new_url)
        for rule, url_from, url_to in (
            (other_site_from_new, self.new_url, '/elsewhere'),
            (other_site_to_old, '/campaign', self.old_url),
            (same_site_manual_to_old, '/promo', self.old_url),
            (same_site_rewrite, self.new_url, '/landing'),
        ):
            self.assertTrue(rule.exists())
            self.assertEqual((rule.url_from, rule.url_to), (url_from, url_to))
        created = self.Rewrite.search([('url_from', '=', self.old_url), ('permalink_managed', '=', True)])
        self.assertEqual((created.url_to, created.website_id), (self.new_url, self.site_a))

    def test_managed_upkeep_only_on_same_website(self):
        # a managed rule on another website with the same URLs is that website's business
        foreign = self.Rewrite.create({
            'name': 'Permalink: elsewhere', 'url_from': self.new_url, 'url_to': '/x',
            'redirect_type': '301', 'website_id': self.site_b.id, 'permalink_managed': True})
        self.product.write({'name': 'New Name', 'permalink_update_url': True})
        self.assertTrue(foreign.exists())
        self.assertEqual(foreign.url_to, '/x')

    def test_rename_back_and_chain_on_one_website(self):
        self.product.write({'name': 'Second', 'permalink_update_url': True})
        second_url = self.product.website_url
        self.product.write({'name': 'Third', 'permalink_update_url': True})
        third_url = self.product.website_url
        managed = self.Rewrite.search([('permalink_managed', '=', True)])
        self.assertEqual(managed.filtered(lambda r: r.url_from == self.old_url).url_to, third_url)
        self.product.write({'name': 'Second', 'permalink_update_url': True})
        self.assertEqual(self.product.website_url, second_url)
        self.assertFalse(self.Rewrite.search([('url_from', '=', second_url), ('permalink_managed', '=', True)]))


@tagged('post_install', '-at_install')
class TestPermalinkLanguages(TransactionCase):
    """seo_name is translated: each language keeps or changes its own URL."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env['res.lang']._activate_lang('fr_FR')
        cls.Rewrite = cls.env['website.rewrite']
        # translated while still a draft, so setting up does not pin anything
        cls.product = cls.env['product.template'].create({'name': 'Chair'})
        cls.product.update_field_translations('name', {'fr_FR': 'Chaise'})
        cls.product.is_published = True
        cls.pid = cls.product.id

    def _url(self, lang):
        self.env.invalidate_all()
        return self.product.with_context(lang=lang).website_url

    def test_setup(self):
        self.assertEqual(self._url('en_US'), '/shop/chair-%s' % self.pid)
        self.assertEqual(self._url('fr_FR'), '/shop/chaise-%s' % self.pid)

    def test_keep_in_english_keeps_french(self):
        self.product.with_context(lang='en_US').name = 'Seat'
        self.assertEqual(self._url('en_US'), '/shop/chair-%s' % self.pid)
        self.assertEqual(self._url('fr_FR'), '/shop/chaise-%s' % self.pid)

    def test_keep_in_french_keeps_english(self):
        self.product.with_context(lang='fr_FR').name = 'Siege'
        self.assertEqual(self._url('fr_FR'), '/shop/chaise-%s' % self.pid)
        self.assertEqual(self._url('en_US'), '/shop/chair-%s' % self.pid)

    def test_change_in_french_only_moves_french(self):
        self.product.with_context(lang='en_US').name = 'Seat'  # pins both languages first
        self.product.with_context(lang='fr_FR').write({'name': 'Siege', 'permalink_update_url': True})
        self.assertEqual(self._url('fr_FR'), '/shop/siege-%s' % self.pid)
        self.assertEqual(self._url('en_US'), '/shop/chair-%s' % self.pid)
        rule = self.Rewrite.search([('url_from', '=', '/shop/chaise-%s' % self.pid)])
        self.assertEqual(rule.url_to, '/shop/siege-%s' % self.pid)
        self.assertFalse(self.Rewrite.search([('url_from', '=', '/shop/chair-%s' % self.pid)]))

    def test_change_in_english_first_rename_keeps_french(self):
        self.product.with_context(lang='en_US').write({'name': 'Seat', 'permalink_update_url': True})
        self.assertEqual(self._url('en_US'), '/shop/seat-%s' % self.pid)
        self.assertEqual(self._url('fr_FR'), '/shop/chaise-%s' % self.pid)


@tagged('post_install', '-at_install')
class TestPermalinkCategoryTree(TransactionCase):
    """A category's display name, and so its children's slugs, include parent names."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Category = cls.env['product.public.category']
        cls.parent = Category.create({'name': 'Furniture'})
        cls.child = Category.create({'name': 'Chairs', 'parent_id': cls.parent.id})
        cls.other = Category.create({'name': 'Outdoor'})
        cls.child_url = cls.child._permalink_url()
        cls.parent_url = cls.parent._permalink_url()

    def _url(self, category):
        # display names (and so slugs) are cached: read them fresh
        self.env.invalidate_all()
        return category._permalink_url()

    def test_parent_rename_keeps_child_url(self):
        self.parent.name = 'Home'
        self.assertEqual(self._url(self.parent), self.parent_url)
        self.assertEqual(self._url(self.child), self.child_url)

    def test_reparent_redirects_child(self):
        # from Odoo 20 the URL holds every ancestor's segment, so moving a
        # category moves its URL: the old one must 301 to the new path
        self.child.parent_id = self.other
        new_url = self._url(self.child)
        self.assertEqual(new_url, '/shop/category/outdoor-%s/chairs-%s' % (self.other.id, self.child.id))
        rule = self.env['website.rewrite'].search([('url_from', '=', self.child_url)])
        self.assertEqual(rule.url_to, new_url)

    def test_parent_change_url_redirects_child(self):
        # the parent's segment is part of the child's URL from Odoo 20 on: the
        # child keeps its own segment and gets a 301 for the new path
        self.parent.write({'name': 'Home', 'permalink_update_url': True})
        Rewrite = self.env['website.rewrite']
        new_parent_url, new_child_url = self._url(self.parent), self._url(self.child)
        self.assertEqual(new_child_url, '/shop/category/home-%s/chairs-%s' % (self.parent.id, self.child.id))
        self.assertEqual(Rewrite.search([('url_from', '=', self.parent_url)]).url_to, new_parent_url)
        self.assertEqual(Rewrite.search([('url_from', '=', self.child_url)]).url_to, new_child_url)


@tagged('post_install', '-at_install')
class TestPermalinkCopyAndBulk(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.products = cls.env['product.template'].create([
            {'name': 'Alpha', 'is_published': True},
            {'name': 'Beta', 'is_published': True},
            {'name': 'Gamma', 'is_published': True},
        ])

    def test_copy_of_pinned_record_follows_its_name(self):
        original = self.products[0]
        original.name = 'Alpha Renamed'
        self.assertEqual(original.seo_name, 'alpha')
        copy = original.copy()
        self.assertFalse(copy.seo_name)
        self.assertFalse(copy.permalink_was_published)
        copy.name = 'Fresh Draft'
        self.assertEqual(copy.website_url, '/shop/fresh-draft-%s' % copy.id)

    def test_copy_honours_explicit_slug(self):
        copy = self.products[0].copy({'seo_name': 'chosen'})
        self.assertEqual(copy.seo_name, 'chosen')

    def test_bulk_rename_keeps_every_url(self):
        before = {p.id: p.website_url for p in self.products}
        self.products.write({'name': 'Same New Name'})
        for product in self.products:
            self.assertEqual(product.website_url, before[product.id])
        self.assertFalse(self.env['website.rewrite'].search([('url_from', 'in', list(before.values()))]))

    def test_bulk_change_url_redirects_each(self):
        before = {p.id: p.website_url for p in self.products}
        self.products.write({'name': 'Same New Name', 'permalink_update_url': True})
        for product in self.products:
            rule = self.env['website.rewrite'].search([('url_from', '=', before[product.id])])
            self.assertEqual(rule.url_to, '/shop/same-new-name-%s' % product.id)
