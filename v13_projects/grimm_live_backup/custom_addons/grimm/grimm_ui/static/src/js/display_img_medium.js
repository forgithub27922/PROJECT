$(document).ajaxComplete(function(){
    var arr = window.location.href.toString().split("&");
    var is_product = false;
    for (i=1; i <= arr.length - 1; i++) {
        if(arr[i].split("=")[1] == "product.template") {
            is_product = true;
        }
    }
    if(is_product == true) {
        $('div.oe_avatar').removeClass('o_field_empty');
    }
});