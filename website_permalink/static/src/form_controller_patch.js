import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { PermalinkDialog } from "./permalink_dialog";

// Every save path (Save button, autosave on leaving, Go to Website, pager)
// goes through onWillSaveRecord, so asking here means a rename never slips
// through unseen. No-op on forms without the permalink fields; the server
// only flags a rename on pages that have ever been published.
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
});
