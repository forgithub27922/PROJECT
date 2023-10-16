odoo.define('grimm_product_stock_ext.backend', function (require) {
    "use strict";
    var ListRenderer = require('web.ListRenderer');
    var config = require('web.config');

    ListRenderer.include({
        _renderHeaderCell: function (node) {
            const { icon, name, string } = node.attrs;
            var order = this.state.orderedBy;
            var isNodeSorted = order[0] && order[0].name === name;
            var field = this.state.fields[name];
            var $th = $('<th>');
            if (name) {
                $th.attr('data-name', name);
            } else if (string) {
                $th.attr('data-string', string);
            } else if (icon) {
                $th.attr('data-icon', icon);
            }
            if (node.attrs.editOnly) {
                $th.addClass('oe_edit_only');
            }
            if (node.attrs.readOnly) {
                $th.addClass('oe_read_only');
            }
            if (!field) {
                return $th;
            }
            var description = string || field.string;
            if (node.attrs.widget) {
                $th.addClass(' o_' + node.attrs.widget + '_cell');
                if (this.state.fieldsInfo.list[name].Widget.prototype.noLabel) {
                    description = '';
                }
            }
            $th.text(description)
                .attr('tabindex', -1)
                .toggleClass('o-sort-down', isNodeSorted ? !order[0].asc : false)
                .toggleClass('o-sort-up', isNodeSorted ? order[0].asc : false)
                .addClass(field.sortable && 'o_column_sortable');

            if (isNodeSorted) {
                $th.attr('aria-sort', order[0].asc ? 'ascending' : 'descending');
            }

            if (field.type === 'float' || field.type === 'integer' || field.type === 'monetary') {
                $th.addClass('o_list_number_th');
            }

            if (config.isDebug()) {
                var fieldDescr = {
                    field: field,
                    name: name,
                    string: description || name,
                    record: this.state,
                    attrs: _.extend({}, node.attrs, this.state.fieldsInfo.list[name]),
                };
                this._addFieldTooltip(fieldDescr, $th);
            } else {
                var fieldDescr = {
                    field: field,
                    name: name,
                    string: description || name,
                    attrs: _.extend({}, node.attrs, this.state.fieldsInfo.list[name]),
                };
                this._addFieldTooltip(fieldDescr, $th);
            }
            return $th;
        },
    });
});
