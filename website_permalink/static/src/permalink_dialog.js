import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";
import { Component, useState } from "@odoo/owl";

export class PermalinkDialog extends Component {
    static template = "website_permalink.PermalinkDialog";
    static components = { Dialog };
    static props = { close: Function, url: String, resolve: Function };

    setup() {
        this.title = _t("Website Permalink");
        this.state = useState({ choice: "keep", redirect: true });
    }

    save() {
        this.props.resolve({ updateUrl: this.state.choice === "change", redirect: this.state.redirect });
        this.props.close();
    }
}
