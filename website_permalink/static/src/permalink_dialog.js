import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";
import { Component, proxy, t, useProps } from "@odoo/owl";

export class PermalinkDialog extends Component {
    static template = "website_permalink.PermalinkDialog";
    static components = { Dialog };
    props = useProps({ close: t.function(), url: t.string(), resolve: t.function() });

    setup() {
        this.title = _t("Website Permalink");
        this.state = proxy({ choice: "keep", redirect: true });
    }

    save() {
        this.props.resolve({ updateUrl: this.state.choice === "change", redirect: this.state.redirect });
        this.props.close();
    }
}
