function post_report(eventObj) {
    var pk = eventObj.target.id.substring(6);
    $("input#variant").val(pk);
    $("form#gen_form").submit();
}

function post_init() {
    $("a.indicator_chart img").click(post_report);
}

$(document).ready(post_init);
