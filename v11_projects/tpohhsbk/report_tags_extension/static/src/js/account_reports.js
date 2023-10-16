odoo.define('report_tags_extension.account_report', function (require) {
'use strict';
var accountReportsWidget = require('account_reports.account_report');
accountReportsWidget.include({
	render_searchview_buttons: function() {
		var self = this;
		this._super.apply(this, arguments);
		this.$searchview_buttons.find('.js_account_reports_acc_tags_auto_complete').select2();
    	self.$searchview_buttons.find('[data-filter="acc_tags"]').select2("val", self.report_options.acc_tags);
        this.$searchview_buttons.find('.js_account_reports_acc_tags_auto_complete').on('change', function(){
            self.report_options.acc_tags = self.$searchview_buttons.find('[data-filter="acc_tags"]').val();
            return self.reload().then(function(){
                self.$searchview_buttons.find('.account_tags_filter').click();
            })
        });
	},
})
});
