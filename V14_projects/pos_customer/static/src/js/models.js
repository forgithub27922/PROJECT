odoo.define('pos_customer.pos_customer', function(require) {
    "use strict";

    var models = require('point_of_sale.models');
    var PosModelSuper = models.PosModel;

    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            var self = this;
            _.each(self.models, function (model) {
                if (model.model === "res.partner") {
                    model.domain = function(self) {return [['is_customer', '=', true]];};
                }
            });
            return PosModelSuper.prototype.initialize.call(this, session, attributes);
        },
    });

    var posmodel_super = models.PosModel.prototype;

    models.PosModel = models.PosModel.extend({
        prepare_new_partners_domain: function(){
            const cust_domain = posmodel_super.prepare_new_partners_domain.apply(this);
            cust_domain.push(['is_customer', '=', true]);
            return cust_domain;
        }

    });
  
});