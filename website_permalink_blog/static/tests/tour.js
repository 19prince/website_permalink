import { registry } from "@web/core/registry";

// clean form: the save buttons are hidden or removed, depending on the build
const saved = ".o_form_status_indicator:not(:has(.o_form_status_indicator_buttons:not(.invisible)))";

registry.category("web_tour.tours").add("website_permalink_dialog", {
    steps: () => [
        { trigger: "div[name=name] input", run: "edit Renamed In Tour" },
        {
            // closing the tab must not save the rename unasked, even while the
            // title input is still focused and has not committed its value
            trigger: "div[name=name] input:focus",
            run() {
                // the 19+ tour runner fails on any real beforeunload event, so
                // call the patched handler on a stand-in controller over the real
                // form, whose title input has not committed its value yet
                const { FormController } = odoo.loader.modules.get("@web/views/form/form_controller");
                const controller = Object.create(FormController.prototype);
                controller.model = {
                    root: { data: { permalink_guard_field: "name", name: "Old Title" }, _values: { name: "Old Title" } },
                };
                controller.rootRef = () => document.querySelector(".o_form_view");
                const ev = new Event("beforeunload", { cancelable: true });
                controller.beforeUnload(ev);
                if (!ev.defaultPrevented) {
                    throw new Error("unload with a pending rename was not blocked");
                }
            },
        },
        { trigger: ".o_form_button_save", run: "click" },
        { trigger: ".alert-info:contains(Website Permalink kept)" },
        { trigger: ".modal:contains(Website Permalink kept this page's URL)" },
        { trigger: ".modal button:contains(Cancel)", run: "click" },
        { trigger: "body:not(:has(.modal))" },
        { trigger: ".o_form_button_save", run: "click" },
        { trigger: ".modal #permalink_redirect:disabled" },
        { trigger: ".modal #permalink_change", run: "click" },
        { trigger: ".modal #permalink_redirect:not(:disabled):checked" },
        { trigger: ".modal button:contains(Save)", run: "click" },
        { trigger: saved },
        // an ordinary save after a rename, keeping the URL (the default)
        { trigger: "div[name=name] input", run: "edit Renamed Again" },
        { trigger: ".o_form_button_save", run: "click" },
        { trigger: ".modal #permalink_keep:checked" },
        { trigger: ".modal button:contains(Save)", run: "click" },
        { trigger: "body:not(:has(.modal))" },
        { trigger: saved },
    ],
});
