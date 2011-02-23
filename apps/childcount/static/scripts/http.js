
$(document).ready(function() {
    $('#form').submit( function(){ send_message(); return false; });
    $('#message').keyup(  parse_date );
    setInterval("get_message()", 5000);
});

function parse_date()
{
    var text = $('#message').val();
    var raw_date = text.split(/\s+/, 1)[0].trim();

    var d = Date.parse(raw_date);
    if (d == null) {
        $('#date_value').text('Cannot read date'); 
        $('#date_value').addClass('date_bad'); 
        $('#date_value').removeClass('date_okay'); 
        $('#edate').val('');
    } else {
        $('#date_value').text(d.toString('dd-MMM-yyyy'));
        $('#date_value').addClass('date_okay'); 
        $('#date_value').removeClass('date_bad'); 
        $('#edate').val(d.toString("yyyy-MM-dd"));
    }
}

function send_message()
{
    var identity = $('#phone').val();
    var chw = $('#chw').val();
    var encounter_date = $('#edate').val();
    var text = $('#message').val();
    var raw_date = text.split(/\s+/, 1)[0];
    text = text.slice(raw_date.length).trim();

    if (identity.length < 3) {
        alert("Your name is not set! Fill it in yellow box."); return false;
    }

    if (text.length == 0) {
        alert("Can't send empty message."); return false;
    }

    data = {'identity': identity, 'message': text, 'chw': chw, 'encounter_date': encounter_date};

    confstr = "Please confirm:\n\t";
    confstr += "Encounter Date: " + encounter_date + "\n\t";
    confstr += "CHW: " + $('#chw option:selected').text() + "\n";

    if (confirm(confstr)) {
        res = proxy_send(data, on_proxy_send);
    }
    else return false;
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
