odoo.define('grimm_product_mask.image_pos', function (require) {
    "use strict";

    var AbstractField = require('web.AbstractField');
    var FieldBinaryImage = require('web.basic_fields').FieldBinaryImage;
    var FieldChar = require('web.basic_fields').FieldChar;
    var core = require('web.core');
    var qweb = core.qweb;
    var _t = core._t;

    FieldBinaryImage.include({
        _render: function () {
            this._super();
            var self = this;
            if (this.name == "image_1920" && (this.model == "product.template" || this.model == "product.product")) {
                self.$el.addClass("grimm_prod_img");
                var $img = self.$el.children('img');
            }
        },
    });

    FieldChar.include({
        _render: function () {
            this._super.apply(this, arguments);
            var self = this;
            if (this.field.name == "name" && (this.model == "product.template" || this.model == "product.product")) {
                var status = this.recordData.active ? _t("Active") : _t("Inactive");
                var badge_cls = this.recordData.active ? 'text-success grimm_badge_success': 'text-danger grimm_badge_danger';
                self.$el.append('&nbsp;<span class="badge ' + badge_cls + '">' + status + '</span>');
            }
        }
    });
});