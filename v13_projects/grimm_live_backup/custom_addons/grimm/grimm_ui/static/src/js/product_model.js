odoo.define('grimm_ui.product_model', function (require) {
    "use strict";

    var FormRenderer = require('web.FormRenderer');

    FormRenderer.include({
        _renderTagSeparator: function (node) {
            var $sep = this._super(node);
            if($sep.text() == "" && this.state.model == "product.template") {
                $sep.removeClass('o_horizontal_separator');
            }

            return $sep;
        },
    });
});