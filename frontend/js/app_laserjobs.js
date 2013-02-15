
function send_gcode_to_backend(gcode) {
  if (typeof gcode === "string" && gcode != '') {
    // $().uxmessage('notice', gcode.replace(/\n/g, '<br>'));
  	$.post("/gcode", { 'gcode_program':gcode }, function(data) {
  		if (data != "") {
  			$().uxmessage('success', "G-Code sent to AXIS.");	
  		} else {
  			$().uxmessage('error', "An error occured while saving /tmp/gcode.ngc.");
  		}
    });  
  } else {
    $().uxmessage('error', "No G-Code. Import a SVG first.");
  }
}


var zoom_scale = 4;
$(document).ready(function(){

  // populate queue from queue directory
  $.getJSON("/queue/list", function(data) {
    $.each(data, function(index, name) {
      add_to_job_queue(name);
    });
  });
    
  // populate library from library directory
  $.getJSON("/library/list", function(data) {
    $.each(data, function(index, name) {
      $('#gcode_library').prepend('<li><a href="#">'+ name +'</a></li>');
    });
  	$('#gcode_library li a').click(function(){
  	  var name = $(this).text();
      $.get("/library/get/" + name, function(gdata) {
        load_into_gcode_widget(gdata, name);
      });
  	});  	
  });
  // .success(function() { alert("second success"); })
  // .error(function() { alert("error"); })
  // .complete(function() { alert("complete"); });
 
  


  $("#progressbar").hide();  
  $("#gcode_submit").click(function(e) {
  	// send gcode string to server via POST
  	var gcode = $('#gcode_program').val();
    send_gcode_to_backend(gcode);
  	return false;
  });


  $('#gcode_bbox_submit').tooltip();
  $("#gcode_bbox_submit").click(function(e) {
    var gcodedata = $('#gcode_program').val();
    GcodeReader.parse(gcodedata, 1);
    var gcode_bbox = GcodeReader.getBboxGcode();
    var header = "%\nG21\nG90\nG0F16000\n"
    var footer = "G00X0Y0F16000\n%"
    // save_and_add_to_job_queue($('#gcode_name').val() + 'BBOX', header + gcode_bbox + footer);  // for debugging
    send_gcode_to_backend(header + gcode_bbox + footer);
    return false;
  });

  $('#gcode_save_to_queue').tooltip();
  $("#gcode_save_to_queue").click(function(e) {
    save_and_add_to_job_queue($.trim($('#gcode_name').val()), $('#gcode_program').val());
    return false;
  });


  // G-Code Canvas Preview
  //
  var canvas = new Canvas('#preview_canvas');
  canvas.background('#ffffff');

  $('#preview_zoom_out').click(function(e) {
    if(zoom_scale <= 1) return false;
    redrawCanvas(--zoom_scale);
    return false;
  });
  $('#preview_zoom_in').click(function(e) {
    redrawCanvas(++zoom_scale);
    return false;
  });

});  // ready

function redrawCanvas(scale) {
	if(!scale) scale = 4;
	scale = scale * 0.25
	var canvas = new Canvas('#preview_canvas');
	canvas.background('#ffffff');
	var gcodedata = $('#gcode_program').val();
	canvas.background('#ffffff'); 
	GcodeReader.parse(gcodedata, scale);
  	GcodeReader.draw(canvas, '#000000');
}
