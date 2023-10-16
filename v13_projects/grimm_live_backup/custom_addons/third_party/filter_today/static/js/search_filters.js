odoo.define('web.search_filters', function (require) {
"use strict";

var core = require('web.core');
var datepicker = require('web.datepicker');
var field_utils = require('web.field_utils');
var search_filters_registry = require('web.search_filters_registry');
var Widget = require('web.Widget');

var _t = core._t;
var _lt = core._lt;

var ExtendedSearchProposition = Widget.extend({
    template: 'SearchView.extended_search.proposition',
    events: {
        'change .o_searchview_extended_prop_field': 'changed',
        'change .o_searchview_extended_prop_op': 'operator_changed',
        'click .o_searchview_extended_delete_prop': function (e) {
            e.stopPropagation();
            this.trigger_up('remove_proposition');
        },
        'keyup .o_searchview_extended_prop_value': function (ev) {
            if (ev.which === $.ui.keyCode.ENTER) {
                this.trigger_up('confirm_proposition');
            }
        },
    },
    /**
     * @override
     * @param fields
     */
    init: function (parent, fields) {
        this._super(parent);
        this.fields = _(fields).chain()
            .map(function (val, key) { return _.extend({}, val, {'name': key}); })
            .filter(function (field) { return !field.deprecated && field.searchable; })
            .sortBy(function (field) {return field.string;})
            .value();
        this.attrs = {_: _, fields: this.fields, selected: null};
        this.value = null;
    },
    start: function () {
        var parent =  this._super();
        parent.then(this.proxy('changed'));
        return parent;
    },
    changed: function () {
        var nval = this.$(".o_searchview_extended_prop_field").val();
        if(this.attrs.selected === null || this.attrs.selected === undefined || nval !== this.attrs.selected.name) {
            this.select_field(_.detect(this.fields, function (x) {return x.name === nval;}));
        }
    },
    operator_changed: function (e) {
        this.value.show_inputs($(e.target));
    },
    /**
     * Selects the provided field object
     *
     * @param field a field descriptor object (as returned by fields_get, augmented by the field name)
     */
    select_field: function (field) {
        var self = this;
        if(this.attrs.selected !== null && this.attrs.selected !== undefined) {
            this.value.destroy();
            this.value = null;
            this.$('.o_searchview_extended_prop_op').html('');
        }
        this.attrs.selected = field;
        if(field === null || field === undefined) {
            return;
        }

        var type = field.type;
        var Field = search_filters_registry.getAny([type, "char"]);

        this.value = new Field(this, field);
        _.each(this.value.operators, function (operator) {
            $('<option>', {value: operator.value})
                .text(String(operator.text))
                .appendTo(self.$('.o_searchview_extended_prop_op'));
        });
        var $value_loc = this.$('.o_searchview_extended_prop_value').show().empty();
        this.value.appendTo($value_loc);

    },
    get_filter: function () {
        if (this.attrs.selected === null || this.attrs.selected === undefined) {
            return null;
        }
        var field = this.attrs.selected,
            op_select = this.$('.o_searchview_extended_prop_op')[0],
            operator = op_select.options[op_select.selectedIndex];

        return {
            attrs: {
                domain: this.value.get_domain(field, operator),
                string: this.value.get_label(field, operator),
            },
            children: [],
            tag: 'filter',
        };
    },
});

var Field = Widget.extend({
    init: function (parent, field) {
        this._super(parent);
        this.field = field;
    },
    get_label: function (field, operator) {
        var format;
        switch (operator.value) {
        case '∃': case '∄': format = _t('%(field)s %(operator)s'); break;
        default: format = _t('%(field)s %(operator)s "%(value)s"'); break;
        }
        return this.format_label(format, field, operator);
    },
    format_label: function (format, field, operator) {
        return _.str.sprintf(format, {
            field: field.string,
            // According to spec, HTMLOptionElement#label should return
            // HTMLOptionElement#text when not defined/empty, but it does
            // not in older Webkit (between Safari 5.1.5 and Chrome 17) and
            // Gecko (pre Firefox 7) browsers, so we need a manual fallback
            // for those
            operator: operator.label || operator.text,
            value: this
        });
    },
    get_domain: function (field, operator) {
        switch (operator.value) {
        case '∃': return [[field.name, '!=', false]];
        case '∄': return [[field.name, '=', false]];
        default: return [[field.name, operator.value, this.get_value()]];
        }
    },
    show_inputs: function ($operator) {
        var $value = this.$el.parent();
        switch ($operator.val()) {
            case '∃':
            case '∄':
                $value.hide();
                break;
            default:
                $value.show();
        }
    },
    /**
     * Returns a human-readable version of the value, in case the "logical"
     * and the "semantic" values of a field differ (as for selection fields,
     * for instance).
     *
     * The default implementation simply returns the value itself.
     *
     * @return {String} human-readable version of the value
     */
    toString: function () {
        return this.get_value();
    }
});

var Char = Field.extend({
    tagName: 'input',
    attributes: {
        type: 'text'
    },
    operators: [
        {value: "ilike", text: _lt("contains")},
        {value: "not ilike", text: _lt("doesn't contain")},
        {value: "=", text: _lt("is equal to")},
        {value: "!=", text: _lt("is not equal to")},
        {value: "∃", text: _lt("is set")},
        {value: "∄", text: _lt("is not set")}
    ],
    get_value: function () {
        return this.$el.val();
    }
});
var Dat = Field.extend({
    tagName: 'span',
    attributes: {
        type: 'number',
        value: 0
    },
    operators: [
        {value: "Test", text: _lt("Test")}
    ],
    show_inputs: function ($operator) {
        var $value = this.$el.parent();
        switch ($operator.val()) {
            case 'Test':
                $value.hide();
                break;
            default:
                $value.show();
        }
    }
});
//custom
var DateTime = Field.extend({
    tagName: 'span',
    attributes: {
        type: 'datetime'
    },
    operators: [
        {value: "between", text: _lt("is between")},
        {value: "=", text: _lt("is equal to")},
        {value: "!=", text: _lt("is not equal to")},
        {value: ">", text: _lt("is after")},
        {value: "<", text: _lt("is before")},
        {value: ">=", text: _lt("is after or equal to")},
        {value: "<=", text: _lt("is before or equal to")},
        {value: "∃", text: _lt("is set")},
        {value: "∄", text: _lt("is not set")},
        //custom
        {value: "Today", text: _lt("Heute")},//date = hom nay
        {value: "Less than days ago", text: _lt("Weniger als vor X Tagen")},//Loc ra ban ghi co today-x < date < today
        {value: "More than days ago", text: _lt("Mehr als vor X Tagen")},//Loc ra ban ghi co date < today-x
        {value: "Days Ago", text: _lt("Vor X Tagen")},//Loc ra ban ghi co date = today -x
        {value: "Is less than", text: _lt("In weniger als X Tagen")},//loc ra cac ban ghi co today < date < today + x
        {value: "Is more than", text: _lt("In mehr als X Tagen")},//Lọc ra các bản ghi có date > today + x
        {value: "Days Later", text: _lt("In X Tagen")}//Lọc ra các bản ghi có date = today + x
        //end custom
    ],
    /**
     * Gets the value of the datepicker
     *
     * @public
     * @param {Integer} [index] The datepicker's index.
     *  0 for the lower boundary (default)
     *  1 for the higher boundary
     *
     * @return {Moment} The value in UTC
     */
    get_value: function (index) {
        // retrieve the datepicker value
        var value = this["datewidget_" + (index || 0)].getValue().clone();
        // convert to utc
        return value.add(-this.getSession().getTZOffset(value), 'minutes');
    },
    get_domain: function (field, operator) {
        switch (operator.value) {
            case '∃':
                return [[field.name, '!=', false]];
            case '∄':
                return [[field.name, '=', false]];
            case 'between':
                return [[field.name, '>=', this.get_value()], [field.name, '<=', this.get_value(1)]];
            //custom
            case 'Today':
                var value = moment(new Date());
                var date_start = value.set({hour: 23, minute: 59, second: 59, millisecond: 59});
                this["datewidget_" + (1)].setValue(date_start);
                return [[field.name, '>=', this.get_value(0)], [field.name, '<=', this.get_value(1)]];

            case 'Less than days ago':
                var date_start = this.get_value_number("sub").set({
                    hour: 23,
                    minute: 59,
                    second: 59,
                    millisecond: 59
                });
                var temp = moment(new Date());
                var date_end = temp.set({hour: 0, minute: 0, second: 0, millisecond: 0});
                this["datewidget_" + (0)].setValue(date_start);//set value display toString
                this["datewidget_" + (1)].setValue(date_end);
                return [[field.name, '>', this.get_value(0)], [field.name, '<', this.get_value(1)]];

            case 'More than days ago' :
                var date_start = this.get_value_number("sub").set({
                    hour: 0,
                    minute: 0,
                    second: 0,
                    millisecond: 0
                });
                this['datewidget_' + (0)].setValue(date_start);//set value display toString
                return [[field.name, '<', this.get_value(0)]];

            case 'Days Ago':
                var date_start = this.get_value_number("sub").set({
                    hour: 0,
                    minute: 0,
                    second: 0,
                    millisecond: 0
                });
                var date_end = this.get_value_number("sub").set({
                    hour: 23,
                    minute: 59,
                    second: 59,
                    millisecond: 59
                });
                this['datewidget_' + (0)].setValue(date_start);
                this['datewidget_' + (1)].setValue(date_end);
                return [[field.name, '>=', this.get_value(0)], [field.name, '<=', this.get_value(1)]];

            case 'Is less than' :
                var temp = moment(new Date());
                var date_start = temp.set({hour: 23, minute: 59, second: 59, millisecond: 59});
                var date_end = this.get_value_number("add").set({
                    hour: 0,
                    minute: 0,
                    second: 0,
                    millisecond: 0
                });
                this['datewidget_' + (0)].setValue(date_start);
                this['datewidget_' + (1)].setValue(date_end);
                return [[field.name, '>', this.get_value(0)], [field.name, '<', this.get_value(1)]];

            case 'Is more than' :
                var date_start = this.get_value_number("add").set({
                    hour: 23,
                    minute: 59,
                    second: 59,
                    millisecond: 59
                });
                this['datewidget_' + (0)].setValue(date_start);
                return [[field.name, '>', this.get_value(0)]];

            case 'Days Later':
                var date_start = this.get_value_number("add").set({
                    hour: 0,
                    minute: 0,
                    second: 0,
                    millisecond: 0
                });
                var date_end = this.get_value_number("add").set({
                    hour: 23,
                    minute: 59,
                    second: 59,
                    millisecond: 59
                });
                this['datewidget_' + (0)].setValue(date_start);
                this['datewidget_' + (1)].setValue(date_end);
                return [[field.name, '>=', this.get_value(0)], [field.name, '<=', this.get_value(1)]];
            //end custom
            default:
                return [[field.name, operator.value, this.get_value()]];
        }
    },
    show_inputs: function ($operator) {
        this._super.apply(this, arguments);
        var custom_search_condition = ["Less than days ago", "More than days ago", "Days Ago", "Is less than", "Is more than","Days Later"];
        if ($operator.val() === "between") {
            this.datewidget_1.do_show();
        } else if (custom_search_condition.includes($operator.val())) {
            this._hide_datewidget();
            this._show_input_integer();
        } else {
            this.datewidget_1.do_hide();
        }
    },
    toString: function () {
        var str = field_utils.format[this.attributes.type](this.get_value(), {type: this.attributes.type});
        // the second datewidget might have been hidden because the operator has changed
        var date_1_value = this.datewidget_1 && !this.datewidget_1.$el.hasClass('o_hidden') && this.get_value(1);
        if (date_1_value) {
            str += _lt(" and ") + field_utils.format[this.attributes.type](date_1_value, {type: this.attributes.type});
        }
        if (this["value_0"].getValueNumber() >= 0) {
            str = _lt("Value = ") + this["value_0"].getValueNumber();
        }
        return str;
    },
    start: function () {
        return Promise.all([
            this._super.apply(this, arguments),
            this._create_new_widget("datewidget_0"),
            this._create_new_widget("datewidget_1"),
            this._create_new_integer_widget("value_0"),
        ]).then(() => {
            this._hide_input_integer();
            if (this.operators[0].value !== "between") {
                this.datewidget_1.do_hide();
            }
        });
    },
    _create_new_widget: function (name, ...time) {
        this[name] = new (this._get_widget_class())(this);
        return this[name].appendTo(this.$el).then((function () {
            this[name].setValue(moment(...time));
        }).bind(this));
    },
    _get_widget_class: function () {
        return datepicker.DateTimeWidget;
    },
    /**
     * Transform a Moment in a server acceptable format
     *
     * @private
     * @param {Moment} momentValue The moment to get the string for
     *
     * @return {String} Represents the value in UTC
     */
    //_formatMomentToServer: function (momentValue) {
    //    return momentValue.locale('en').format(this.serverFormat);
    //},
});

var Date = DateTime.extend({
    attributes: {
        type: 'date'
    },
    operators: [
        {value: "=", text: _lt("is equal to")},
        {value: "!=", text: _lt("is not equal to")},
        {value: ">", text: _lt("is after")},
        {value: "<", text: _lt("is before")},
        {value: ">=", text: _lt("is after or equal to")},
        {value: "<=", text: _lt("is before or equal to")},
        {value: "between", text: _lt("is between")},
        {value: "∃", text: _lt("is set")},
        {value: "∄", text: _lt("is not set")}
    ],
    /**
     * @override
     */
    get_value: function (index) {
        // retrieve the datepicker value
        // var value = this["datewidget_" + (index || 0)].getValue();
        return this["datewidget_" + (index || 0)].getValue();
    },
    //custom
    get_domain: function (field, operator) {
        switch (operator.value) {
            case '∃':
                return [[field.name, '!=', false]];
            case '∄':
                return [[field.name, '=', false]];
            case 'between':
                return [[field.name, '>=', this.get_value()], [field.name, '<=', this.get_value(1)]];
            case 'Today':
                return [[field.name, '=', this.get_value()]];
            case 'Less than days ago':
                var date_start = this.get_value_number("sub");
                var date_end = moment(new Date());
                this["datewidget_" + (0)].setValue(date_start);
                this["datewidget_" + (1)].setValue(date_end);
                return [[field.name, '>', this.get_value(0)], [field.name, '<', this.get_value(1)]];
            case 'More than days ago' :
                var date_start = this.get_value_number("sub");
                this['datewidget_' + (0)].setValue(date_start);
                return [[field.name, '<', this.get_value(0)]];
            case 'Days Ago':
                var date_start = this.get_value_number("sub");
                this['datewidget_' + (0)].setValue(date_start);
                return [[field.name, '=', this.get_value(0)]];
            case 'Is less than' :
                var date_end = this.get_value_number("add");
                var date_start = moment(new Date());
                this["datewidget_" + (0)].setValue(date_start);
                this["datewidget_" + (1)].setValue(date_end);
                return [[field.name, '>', this.get_value(0)], [field.name, '<', this.get_value(1)]];
            case 'Is more than' :
                var date_start = this.get_value_number("add");
                this['datewidget_' + (0)].setValue(date_start);
                return [[field.name, '>', this.get_value(0)]];
            case 'Days Later':
                var date_start = this.get_value_number("add");
                this['datewidget_' + (0)].setValue(date_start);
                return [[field.name, '=', this.get_value(0)]];
            default:
                return [[field.name, operator.value, this.get_value()]];
        }
    },
    //end custom
    _get_widget_class: function () {
        return datepicker.DateWidget;
    },
});

var Integer = Field.extend({
    tagName: 'input',
    className: 'o_input',
    attributes: {
        type: 'number',
        value: '0',
    },
    operators: [
        {value: "=", text: _lt("is equal to")},
        {value: "!=", text: _lt("is not equal to")},
        {value: ">", text: _lt("greater than")},
        {value: "<", text: _lt("less than")},
        {value: ">=", text: _lt("greater than or equal to")},
        {value: "<=", text: _lt("less than or equal to")},
        {value: "∃", text: _lt("is set")},
        {value: "∄", text: _lt("is not set")}
    ],
    toString: function () {
        return this.$el.val();
    },
    get_value: function () {
        try {
            var val =this.$el.val();
            return field_utils.parse.integer(val === "" ? 0 : val);
        } catch (e) {
            return "";
        }
    }
});

var Id = Integer.extend({
    operators: [{value: "=", text: _lt("is")}]
});

var Float = Field.extend({
    template: 'SearchView.extended_search.proposition.float',
    operators: [
        {value: "=", text: _lt("is equal to")},
        {value: "!=", text: _lt("is not equal to")},
        {value: ">", text: _lt("greater than")},
        {value: "<", text: _lt("less than")},
        {value: ">=", text: _lt("greater than or equal to")},
        {value: "<=", text: _lt("less than or equal to")},
        {value: "∃", text: _lt("is set")},
        {value: "∄", text: _lt("is not set")}
    ],
    init: function (parent) {
        this._super(parent);
        this.decimal_point = _t.database.parameters.decimal_point;
    },
    toString: function () {
        return this.$el.val();
    },
    get_value: function () {
        try {
            var val =this.$el.val();
            return field_utils.parse.float(val === "" ? 0.0 : val);
        } catch (e) {
            return "";
        }
    }
});

var Selection = Field.extend({
    template: 'SearchView.extended_search.proposition.selection',
    operators: [
        {value: "=", text: _lt("is")},
        {value: "!=", text: _lt("is not")},
        {value: "∃", text: _lt("is set")},
        {value: "∄", text: _lt("is not set")}
    ],
    toString: function () {
        var select = this.$el[0];
        var option = select.options[select.selectedIndex];
        return option.label || option.text;
    },
    get_value: function () {
        return this.$el.val();
    }
});

var Boolean = Field.extend({
    tagName: 'span',
    operators: [
        {value: "=", text: _lt("is true")},
        {value: "!=", text: _lt("is false")}
    ],
    get_label: function (field, operator) {
        return this.format_label(
            _t('%(field)s %(operator)s'), field, operator);
    },
    get_value: function () {
        return true;
    }
});

return {
    Boolean: Boolean,
    Char: Char,
    Date: Date,
    DateTime: DateTime,
    ExtendedSearchProposition: ExtendedSearchProposition,
    Field: Field,
    Float: Float,
    Id: Id,
    Integer: Integer,
    Selection: Selection,
};

});
