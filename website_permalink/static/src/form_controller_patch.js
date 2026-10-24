import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { PermalinkDialog } from "./permalink_dialog";

// Every in-app save path (Save button, autosave on leaving, Go to Website,
// pager) goes through onWillSaveRecord, so asking here means a rename never
// slips through unseen. No-op on forms without the permalink fields; the
// server only flags a rename on pages that have ever been published.
patch(FormController.prototype, {
    async onWillSaveRecord(record, changes) {
        const proceed = await super.onWillSaveRecord(...arguments);
        if (proceed === false || record !== this.model.root || !record.data.permalink_name_changed) {
            return proceed;
        }
        const choice = await new Promise((resolve) => {
            this.dialogService.add(
                PermalinkDialog,
                { url: record.data.permalink_url || "", resolve },
                { onClose: () => resolve(null) }
            );
        });
        if (!choice) {
            return false; // Cancel: stay on the form, nothing saved
        }
        changes.permalink_update_url = choice.updateUrl;
        changes.permalink_redirect = choice.redirect;
        return proceed;
    },

    beforeUnload(ev) {
        // Closing or reloading the tab saves by sendBeacon, which skips
        // onWillSaveRecord, and a dialog cannot be shown during unload. Ask the
        // browser to confirm leaving instead of saving the rename unasked;
        // staying lets the next save show the dialog.
        if (this._permalinkPendingRename()) {
            ev.preventDefault();
            ev.returnValue = "Unsaved changes";
            return;
        }
        return super.beforeUnload(...arguments);
    },

    _permalinkPendingRename() {
        const root = this.model.root;
        const fieldName = root?.data.permalink_guard_field;
        if (!fieldName) {
            return false;
        }
        // a still-focused input has not committed its value to the record yet
        const input = this.rootRef.el?.querySelector(
            `.o_field_widget[name="${fieldName}"] :is(input, textarea)`
        );
        const current = input ? input.value : root.data[fieldName];
        return (current || "") !== (root._values[fieldName] || "");
    },
});
