import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("website_permalink_dialog", {
    steps: () => [
        { trigger: "div[name=name] input", run: "edit Renamed In Tour" },
        { trigger: ".o_form_button_save", run: "click" },
        { trigger: ".modal:contains(Website Permalink kept this page's URL)" },
        { trigger: ".modal button:contains(Cancel)", run: "click" },
        { trigger: "body:not(:has(.modal))" },
        { trigger: ".o_form_button_save", run: "click" },
        { trigger: ".modal #permalink_redirect:disabled" },
        { trigger: ".modal #permalink_change", run: "click" },
        { trigger: ".modal #permalink_redirect:not(:disabled):checked" },
        { trigger: ".modal button:contains(Save)", run: "click" },
        { trigger: ".o_form_saved" },
    ],
});
