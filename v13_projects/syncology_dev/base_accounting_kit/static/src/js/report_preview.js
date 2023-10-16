odoo.define("base_accounting_kit.ReportPreview", function(require) {
    "use strict";

    var ActionManager = require("web.ActionManager");
    var core = require("web.core");
    var _t = core._t;

    // Action Manager
    ActionManager.include({
        // --------------------------------------------------------------------------
        // Private
        // --------------------------------------------------------------------------

        /**
         * Downloads a PDF report for the given url. It blocks the UI during the
         * report generation and download.
         *
         * @param {String} url
         * @returns {Deferred} resolved when the report has been downloaded ;
         *   rejected if something went wrong during the report generation
         */
        _downloadReport: function(url) {
            if (!window.open(url)) {
                // AAB: this check should be done in get_file service directly,
                // should not be the concern of the caller (and that way, get_file
                // could return a deferred)
                var message = _t(
                    "A popup window with your report was blocked. You " +
                        "may need to change your browser settings to allow " +
                        "popup windows for this page."
                );
                this.do_warn(_t("Warning"), message, true);
            }
            return Promise.resolve();
        },
    });
});
