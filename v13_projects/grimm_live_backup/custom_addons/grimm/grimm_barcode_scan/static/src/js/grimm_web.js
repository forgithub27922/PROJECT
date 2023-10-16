odoo.define('grimm_barcode_scan.Photo_MainMenu', function (require) {
"use strict";

var core = require('web.core');
var AbstractAction = require('web.AbstractAction');
var Session = require('web.session');

var _t = core._t;
var QWeb = core.qweb;
var FormController = require('web.FormController');

FormController.include({
    _barcodePickingAddRecordId: function (barcode, activeBarcode) {
        if (!activeBarcode.handle) {
            return $.Deferred().reject();
        }
        var record = this.model.get(activeBarcode.handle);
        if (record.data.state === 'cancel' || record.data.state === 'done') {
            var self = this;
            Session.rpc('/stock_barcode/scan_from_transfer_main_menu', {
                barcode: barcode,
            }).then(function(result) {
                if (result.notify) {
                    self.do_notify(_t("Success"), result.notify);
                } else if (result.action){
                    self.do_action(result.action)
                }else {
                    self.do_warn(result.warning);
                }

            });
            return new $.Deferred().reject();
            //this.do_warn(_.str.sprintf(_t("Picking %s"), record.data.state),
            //    _.str.sprintf(_t("The picking is %s and cannot be edited."), record.data.state));
            //return $.Deferred().reject();
        }
        return this._barcodeAddX2MQuantity(barcode, activeBarcode);
    }
});


var Photo_MainMenu = AbstractAction.extend({
    template: 'photo_main_menu',

    events: {
        "click .button_photo_operations": function(){
            this.do_action('product.product_template_action');
        },
    },

    init: function(parent, action) {
        // Yet, "_super" must be present in a function for the class mechanism to replace it with the actual parent method.
        this._super.apply(this, arguments);
    },

    start: function() {
        var self = this;
        core.bus.on('barcode_scanned', this, this._onBarcodeScanned);
        return this._super();
    },

    destroy: function () {
        core.bus.off('barcode_scanned', this, this._onBarcodeScanned);
        this._super();
    },

    _onBarcodeScanned: function(barcode) {
        var self = this;
        if (!$.contains(document, this.el)) {
            return;
        }
        Session.rpc('/stock_barcode/scan_from_photo_main_menu', {
            barcode: barcode,
        }).then(function(result) {
            if (result.notify) {
                self.do_notify(_t("Success"), result.notify);
            } else if (result.action){
                self.do_action(result.action)
            }else {
                self.do_warn(result.warning);
            }

        });
    },
});

core.action_registry.add('photo_barcode_main_menu', Photo_MainMenu);

var Int_Transfer_MainMenu = AbstractAction.extend({
    template: 'internal_transfer_main_menu',

    events: {
        "click .button_open_operations": function(){
            this.do_action('stock_barcode.stock_picking_type_action_kanban');
        },
    },

    init: function(parent, action) {
        // Yet, "_super" must be present in a function for the class mechanism to replace it with the actual parent method.
        this._super.apply(this, arguments);
    },

    start: function() {
        var self = this;
        core.bus.on('barcode_scanned', this, this._onBarcodeScanned);
        return this._super();
    },

    destroy: function () {
        core.bus.off('barcode_scanned', this, this._onBarcodeScanned);
        this._super();
    },

    _onBarcodeScanned: function(barcode) {
        this.notification_manager = new NotificationManager(this);
        var self = this;
        if (!$.contains(document, this.el)) {
            return;
        }
        Session.rpc('/stock_barcode/scan_from_transfer_main_menu', {
            barcode: barcode,
        }).then(function(result) {
            if (result.notify) {
                self.do_notify(_t("Success"), result.notify);
            } else if (result.action){
                self.do_action(result.action)
            }else {
                self.do_warn(result.warning);
            }
        });
    },
});

core.action_registry.add('internal_transfer_main_menu', Int_Transfer_MainMenu);

return {
    Photo_MainMenu: Photo_MainMenu,
    Int_Transfer_MainMenu: Int_Transfer_MainMenu,
};

});
