import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-server-ux",
    description="Meta package for oca-server-ux Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-announcement',
        'odoo13-addon-barcode_action',
        'odoo13-addon-base_action_visibility_restriction',
        'odoo13-addon-base_binary_url_import',
        'odoo13-addon-base_custom_filter',
        'odoo13-addon-base_duplicate_security_group',
        'odoo13-addon-base_export_manager',
        'odoo13-addon-base_field_deprecated',
        'odoo13-addon-base_import_security_group',
        'odoo13-addon-base_ir_actions_sequence',
        'odoo13-addon-base_menu_visibility_restriction',
        'odoo13-addon-base_optional_quick_create',
        'odoo13-addon-base_rule_visibility_restriction',
        'odoo13-addon-base_search_custom_field_filter',
        'odoo13-addon-base_substate',
        'odoo13-addon-base_technical_features',
        'odoo13-addon-base_tier_validation',
        'odoo13-addon-base_tier_validation_formula',
        'odoo13-addon-base_tier_validation_forward',
        'odoo13-addon-base_user_locale',
        'odoo13-addon-chained_swapper',
        'odoo13-addon-date_range',
        'odoo13-addon-default_multi_user',
        'odoo13-addon-document_quick_access',
        'odoo13-addon-document_quick_access_folder_auto_classification',
        'odoo13-addon-filter_multi_user',
        'odoo13-addon-mass_editing',
        'odoo13-addon-mass_operation_abstract',
        'odoo13-addon-multi_step_wizard',
        'odoo13-addon-sequence_check_digit',
        'odoo13-addon-sequence_reset_period',
        'odoo13-addon-test_base_binary_url_import',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 13.0',
    ]
)
