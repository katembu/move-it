
/* HTTP Client */

url = '/dataentry/proxy/';

$(document).ready( function() {
    $('#form').submit( function(){ send_message(); return false; });
    setInterval("get_message()", 5000);
});

function send_message()
{
    var identity = $('#phone').val();
    var message =  $('#message').val();

    if (identity.length < 3) {
        alert("Your name is not set! Fill it in yellow box."); return false;
    }

    if (message.length == 0) {
        alert("Can't send empty message.");   
    }

    $.getJSON(url + identity + "/" + message, function (data) { 

            if (data) {

                // store msg in row
                SMSes[dataentry_form.name][current] = {'message': $('#message').val()}

                // create new row
                current = parseInt(current) + 1;
                gen_table(current);

                // scroll to new row
                $('#ccform_body').scrollTo('#sms_' + current, 1);

                // empty entry input
				$('#message').val("");
			}
    }, "json");

}

function get_message()
{
    var identity = $('#phone').val();

    if (identity.length < 3) {
        return false;
    }
    
    $.getJSON(url + identity + "/json_resp", function (data) { 

            if (data && data.message) {

                var status = data.status || 'unknown';
                var message = data.message || "";

				snippet = '<tr class="out"><td class="status"><img src="/static/dataentry/icons/' + status.toLowerCase() + '.png" /></td><td class="msg">' + message + '</td></tr>';
                doc = document.getElementById('log');
				doc.innerHTML = snippet += doc.innerHTML;

				$('div.tester').scrollTo('#log tr:last', 800);
			}
    }, "json");
}
