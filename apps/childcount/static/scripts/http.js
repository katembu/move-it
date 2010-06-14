
$(document).ready( function() {
    $('#form').submit( function(){ send_message(); return false; });
    setInterval("get_message()", 5000);
});

function send_message()
{
    var identity = $('#phone').val();
    var text =  $('#message').val();
    var chw = $('#chw').val();
    var encounter_date = $('#date').val() || null;

    if (identity.length < 3) {
        alert("Your name is not set! Fill it in yellow box."); return false;
    }

    if (text.length == 0) {
        alert("Can't send empty message.");   
    }

    data = {'identity': identity, 'message': text, 'chw': chw, 'encounter_date': encounter_date};

    res = proxy_send(data, on_proxy_send);
}

function on_proxy_send(data)
{
    if (data) {
        clog(data); 
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
}

function get_message()
{
    var identity = $('#phone').val();

    if (identity.length < 3) {
        return false;
    }

    data = proxy_get(identity, on_proxy_get);
}

function on_proxy_get(data)
{
    if (data && data.text) {

        clog(data);
        var status = data.status || 'unknown';
        var text = data.text || "";

	    snippet = '<tr class="out"><td class="status"><img src="/static/childcount/icons/' + status.toLowerCase() + '.png" /></td><td class="msg">' + text + '</td></tr>';
        doc = document.getElementById('log');
	    doc.innerHTML = snippet += doc.innerHTML;

	    $('div.tester').scrollTo('#log tr:last', 800);
    
    }
}
