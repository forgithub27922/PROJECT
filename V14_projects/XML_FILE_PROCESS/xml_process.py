from bs4 import BeautifulSoup

with open('FILE.xml', 'r') as f:
    data = f.read()
Bs_data = BeautifulSoup(data, "xml")
print(Bs_data.prettify())
print("\n\n::::> BS DATA STRING", Bs_data.Caption.string)
# print(Bs_data.title)
# b_unique = Bs_data.find_all('Caption')
# print(b_unique)
# # b_layer = Bs_data.find_all('Marquardt')
# # print(b_layer)
# # b_image = Bs_data.find_all('Image')
# # print(b_image)
# b_name =
#
# value = b_unique.get('', {''})
# print(b_unique)
#


from lxml import etree

root = etree.parse(r'/home/parth/workspace/V14_projects/XML_FILE_PROCESS/FILE.xml')
# Print the loaded XML
print(etree.tostring(root))
