# -*- coding: utf-8 -*-
{
    'name': "sms core",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Syncology",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['mail',
                'report_xlsx',
                'website',
                'website_slides',
                'intl_tel_widget',
                'base_address_city',
                'account',
                ],

    # always loaded
    'data': [
        'wizard/admission_list_wizard.xml',
        'wizard/register_student_in_school_class.xml',
        'wizard/reject_admission_reason.xml',
        'wizard/student_reports_wizard.xml',
        'wizard/warning_email_fee_overdue.xml',
        'wizard/pay_student_fee_wizard.xml',
        'wizard/fee_collection_dues_report_wizard.xml',
        'wizard/sync_lms_wizard.xml',
        'wizard/post_fee_installment_wizard.xml',
        'wizard/activate_deactivate_lms_wizard.xml',
        'wizard/delete_student_views.xml',
        'wizard/fees_installments_wizard_view.xml',
        'security/sms_core_security.xml',
        'security/ir.model.access.csv',
        'report/report_admission_list.xml',
        'report/std_admission_biodata_report.xml',
        'report/students_information_report.xml',
        'report/parents_guardian_info_report.xml',
        'report/report_fee_collection_dues.xml',
        'report/reports_declarator.xml',
        'views/sms_core_masterdata_views.xml',
        'views/sms_core_views.xml',
        'wizard/update_accounts_journal_wizard.xml',
        'views/sms_fee_view.xml',
        # 'views/templates.xml',
        'views/sms_core_menu.xml',
        'views/admission_website_form.xml',
        'views/res_config_settings_view.xml',
        'views/res_city.xml',
        'data/schedulers.xml',
        'static/src/xml/link_file_change_menu_color.xml',
        'templates/login_layout.xml',
        'data/website_data.xml',
        'data/student_fee_sequence.xml',
        'data/documents_stage_mail_template.xml',
        'data/deactivation_lms_mail_template.xml',
        'data/register_student_in_school_mail_template.xml',
        'data/reject_admission_reason_mail.xml',
        'data/pending_for_payment_mail_template.xml',
        'data/due_payment_mail_template.xml',
        'report/report_student_fee_template.xml',
        'report/student_fee_reports.xml',
        'views/asset.xml',
        'data/student_interview_mail_template.xml',
        'data/student_cancel_mail_template.xml',
        'views/academic_student_installment_view.xml',
    ],

    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
