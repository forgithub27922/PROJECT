odoo.define('report_partner_filter.account_report', function (require) {
'use strict';

var accountReportsWidget = require('account_reports.account_report');
accountReportsWidget.include({
	render_searchview_buttons: function() {
		var self = this;
		this._super.apply(this, arguments);
        // Partners filter
        this.$searchview_buttons.find('.js_partner_reports_auto_complete').select2();
        if (self.report_options.partner) {
            self.$searchview_buttons.find('[data-filter="partners"]').select2("val", self.report_options.partners);
        }
        this.$searchview_buttons.find('.js_partner_reports_auto_complete').on('change', function(){
            self.report_options.partners = self.$searchview_buttons.find('[data-filter="partners"]').val();
            return self.reload().then(function(){
                self.$searchview_buttons.find('.partner_filter').click();
            })
        });
	},
})

});
