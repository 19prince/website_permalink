from odoo.tests import HttpCase, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestBlogPermalink(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.blog = cls.env['blog.blog'].create({'name': 'News'})
        cls.post = cls.env['blog.post'].create({'name': 'Old Title', 'blog_id': cls.blog.id, 'is_published': True})

    def _urls(self):
        # website_url is a non-stored compute: read it fresh, not from the cache
        self.env.invalidate_all()
        return self.blog._permalink_url(), self.post.website_url

    def test_blog_post_rename_keeps_url(self):
        url_before = self.post.website_url
        self.post.name = 'New Title'
        self.assertEqual(self.post.website_url, url_before)
        self.post.write({'name': 'Newest Title', 'permalink_update_url': True})
        self.assertIn('newest-title', self.post.website_url)
        self.assertTrue(self.env['website.rewrite'].search([('url_from', '=', url_before)]))

    def test_blog_rename_keeps_post_urls(self):
        before = self._urls()
        self.blog.name = 'Journal'
        self.assertEqual(self._urls(), before)

    def test_blog_change_url_redirects_its_posts(self):
        blog_url, post_url = self._urls()
        self.blog.write({'name': 'Journal', 'permalink_update_url': True})
        new_blog_url, new_post_url = self._urls()
        self.assertIn('journal', new_blog_url)
        self.assertNotEqual(new_post_url, post_url)
        Rewrite = self.env['website.rewrite']
        self.assertEqual(Rewrite.search([('url_from', '=', blog_url)]).url_to, new_blog_url)
        self.assertEqual(Rewrite.search([('url_from', '=', post_url)]).url_to, new_post_url)


@tagged('post_install', '-at_install')
class TestBlogPermalinkDialog(HttpCase):

    def test_dialog_and_unload(self):
        blog = self.env['blog.blog'].create({'name': 'News'})
        post = self.env['blog.post'].create({'name': 'Old Title', 'blog_id': blog.id, 'is_published': True})
        old_url = post.website_url
        self.start_tour('/odoo/action-website_blog.action_blog_post/%s' % post.id, 'website_permalink_dialog', login='admin')
        self.assertEqual(post.name, 'Renamed Again')
        # Change URL on the first save, Keep URL on the second
        self.assertIn('renamed-in-tour', post.website_url)
        self.assertTrue(self.env['website.rewrite'].search([('url_from', '=', old_url)]))
