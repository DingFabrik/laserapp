
var gcode_coordinate_offset = undefined;

function reset_offset() {
  $("#offset_area").hide();
  $('#offset_area').css({'opacity':0.0, left:0, top:0});
  gcode_coordinate_offset = undefined;
	$("#cutting_area").css('border', '1px dashed #ff0000');
	$("#offset_area").css('border', '1px dashed #aaaaaa');
  send_gcode('G54\n', "Offset reset.", "Serial not connected.");
  $('#coordinates_info').text('');
}

  
$(document).ready(function(){

  var isDragging = false;
  
  function assemble_and_send_gcode(x,y) {
    	var g0_or_g1 = 'G0'
    	if($('#feed_btn').hasClass("active")){
    		g0_or_g1 = 'G1';
    	}
    	var feedrate = mapConstrainFeedrate($("#feedrate_field" ).val());
    	var intensity =  mapConstrainIntesity($( "#intensity_field" ).val());
    	var gcode = 'S'+ intensity + '\n' + g0_or_g1 + ' X' + 2*x + 'Y' + 2*y + 'F' + feedrate + '\nS0\n';	
      // $().uxmessage('notice', gcode);
    	send_gcode(gcode, "Motion request sent.", "Serial not connected.");    
  }
  
  function assemble_info_text(x,y) {
    var coords_text;
  	var move_or_cut = 'move';
  	if($('#feed_btn').hasClass("active")){
  		move_or_cut = 'cut';
  	}
  	var feedrate = mapConstrainFeedrate($( "#feedrate_field" ).val());
  	var intensity =  mapConstrainIntesity($( "#intensity_field" ).val());
  	var coords_text;
  	if (move_or_cut == 'cut') {
  	  coords_text = move_or_cut + ' to (' + 2*x + ', '+ 2*y + ') at ' + feedrate + 'mm/min and ' + Math.round(intensity/2.55) + '% intensity';
  	} else {
  	  coords_text = move_or_cut + ' to (' + 2*x + ', '+ 2*y + ') at ' + feedrate + 'mm/min'
  	}
  	return coords_text;
  }
  
  
  $("#cutting_area").mousedown(function() {
    isDragging = true;
  }).mouseup(function() {
    isDragging = false;
  });
  

  $("#cutting_area").click(function(e) {
  	var offset = $(this).offset();
  	var x = (e.pageX - offset.left);
  	var y = (e.pageY - offset.top);

    if(e.shiftKey) {
      //// set offset
      $("#offset_area").show();
      $("#offset_area").animate({
        opacity: 1.0,
        left: x,
        top: y,
        width: 609-x,
        height: 304-y
      }, 200 );
      gcode_coordinate_offset = [x,y];
      var gcode = 'G10 L2 P1 X'+ 2*x + ' Y' + 2*y + '\nG55\n';
      send_gcode(gcode, "Offset set.", "Serial not connected.");
  		$(this).css('border', '1px dashed #aaaaaa');
  		$("#offset_area").css('border', '1px dashed #ff0000');
    } else if (!gcode_coordinate_offset) {	
      assemble_and_send_gcode(x,y);
    } else {
      var pos = $("#offset_area").position()
      if ((x < pos.left) || (y < pos.top)) {       
        //// reset offset
        reset_offset();
      }
    }
    return false;
  });


  $("#cutting_area").hover(
    function () {
      if (!gcode_coordinate_offset) {
    		$(this).css('border', '1px dashed #ff0000');
    	}
    	$(this).css('cursor', 'crosshair');
    },
    function () {
  		$(this).css('border', '1px dashed #aaaaaa');
  		$(this).css('cursor', 'pointer');	
  		$('#coordinates_info').text('');		
    }
  );
  
  $("#cutting_area").mousemove(function (e) {
  	var offset = $(this).offset();
  	var x = (e.pageX - offset.left);
  	var y = (e.pageY - offset.top);
  	if (!gcode_coordinate_offset) {
  	  if(!e.shiftKey) {
        coords_text = assemble_info_text(x,y);
        if (e.altKey &&isDragging) {
            assemble_and_send_gcode(x,y);
        }
      } else {
        coords_text = 'set offset to (' + 2*x + ', '+ 2*y + ')';
      }
    } else {
      if(e.shiftKey) {
        coords_text = 'set offset to (' + x + ', '+ y + ')'
      } else {
        var pos = $("#offset_area").position()
        if ((x < pos.left) || (y < pos.top)) {           
          coords_text = 'click to reset offset';
        } else {
          coords_text = '';
        }
      }
    }
    $('#coordinates_info').text(coords_text);
  });
  
  
  $("#offset_area").click(function(e) { 
    if(!e.shiftKey) {
    	var offset = $(this).offset();
    	var x = (e.pageX - offset.left);
    	var y = (e.pageY - offset.top);     
      assemble_and_send_gcode(x,y);
      return false
    }
  });

  $("#offset_area").hover(
    function () {
    },
    function () {
  		$('#offset_info').text('');		
    }
  );
  
  $("#offset_area").mousemove(function (e) {
    if(!e.shiftKey) {
    	var offset = $(this).offset();
    	var x = (e.pageX - offset.left);
    	var y = (e.pageY - offset.top);
      $('#offset_info').text(assemble_info_text(x,y));
    } else {
      $('#offset_info').text('');
    }
  });
  
  // function moveto (x, y) {
  //  $('#y_cart').animate({  
  //    top: y - 8.5 - 6
  //  });   
  //  
  //  $('#x_cart').animate({  
  //    left: x - 6,  
  //    top: y - 6 
  //  });
  // };
  
  //// motion parameters
  $( "#intensity_field" ).val('0');
  
  $("#seek_btn").click(function(e) {
    $( "#intensity_field" ).hide();
    $( "#intensity_field_disabled" ).show();
  });  
  $("#feed_btn").click(function(e) {
    $( "#intensity_field_disabled" ).hide();
    $( "#intensity_field" ).show();
  });   
  
  $("#feedrate_btn_slow").click(function(e) {
    $( "#feedrate_field" ).val("600");
  });  
  $("#feedrate_btn_medium").click(function(e) {
    $( "#feedrate_field" ).val("2000");
  });  
  $("#feedrate_btn_fast").click(function(e) {
    $( "#feedrate_field" ).val("16000");
  });  
  $("#feedrate_field").focus(function(e) {
    $("#feedrate_btn_slow").removeClass('active');
    $("#feedrate_btn_medium").removeClass('active');
    $("#feedrate_btn_fast").removeClass('active');
  });
  
  if ($("#feedrate_field" ).val() != 16000) {
    $("#feedrate_btn_slow").removeClass('active');
    $("#feedrate_btn_medium").removeClass('active');
    $("#feedrate_btn_fast").removeClass('active');    
  }
  
  //// jog buttons
  $("#jog_up_btn").click(function(e) {
    var gcode = 'G91\nG0Y-10F6000\nG90\n';
    send_gcode(gcode, "Moving Up ...", "Serial not connected.")	
  });   
  $("#jog_left_btn").click(function(e) {
    var gcode = 'G91\nG0X-10F6000\nG90\n';
    send_gcode(gcode, "Moving Left ...", "Serial not connected.")	
  });   
  $("#jog_right_btn").click(function(e) {
    var gcode = 'G91\nG0X10F6000\nG90\n';
    send_gcode(gcode, "Moving Right ...", "Serial not connected.")	
  });
  $("#jog_down_btn").click(function(e) {
    var gcode = 'G91\nG0Y10F6000\nG90\n';
    send_gcode(gcode, "Moving Down ...", "Serial not connected.")	
  });
      
});  // ready
