odoo.define('sky_website_hr_recruitment_custom.custom-form', function(require) {
    'use strict';

    var core = require('web.core');
    var _t = core._t;
    var ajax = require('web.ajax');
    var coll = document.getElementsByClassName("collapsible");

    $(document).ready(function() {

        for (i = 0; i < coll.length; i++) {
            coll[i].addEventListener("click", function() {
                this.classList.toggle("active");
                var content = this.nextElementSibling;
                if (content.style.display === "block") {
                    content.style.display = "none";
                } else {
                    content.style.display = "block";
                }
            });
        }

        var attachment_data_updated_resume
        $("input[name='attachment_resume']").change(function() {
            var self = this
            var allowedExtensions = /(\.pdf)$/i;
            /*--------Allow only PDF to upload-----------------*/
            if (!allowedExtensions.exec($(self).val())) {
                $(self).val('')
                $(self).parent('.file-input').find('.span_label').text('Choose File')
                alert(_t('Invalid file type'))
                return false;
            } else {
                var name= $("input[name='attachment_resume']").val()
                var name_list = name.split('\\')
                var file_name= name_list[name_list.length -1 ]
                $("input[name='hidden_file_name']").val(file_name)
                $("input[name='hidden_file_name']").removeAttr('style');
                $("input[name='hidden_file_name']").css('border','none');
                var attachment_input = $(self)[0]
                var attachment_data = false
                if (attachment_input.files && attachment_input.files[0]) {
                    var reader = new FileReader();
                    reader.addEventListener("load", function() {
                        attachment_data = reader.result
                        attachment_data_updated_resume = attachment_data
                        attachment_data_updated_resume = attachment_data_updated_resume.replace(/^data:application\/[a-z]+;base64,/, "");
                        $(self).next("input[name='attachment_newresume']").val(attachment_data_updated_resume)
                    }, false);
                    reader.readAsDataURL(attachment_input.files[0]);
                }
            }
        })
        /*------------Form Submission--------------------*/
        $("#custom_form_submit").click(function() {
            var national_id_rec = $("#hr_recruitment_form input[name='national_id']").val()
            var passport_id_rec = $("#hr_recruitment_form input[name='passport_id']").val()

            if (!national_id_rec && !passport_id_rec){
                alert("Please Fill Either National ID or Passport No")
            }
            $(".required_fields").each(function() {
                var self = this
                if ($(this).val() == '') {
                    $(self).addClass('sit_error')
                } else {
                    $(self).removeClass('sit_error')
                }
            })
            if ($('.sit_error').length) {
                return false;
            }
            /*----------------Variables---------------*/
            var training_details = [];
            var experience_details = [];
            var education_details = [];

             /* ---------------Education Qualification Data------------------*/
            $("#hr_recruitment_form .main_education_details").each(function() {
                var name = $(this).find("input[name='name']").val();
                var institute = $(this).find("input[name='institute']").val();
                var start_date = $(this).find("input[name='start_date']").val();
                var end_date = $(this).find("input[name='end_date']").val();
                var final_grade = $(this).find("select[name='final_grade']").val();

                var edu_dict = {
                    'name': name,
                    'institute': institute,
                    'start_date': start_date,
                    'end_date': end_date,
                    'final_grade': final_grade
                }

                education_details.push(edu_dict)
            });
            /* ---------------Training Data------------------*/
            $("#hr_recruitment_form .main_training_details").each(function() {
                var trianing_name = $(this).find("input[name='training']").val();
                var institute_name = $(this).find("input[name='institute_name']").val();
                var start_date = $(this).find("input[name='start_date']").val();
                var end_date = $(this).find("input[name='end_date']").val();

                var tra_dict = {
                    'name': trianing_name,
                    'institute_name': institute_name,
                    'start_date': start_date,
                    'end_date': end_date,
                }

                training_details.push(tra_dict)
            });
            /* ---------------Experience Data------------------*/
            $("#hr_recruitment_form .main_exp_details").each(function() {
                var employer_name = $(this).find("input[name='employer_name']").val();
                var job_id = $(this).find("select[name='job_id']").val();
                var experience_start_date = $(this).find("input[name='experience_start_date']").val();
                var experience_end_date = $(this).find("input[name='experience_end_date']").val();

                var data = {
                    'employer_name': employer_name,
                    'job_id': job_id,
                    'experience_start_date': experience_start_date,
                    'experience_end_date': experience_end_date,
                }
                experience_details.push(data)
            });
            var with_children = false;
            if ($("#hr_recruitment_form input[name='with_children']").is(":checked")){
                with_children = true;
            }


            /*-------------Ajax Request for form Submission-----------------*/
            ajax.jsonRpc("/website_form_recruitment", 'call', {
                'first_name_arabic': $("#hr_recruitment_form input[name='first_name_arabic']").val(),
                'middle_name_arabic': $("#hr_recruitment_form input[name='middle_name_arabic']").val(),
                'last_name_arabic': $("#hr_recruitment_form input[name='last_name_arabic']").val(),
                'fourth_name_arabic': $("#hr_recruitment_form input[name='fourth_name_arabic']").val(),
                'first_name': $("#hr_recruitment_form input[name='first_name']").val(),
                'middle_name': $("#hr_recruitment_form input[name='middle_name']").val(),
                'last_name': $("#hr_recruitment_form input[name='last_name']").val(),
                'fourth_name': $("#hr_recruitment_form input[name='fourth_name']").val(),
                'english_name': $("#hr_recruitment_form input[name='english_name']").val(),
                'address': $("#hr_recruitment_form input[name='address']").val(),
                'city_id': $("#hr_recruitment_form select[name='city_id']").val(),
                'partner_phone': $("#hr_recruitment_form input[name='partner_phone']").val(),
                'email_from': $("#hr_recruitment_form input[name='email_from']").val(),
                'religion': $("#hr_recruitment_form input[name='religion']").val(),
                'gender': $("#hr_recruitment_form select[name='gender']").val(),
                'job_id': $("#hr_recruitment_form input[name='hidden_job_id']").val(),
                'department_id': $("#hr_recruitment_form input[name='hidden_department_id']").val(),
                'date_of_birth': $("#hr_recruitment_form input[name='date_of_birth']").val(),
                'place_of_birth': $("#hr_recruitment_form select[name='place_of_birth']").val(),
                'nationality': $("#hr_recruitment_form select[name='nationality']").val(),
                'marital_status': $("#hr_recruitment_form select[name='marital_status']").val(),
                'military_status': $("#hr_recruitment_form select[name='military_status']").val(),
                'national_id': $("#hr_recruitment_form input[name='national_id']").val(),
                'passport_id': $("#hr_recruitment_form input[name='passport_id']").val(),
                'general_service_status': $("#hr_recruitment_form select[name='general_service_status']").val(),
                'partner_full_name': $("#hr_recruitment_form input[name='partner_full_name']").val(),
                'partner_national_id': $("#hr_recruitment_form input[name='partner_national_id']").val(),
                'partner_qualification': $("#hr_recruitment_form input[name='partner_qualification']").val(),
                'partner_birthdate': $("#hr_recruitment_form input[name='partner_birthdate']").val(),
                'partner_place_of_birth': $("#hr_recruitment_form select[name='partner_place_of_birth']").val(),
                'partner_employment': $("#hr_recruitment_form input[name='partner_employment']").val(),
                'partner_employment_location': $("#hr_recruitment_form input[name='partner_employment_location']").val(),
                'with_children': with_children,
                'upload_cv': $("#hr_recruitment_form input[name='attachment_newresume']").val(),
                'fname': $("#hr_recruitment_form input[name='attachment_resume']").val().replace(/C:\\fakepath\\/i, ''),
                'education_data' : education_details,
                'training_data': training_details,
                'experience_data': experience_details,
            }).then(function(data) {
                window.location.replace('/job-thank-you');
            })
        })

        // On "other" add the char field
        function onchangesel(self) {
            $(self).change(function() {
                if ($(self).val() == -1) {
                    if (!$(self).next("input.custom_added_class").length || $(self).next("input.custom_added_class").length == 0) {
                        $('<input style="margin-top:10px;" type="text" name="' + $(self).attr("for") + '" class="effect-2 custom_added_class form-control o_website_form_input" placeholder="' + $(self).attr("data") + '" />').insertAfter($(self))
                        var input_val = $(self).next("input.custom_added_class").val()
                    }
                } else {
                    $(self).next("input.custom_added_class").remove()
                }
            })
        }
        $('select').each(function() {
            var self = this
            onchangesel(self)
        })

        // File Input Style
        var inputs = document.querySelectorAll('.file-input')
        for (var i = 0, len = inputs.length; i < len; i++) {
            customInput(inputs[i])
        }

        function customInput(el) {
            const fileInput = el.querySelector('[type="file"]')
            const label = el.querySelector('[data-js-label]')

            fileInput.onchange =
                fileInput.onmouseout = function() {
                    if (!fileInput.value) return
                    var value = fileInput.value.replace(/^.*[\\\/]/, '')
                    el.className += ' -chosen'
                    // label.innerText = value
                }
        }

        // Ajax request for adding new Fields
        $(".add_details").click(function() {
            var detail_type = $(this).find("#details").val()
            ajax.jsonRpc("/add_details", 'call', {
                'detail_type': detail_type,
            }).then(function(data) {
                if (detail_type == 'tra') {
                    $("#tra_details").append(data)
                    $(document).on("click", '#remove_detail', function(event) {
                        $(this).parents('.main_training_details').remove()
                    });
                }
                if (detail_type == 'exp') {
                    $("#exp_details").append(data)
                    $(document).on("click", '#remove_detail', function(event) {
                        $(this).parents('.main_exp_details').remove()
                    });
                }
                if (detail_type == 'edu') {
                    $("#edu_details").append(data)
                    $(document).on("click", '#remove_detail', function(event) {
                        $(this).parents('.main_education_details').remove()
                    });
                }
            })
        })

        function visible_family(){
            var marital_status = $("select[name='marital_status']").val()
            if (marital_status != 'married'){
                $("#family_information").hide();
                $("#hr_recruitment_form input[name='partner_full_name']").removeClass('required_fields')
                $("#hr_recruitment_form input[name='partner_national_id']").removeClass('required_fields')
                $("#hr_recruitment_form input[name='partner_qualification']").removeClass('required_fields')
                $("#hr_recruitment_form input[name='partner_birthdate']").removeClass('required_fields')
                $("#hr_recruitment_form select[name='partner_place_of_birth']").removeClass('required_fields')
                $("#hr_recruitment_form input[name='partner_employment']").removeClass('required_fields')
                $("#hr_recruitment_form input[name='partner_employment_location']").removeClass('required_fields')
                $("#hr_recruitment_form input[name='with_children']").removeClass('required_fields')

                $("#hr_recruitment_form input[name='partner_full_name']").removeAttr('required')
                $("#hr_recruitment_form input[name='partner_national_id']").removeAttr('required')
                $("#hr_recruitment_form input[name='partner_qualification']").removeAttr('required')
                $("#hr_recruitment_form input[name='partner_birthdate']").removeAttr('required')
                $("#hr_recruitment_form select[name='partner_place_of_birth']").removeAttr('required')
                $("#hr_recruitment_form input[name='partner_employment']").removeAttr('required')
                $("#hr_recruitment_form input[name='partner_employment_location']").removeAttr('required')
                $("#hr_recruitment_form input[name='with_children']").removeAttr('required')

            }
            else{
                $("#family_information").show();
                $(self).addClass('sit_error')
                $("#hr_recruitment_form input[name='partner_full_name']").addClass('required_fields')
                $("#hr_recruitment_form input[name='partner_national_id']").addClass('required_fields')
                $("#hr_recruitment_form input[name='partner_qualification']").addClass('required_fields')
                $("#hr_recruitment_form input[name='partner_birthdate']").addClass('required_fields')
                $("#hr_recruitment_form select[name='partner_place_of_birth']").addClass('required_fields')
                $("#hr_recruitment_form input[name='partner_employment']").addClass('required_fields')
                $("#hr_recruitment_form input[name='partner_employment_location']").addClass('required_fields')
                $("#hr_recruitment_form input[name='with_children']").addClass('required_fields')

                $("#hr_recruitment_form input[name='partner_full_name']").attr("required", "true");
                $("#hr_recruitment_form input[name='partner_national_id']").attr("required", "true");
                $("#hr_recruitment_form input[name='partner_qualification']").attr("required", "true");
                $("#hr_recruitment_form input[name='partner_birthdate']").attr("required", "true");
                $("#hr_recruitment_form select[name='partner_place_of_birth']").attr("required", "true");
                $("#hr_recruitment_form input[name='partner_employment']").attr("required", "true");
                $("#hr_recruitment_form input[name='partner_employment_location']").attr("required", "true");
                $("#hr_recruitment_form input[name='with_children']").attr("required", "true");
            }
        }

        visible_family();
        $("select[name='marital_status']").on('change', function() {
            visible_family()
        })
    })
});