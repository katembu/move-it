
/* setup environment */
$(document).ready( function() {
    // setup variables
    SMSes = {};
    current = 0;
    gen_table(current);

    // set identity from cookie if exists
    var identity = readCookie('dataentry_identity');
    if (identity && identity.length > 0)
        $('#phone').val(decodeURIComponent(identity));

    // give message box the focus
    focus_entry();

    // setup form action
    $('#form').submit( function() { try { send_message(); } catch(e) {} return false; });

    // start message query loop
    setInterval("get_message()", 5000);
});

/* sends the current message to the proxy for processing */
function send_message()
{
    var identity = $('#phone').val();
    var text =  $('#message').val();

    if (identity.length == 0) {
        alert("You must set your Identity to be able to send messages.\nPlease fill the Identity box and retry.");
        return false;
    }

    if (text.length == 0) {
        alert("You can't send empty messages!\nPlease write something and retry.");
        return false;   
    }

    // store identity in a cookie
    createCookie('dataentry_identity', encodeURIComponent(identity));

    data = {'identity': identity, 'message': text};
    res = proxy_send(data, on_proxy_send);
}

/* send_message callback: copy message text to history and create a new row in Sent table */
function on_proxy_send(data)
{
    if (data) {
        // store msg in row
        SMSes[current] = {'message': $('#message').val()}

        // create new row
        current = parseInt(current) + 1;
        gen_table(current);

        // scroll to new row
        $('#ccform_body').scrollTo('#sms_' + current, 1);

        // empty entry input
		$('#message').val("");

        // return focus to text box
        focus_entry();
    }
}

/* calls the proxy for new message */
function get_message()
{
    var identity = $('#phone').val();

    if (identity.length == 0) {
        return false;
    }
    data = proxy_get(identity, on_proxy_get);
}

/* get_message callback: copy message info into the Inbox table */
function on_proxy_get(data)
{
    if (data && data.text) {
        var status = data.status || 'unknown';
        var text = data.text || "";

	    snippet = '<tr class="out"><td class="status"><img src="/static/childcount/icons/' + status.toLowerCase() + '.png" /></td><td class="msg">' + text + '</td></tr>';
        doc = document.getElementById('log');
	    doc.innerHTML = snippet += doc.innerHTML;

	    $('div.tester').scrollTo('#log tr:last', 800);
    }
}

/* generates a new empty row in Sent Messages */
function gen_table(id)
{
    var snippet = '<tr id="sms_' + id + '">';
    snippet += '<td id="td_' + id + '" class="f" title="message"></td>';
    snippet += '<td id="duplicate_' + id + '" title="Duplicate SMS"><img class="duplicate" src="/static/childcount/icons/copy.png" onclick="duplicate_sms(' + id + ');" /></td></tr>';
    $('#ccform_body').append(snippet);
}

/* replicates message box content into the Sent Message table row */
function parse_message()
{
    var doc = document.getElementById('td_'+current);
    var text = $('#message').val();
    doc.innerHTML = text;
}

/* copy a previously entered message from the Sent table to message box */
function duplicate_sms(id)
{
    $('#message').val(SMSes[id].message);
    parse_message();
    focus_entry();
}

/* gives message box the focus */
function focus_entry()
{
    $('#message').focus();
}

/* generic function to record a cookie */
function createCookie(name,value,days) {
	if (days) {
		var date = new Date();
		date.setTime(date.getTime()+(days*24*60*60*1000));
		var expires = "; expires="+date.toGMTString();
	}
	else var expires = "";
	document.cookie = name+"="+value+expires+"; path=/";
}

/* generic function to read a cookie */
function readCookie(name) {
	var nameEQ = name + "=";
	var ca = document.cookie.split(';');
	for(var i=0;i < ca.length;i++) {
		var c = ca[i];
		while (c.charAt(0)==' ') c = c.substring(1,c.length);
		if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
	}
	return null;
}

/* generic function to delete a cookie */
function eraseCookie(name) {
	createCookie(name,"",-1);
}

UTF8 = {
	encode: function(s){
		for(var c, i = -1, l = (s = s.split("")).length, o = String.fromCharCode; ++i < l;
			s[i] = (c = s[i].charCodeAt(0)) >= 127 ? o(0xc0 | (c >>> 6)) + o(0x80 | (c & 0x3f)) : s[i]
		);
		return s.join("");
	},
	decode: function(s){
		for(var a, b, i = -1, l = (s = s.split("")).length, o = String.fromCharCode, c = "charCodeAt"; ++i < l;
			((a = s[i][c](0)) & 0x80) &&
			(s[i] = (a & 0xfc) == 0xc0 && ((b = s[i + 1][c](0)) & 0xc0) == 0x80 ?
			o(((a & 0x03) << 6) + (b & 0x3f)) : o(128), s[++i] = "")
		);
		return s.join("");
	}
};

