odoo.define('grimm_dashboard.display_stats', function (require) {
    var core = require('web.core');
    var _t = core._t;
    var config = require('web.config');
    var HomeMenu = require('web_enterprise.HomeMenu');
    var QWeb = core.qweb;
    var Session = require('web.session');

    HomeMenu.include({
        start: function () {
            return this._super.apply(this, arguments).then(this.display_stats.bind(this));
        },
        display_stats: function() {
            var self = this;

            // don't show the stats for portal users
            if (!(Session.warning))  {
                return;
            }
            this.getSession().user_has_group('grimm_dashboard.cost_data').then(function(has_group) {
                if (has_group) {
                    Session.rpc('/display_stats', {}).then(function(res) {
                        if(res){
                            var $statsTemp = $(QWeb.render("DisplayStats", {'is_mobile': (config.device.size_class < config.device.SIZES.XXL ? 'true': 'false'), 'service': res.service, 'sales': res.sales, 'shop': res.shop, 'project': res.project,
                            'cls_service': res.cls_service, 'cls_sales': res.cls_sales, 'cls_shop': res.cls_shop, 'cls_project': res.cls_project}));
                            $($statsTemp).insertAfter(self.$mainContent);
                            $statsTemp.toast('show');
        //                    $statsTemp.$el.find('#disp_stats').fadeOut('fast');
                        }
                    });
                }
            });
        },
    });
});