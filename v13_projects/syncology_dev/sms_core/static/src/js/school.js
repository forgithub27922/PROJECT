odoo.define('sms_core.school_grade', function (require) {'use strict';
var publicWidget = require('web.public.widget');

publicWidget.registry.CarSell = publicWidget.Widget.extend({
    selector: '#admission_form',
    events: {
            "change select[name='application_for_id']": "_onBrandChange",
            },

    start: function(){
        var def = this._super.apply(this, arguments);
        this.application_for_id= this.$('select[name="application_for_id"]');
        this.$class_grade = this.$('select[name="class_grade"]');
        return def;
    },

    _onBrandChange: function () {
         var self = this;
         var application_for_id = this.application_for_id.val();
         this._rpc({
                    route: '/filter/model',
                    params: {
                                application_for_id: application_for_id,
                            },
                }).then(function (result) {
                                    self.$class_grade.empty();
                                    $.each(result, function (key, value) {
                                    self.$class_grade.append('<option value=' + value['grade_id'] + '>' + value['grade_name'] + '</option>');
        });

        });

    },
});


publicWidget.registry.ChildAdmissionForm = publicWidget.Widget.extend({
    selector: '#child_admission_form',
    events: {
            "change select[name='application_for_id']": "_onSchoolChange",
            },

    start: function(){
        var def = this._super.apply(this, arguments);
        this.application_for_id= this.$('select[name="application_for_id"]');
        this.$class_grade = this.$('select[name="child_class_grade"]');
        return def;
    },

    _onSchoolChange: function () {
         var self = this;
         var application_for_id = this.application_for_id.val();
         this._rpc({
                    route: '/filter/grade',
                    params: {
                                application_for_id: application_for_id,
                            },
                }).then(function (result) {
                                    self.$class_grade.empty();
                                    $.each(result, function (key, value) {
                                    self.$class_grade.append('<option value=' + value['grade_id'] + '>' + value['grade_name'] + '</option>');
        });

        });

    },
});



});

















