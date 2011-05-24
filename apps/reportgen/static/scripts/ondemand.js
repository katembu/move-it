var elms = [
    "#report",
    "#variant",
    "#rformat",
    "#period_type",
    "#period"
];

function count(eobj) {
    var c = 0;
    for(e in eobj) {
        if(eobj[e] == "") continue;
        if(e == "") continue;
        c++;
    }       
    return c;
}

function check_finished(eventObj) {
    var okay = true;
    for(e in elms) {
        if($(elms[e]).val() == "") {
            okay = false;
            break;
        }
    }

    if(okay) {
        $("#submit").removeAttr('disabled');
    } else {
        $("#submit").attr('disabled', 'true');
    }
}

function set_report() {
    r = $("#report");
    if(r.val()) {
        // Enable the report format select box
        $("#rformat").removeAttr('disabled');
        $("#rformat").empty();

        // Populate new options
        $("#rformat").append("<option value=''>[File Type]</option>");
        
        var s = sorted_keys(data['formats'][r.val()]);
        for(i in s) {
            var j = s[i];
            $("#rformat").append("<option value="+j+">" + 
                data['formats'][r.val()][j]+"</option>");
        }
        
        // Enable the report variant select box
        $("#variant").removeAttr('disabled');
        $("#variant").empty();
       
        if(count(data['variants'][r.val()]) == 0) {
            $("#variant").append("<option value='X'>--</option>");
        } else {
            // Populate new options
            $("#variant").append("<option value=''>[Variant]</option>");
            var s = sorted_keys(data['variants'][r.val()]);
            for(i in s) {
                var j = s[i];
                $("#variant").append("<option value="+j+">" + 
                    data['variants'][r.val()][j]+"</option>");
            }
        }
    } else {
        $("#variant").attr('disabled','true');
        $("#variant").empty();
        $("#variant").append("<option value=''>[Variant]</option>");

        $("#rformat").attr('disabled','true');
        $("#rformat").empty();
        $("#rformat").append("<option value=''>[File Type]</option>");
    }
}

function set_dates() {
    pt = $("#period_type").val();
    if(pt) {
        $("#period").removeAttr('disabled');
        $("#period").empty();
        
        $("#period").append("<option value=''>[Dates]</option>");
            for(i in data['time_periods'][pt]) {
                $("#period").append("<option value="+i+">" + 
                    data['time_periods'][pt][i]+"</option>");
            }
    } else {
        $("#period").attr('disabled', 'true');
        $("#period").empty();
        $("#period").append("<option value=''>[Dates]</option>");
    }
}

function progress_process_data(data, textStatus, jqXHR) {
    rows = data[0];
    errors = data[1];
    progresses = data[2];

    values = {}
    for(pk in rows) {
        /* If the progress bar is active */
        if(progresses[pk] != undefined && $("#progress_"+pk+" .progress-value")) {
            $("#progress_"+pk+" .progress-value").animate(
                { width: progresses[pk]+"%" }, 
                { duration: 1000, 
                }
                );
        }
        //alert(pk);
    }

    setTimeout(function() {
        for(pk in rows) {
            $("#row_"+pk).html(rows[pk]);
        }
    }, 1000);

    for(pk in errors) {
        if(!$("#error_"+pk)) {
            $("#row_"+pk).after(errors[pk]);
        }
    }
    refresh_listeners();
}

function progress_update() {
    return $.ajax({
        url: '/reportgen/ajax_progress/',
        data: {},
        success: progress_process_data
    });
}

function refresh_listeners() {
    $("a.err_link").click(toggle_text);
    $("a.delete").click(process_delete);
}

function init() {
    var s = sorted_keys(data['rpts']);
    for(i in s) {
        var j = s[i];
        $("#report").append("<option value="+j+">" + 
            data['rpts'][j]+"</option>");
    }

    var s = sorted_keys(data['time_types']);
    for(i in s) {
        var j = s[i];
        $("#period_type").append("<option value="+j+">" + 
            data['time_types'][j]+"</option>");
    }
    for(e in elms) {
        $(elms[e]).change(check_finished);
    }
    $("#report").change(set_report);
    $("#period_type").change(set_dates);
    refresh_listeners();

    setInterval(progress_update, 5000);
}

function process_delete(eventObj) {
    var pk = eventObj.target.id.substring(7);
    return confirm("Are you sure you want to " + 
                    "permanently delete this report?");
}

function sorted_keys(lst) {
    var keys = [];
    for(k in lst) {
        keys.push(k);
    }

    keys.sort(function(a,b) {
        return lst[a] > lst[b] ? 1 : -1;
    });
    return keys
}

function toggle_text(evt) { 
    $("#error_"+evt.target.id.substring(5)).slideToggle(500);
}


$(document).ready(init);

