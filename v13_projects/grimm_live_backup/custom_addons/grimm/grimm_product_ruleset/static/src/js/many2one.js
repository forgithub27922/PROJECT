odoo.define('grimm_product_ruleset.confirmation', function (require) {
"use strict";

var core = require('web.core');
var rel_fields = require('web.relational_fields');
var _t = core._t;

rel_fields.FieldMany2One.include({
    _onFieldChanged: function (event) {
        var fieldName = event.target.name;
        if (fieldName == 'property_set_id' && event.data.changes.property_set_id.display_name != undefined) {
            var new_value = event.data.changes.property_set_id.display_name.toLowerCase();
//            var record = this.model.get(this.handle);
//            console.log(record)
//            this._rpc({
//                model: 'stock.picking',
//                method: 'disp_model_for_existing_location',
//                args: [[record.data.id], barcode],
//            }).done(function (result) {
//
//            }
            var old_db_value = event.target.m2o_value.toLowerCase();
            var old_value = event.target.$input[0].value.toLowerCase();
            console.log(event);
            console.log(new_value + '==' + old_value + '===' + old_db_value);
            console.log(event.target.lastSetValue);
            var key_entered = new_value.includes(old_value);
    //        console.log(old_value + ' ' + fieldName + 'property_set_id');
            if (new_value != old_db_value) {
                if (old_db_value != "" || old_value != "") {
                    var decision = confirm(_.str.sprintf(_t("Are you sure you want to change the value of Property Set to %s? Note: After changing the value of the Property Set, please press Save in order to save the changes."), event.data.changes.property_set_id.display_name));

                    if (decision == false) {
                        event.stopPropagation();
                    }
                }
            }
//            else if (fieldName == 'ruleset_id') {
//                console.log(event.data.changes.ruleset_id);
//            }
        }

        this.lastChangeEvent = event;
    },
});
});