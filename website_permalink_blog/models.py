from odoo import models


class Blog(models.Model):
    _inherit = 'blog.blog'

    def _permalink_url(self):
        # blogs have no website_url before Odoo 20; this is the blog index route
        self.ensure_one()
        return self.id and '/blog/%s' % self.env['ir.http']._slug(self)

    def _permalink_dependents(self):
        # every post URL starts with its blog's slug
        posts = self.env['blog.post'].search([('blog_id', 'in', self.ids)])
        return super()._permalink_dependents() + [posts]


class BlogPost(models.Model):
    _name = 'blog.post'
    _inherit = ['blog.post', 'website.permalink.published.mixin']
