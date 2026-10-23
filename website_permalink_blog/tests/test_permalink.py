from odoo.tests import HttpCase, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestBlogPermalink(TransactionCase):

    def test_blog_post_rename_keeps_url(self):
        blog = self.env['blog.blog'].create({'name': 'News'})
        post = self.env['blog.post'].create({'name': 'Old Title', 'blog_id': blog.id, 'is_published': True})
        url_before = post.website_url
        post.name = 'New Title'
        self.assertEqual(post.website_url, url_before)
        post.write({'name': 'Newest Title', 'permalink_update_url': True})
        self.assertIn('newest-title', post.website_url)
        self.assertTrue(self.env['website.rewrite'].search([('url_from', '=', url_before)]))


@tagged('post_install', '-at_install')
class TestBlogPermalinkDialog(HttpCase):

    def test_dialog_blocks_save_until_choice(self):
        blog = self.env['blog.blog'].create({'name': 'News'})
        post = self.env['blog.post'].create({'name': 'Old Title', 'blog_id': blog.id, 'is_published': True})
        old_url = post.website_url
        self.start_tour('/odoo/action-website_blog.action_blog_post/%s' % post.id, 'website_permalink_dialog', login='admin')
        self.assertEqual(post.name, 'Renamed In Tour')
        self.assertIn('renamed-in-tour', post.website_url)
        self.assertTrue(self.env['website.rewrite'].search([('url_from', '=', old_url)]))
