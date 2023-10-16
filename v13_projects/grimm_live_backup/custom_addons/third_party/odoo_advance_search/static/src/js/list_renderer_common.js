odoo.define('odoo_advance_search.ListrendererCommon', function (require) {
"use strict";

var ListRenderer = require('web.ListRenderer');

ListRenderer.include({
    _onKeyPress: function (event) {
        if (event.keyCode === $.ui.keyCode.ENTER) {
            this._add();
        }
    },
});

});
