// javascript for the httpclient
url = "/dataentry/proxy/";

$(document).ready(function(){
	$('#form').submit(function(){ sendMsg(); return false; });
	setInterval("checkMsgs()", 5000);
});

function sendMsg() {
    parse_message();
    var phone = $('#phone').val();
    var message = $('#message').val();
	if (phone.length > 0 && message.length > 0) {
		req = url + $('#phone').val() + "/" + escape($('#message').val());
		$.getJSON(
			req,
			function (response) { if (response) {

                // store msg in row
                SMSes[dataentry_form.name][current] = {'message': $('#message').val()}

                // create new row
                current = parseInt(current) + 1;
                gen_table(current);

                // scroll to new row
                $('#ccform_body').scrollTo('#sms_'+current, 1)

                // empty entry input
				$('#message').val("");
			}}
		);
	} else {
        return;
    }
}

function decode(str) {
	str = str.replace(/%23/gi, "#");
	str = str.replace(/%24/gi, "$");
	str = str.replace(/%26/gi, "&");
	str = str.replace(/%3D/gi, "=");
	str = str.replace(/%3B/gi, ";");
	str = str.replace(/%2C/gi, ",");
	str = str.replace(/%3A/gi, ":");
	str = str.replace(/%3F/gi, "?");
	str = decodeURI(str);
	return str;
}

function checkMsgs() {
	if ($('#phone').val().length > 0) {
		req = url + $('#phone').val() + "/json_resp";
		$.getJSON(
			req,
			function (response) { if (response) {
                clog(response);
                var status = response.status;
                clog(status);
				snippet = '<tr class="out"><td class="status"><img src="/static/dataentry/icons/' + status.toLowerCase() + '.png" /></td><td class="msg">' + decode(response.message) + '</td></tr>';
                doc = document.getElementById('log');
				doc.innerHTML = snippet += doc.innerHTML;

				$('div.tester').scrollTo('#log tr:last', 800);
			}}

		);
	}
}
