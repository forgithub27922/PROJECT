odoo.define('grimm_modifications.field_char', function (require) {
    "use strict";

    var basic_fields = require('web.basic_fields');
    var FieldChar = basic_fields.FieldChar;

    FieldChar.include({
        _renderEdit: function () {
            this._super.apply(this, arguments);
            var self = this;
            if (this.model == 'res.partner' && this.field.name == 'city') {
                $(document).ajaxComplete(function(){
                    if (!('params' in self.record.getContext()) || self.record.getContext().active_model == 'res.partner') {
                          self.$el.addClass('grimm_city_field_dialog');
                    } else {
                        if (self.record.viewType == 'form') {
                            self.$el.addClass('grimm_city_field');
                        } else {
                            self.$el.addClass('grimm_city_field_dialog');
                        }
                    }
                });
            }
        },
    });
});