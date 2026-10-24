from odoo import api, fields, models


class WebsiteSeoMetadata(models.AbstractModel):
    _inherit = 'website.seo.metadata'

    # form-only helpers: never stored, consumed by write()
    permalink_url = fields.Char('Permalink URL', compute='_compute_permalink_url')
    permalink_name_changed = fields.Boolean(compute='_compute_permalink_changed')
    permalink_slug_changed = fields.Boolean(compute='_compute_permalink_changed')
    # name of the field the browser watches on unload, False when renames are free
    permalink_guard_field = fields.Char(compute='_compute_permalink_guard_field')
    permalink_update_url = fields.Boolean(
        'Change URL to match the new name', compute='_compute_permalink_options', readonly=False,
        help='Renaming a page that has been published keeps its URL by default. Pass True in the '
             'same write as the new name to move the URL to match it instead. AI agents and API '
             'clients: ask the user before setting this, since moving a URL affects links and '
             'search rankings.')
    permalink_redirect = fields.Boolean(
        'Redirect old URL (301)', compute='_compute_permalink_options', readonly=False,
        help='When a URL moves (permalink_update_url, or a seo_name edit), a 301 redirect from '
             'the old URL is added unless this is False. AI agents and API clients: ask the user '
             'before passing False.')

    def _permalink_url(self):
        """Public URL this record is served at, or False when it has none.

        Bridges override this for models without website_url (categories, blogs).
        """
        self.ensure_one()
        return 'website_url' in self._fields and self.website_url

    def _permalink_live(self):
        """Whether this record's URL has ever been public and so is worth keeping.

        Models without a publish flag (categories) are always live. Checked here
        rather than overridden in website.permalink.published.mixin: models list
        the SEO mixin first, so an override there would never be reached.
        """
        self.ensure_one()
        if 'permalink_was_published' in self._fields:
            return self.is_published or self.permalink_was_published
        # models without a bridge (events, ...): live only while published
        return self.is_published if 'is_published' in self._fields else True

    def _permalink_trigger_fields(self):
        """Fields whose change can move this record's URL or a dependent's."""
        return {dep.split('.')[0] for dep in self.pool.field_depends[self._fields['display_name']]}

    def _permalink_dependents(self):
        """Other records whose URL embeds this record's name (category children,
        a blog's posts), as a list of recordsets. Their URLs are kept too."""
        return []

    def _permalink_langs(self):
        # en_US first: the first write into an empty translated column copies
        # its value into en_US, so en_US has to be settled before the others
        installed = [code for code, _name in self.env['res.lang'].get_installed()]
        return ['en_US'] + [code for code in installed if code != 'en_US']

    def _permalink_slug_text(self):
        """The text part of this record's URL slug, exactly as ir.http._slug
        builds it (seo_name, or the name as each version's overrides see it)."""
        self.ensure_one()
        slug = self.env['ir.http']._slug(self)
        suffix = '-%s' % self.id
        return slug[:-len(suffix)] if slug.endswith(suffix) else ''

    def _permalink_new_slug_text(self):
        """Slug text the current name would give with no seo_name set."""
        self.ensure_one()
        # the context website_sale's _slug override uses from Odoo 20 on (no
        # parent category names); the keys are ignored where nothing reads them
        name = self.with_context(show_attribute=False, show_parent_categories=False).display_name
        return self.env['ir.http']._slugify(name or '')

    def _permalink_state(self, groups, langs):
        """{(model, id): {lang: (url, slug text)}} for every record in groups."""
        state = {}
        for lang in langs:
            # website_url and parent display names are cached without the
            # language, so each language reads from a clean cache
            self.env.invalidate_all()
            for records in groups:
                for rec in records.with_context(lang=lang):
                    state.setdefault((rec._name, rec.id), {})[lang] = (
                        rec._permalink_url(), rec._permalink_slug_text())
        self.env.invalidate_all()
        return state

    def _permalink_pin(self, targets):
        """Write seo_name per language without re-entering the rename logic."""
        self.ensure_one()
        for lang, slug in targets.items():  # targets follow _permalink_langs order
            rec = self.with_context(lang=lang, permalink_internal=True)
            if slug and rec.seo_name != slug:
                rec.write({'seo_name': slug})

    def _compute_permalink_url(self):
        for rec in self:
            # the saved URL, so the form shows what visitors use until save
            rec.permalink_url = rec._origin.id and rec._origin._permalink_url()

    def _compute_permalink_guard_field(self):
        for rec in self:
            origin = rec._origin
            live = origin.id and origin._permalink_live() and origin._permalink_url()
            rec.permalink_guard_field = live and rec._rec_name or False

    @api.depends(lambda self: (self._rec_name, 'seo_name') if self._rec_name else ('seo_name',))
    def _compute_permalink_changed(self):
        for rec in self:
            origin = rec._origin
            rec.permalink_name_changed = bool(
                origin.id and rec._rec_name and rec[rec._rec_name] != origin[rec._rec_name]
                and origin._permalink_live())
            rec.permalink_slug_changed = bool(origin.id and rec.seo_name != origin.seo_name)

    @api.depends()
    def _compute_permalink_options(self):
        self.permalink_update_url = False
        self.permalink_redirect = True

    def write(self, vals):
        """Keep a published record's URL when its name changes.

        Core already builds the slug from seo_name when it is set
        (website/models/ir_http.py `_slug`), so pinning the old slug there is
        the whole permalink: no _slug override, and every model with SEO
        metadata is covered.

        seo_name is translated, so every installed language is pinned
        separately: a rename or a URL change in one language never moves the
        URL in another. Records whose URL embeds this one's name (see
        _permalink_dependents) are pinned the same way.

        Without the form flags (import, API, server actions) the URL is always
        kept, so a bulk rename can never move URLs. When a URL does move, a 301
        from the old one is added unless permalink_redirect is False.
        """
        if self.env.context.get('permalink_internal'):
            return super().write(vals)
        update_url = vals.pop('permalink_update_url', False)
        redirect = vals.pop('permalink_redirect', True)
        for helper in ('permalink_url', 'permalink_name_changed', 'permalink_slug_changed',
                       'permalink_guard_field'):
            vals.pop(helper, None)

        renaming = bool(self._permalink_trigger_fields() & vals.keys())
        slug_edit = 'seo_name' in vals
        if not (renaming or slug_edit):
            return super().write(vals)

        # never-published drafts are skipped: nobody has linked to them yet
        own = self.filtered(lambda r: r.id and r._permalink_live() and r._permalink_url())
        groups = [own, *[deps.filtered(lambda r: r._permalink_live() and r._permalink_url())
                         for deps in own._permalink_dependents()]]
        if not any(groups):
            return super().write(vals)

        langs = self._permalink_langs()
        edit_lang = self.env.lang or 'en_US'
        before = self._permalink_state(groups, langs)
        res = super().write(vals)

        for records in groups:
            is_own = records is own
            for rec in records:
                old = before[(rec._name, rec.id)]
                targets = {}
                for lang in langs:
                    if is_own and lang == edit_lang:
                        if slug_edit:
                            continue  # the slug the user typed stands
                        if update_url:
                            # pinned to the new name rather than cleared: clearing
                            # a translated field wipes every language at once
                            targets[lang] = rec.with_context(lang=lang)._permalink_new_slug_text()
                            continue
                    targets[lang] = old[lang][1]
                rec._permalink_pin(targets)

        if redirect:
            after = self._permalink_state(groups, langs)
            rewrites = {}
            for records in groups:
                for rec in records:
                    website = 'website_id' in rec._fields and rec.website_id.id or False
                    for lang, (old_url, _slug) in before[(rec._name, rec.id)].items():
                        new_url = after[(rec._name, rec.id)][lang][0]
                        if old_url and new_url and old_url != new_url:
                            rewrites[(old_url, website)] = {
                                'name': 'Permalink: %s' % rec.display_name,
                                'url_from': old_url,
                                'url_to': new_url,
                                'redirect_type': '301',
                                'website_id': website,
                            }
            if rewrites:
                self.env['website.rewrite']._permalink_record(list(rewrites.values()))
        return res
