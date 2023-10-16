UPDATE ir_cron
SET active = 'f';
UPDATE fetchmail_server
SET state = 'draft';
UPDATE magento_backend
SET location = '';
UPDATE ir_model_data
SET module = 'queue_job'
WHERE name = 'channel_root';
DELETE
FROM ir_ui_view
WHERE arch_db LIKE '%sale_condition%';
DELETE
FROM ir_ui_view
WHERE arch_db LIKE '%@name=''attribute_set_id%';
-- UPDATE ir_mail_server
-- SET name = 'office11@grimm-gastrobedarf.de', smtp_user = 'office11@grimm-gastrobedarf.de', smtp_pass = 'Hoh56454'
-- WHERE id = 2;
UPDATE ir_module_module
SET name = 'grimm_product'
WHERE name = 'of_product_attribute_extensions';
UPDATE ir_module_module_dependency
SET name = 'grimm_product'
WHERE name = 'of_product_attribute_extensions';
UPDATE ir_model_data
SET module = 'grimm_product'
WHERE module = 'of_product_attribute_extensions';
UPDATE ir_model_data
SET name = 'module_grimm_product'
WHERE name = 'module_of_product_attribute_extensions' AND module = 'base' AND model = 'ir.module.module';
UPDATE ir_translation
SET module = 'grimm_product'
WHERE module = 'of_product_attribute_extensions';
UPDATE stock_move_line
SET product_qty = product_uom_qty
WHERE product_qty IS NULL;
UPDATE ir_module_module
SET state= 'to remove'
WHERE name IN ('web_widget_text_markdown', 'web_sheet_full_width', 'mail_base', 'mail_archive', 'grimm_maintenance',
               'grimm_magentoerpconnect_v2', 'grimm_search_category_tree ');
UPDATE ir_module_module
SET state= 'to remove'
WHERE name LIKE 'muk%';
