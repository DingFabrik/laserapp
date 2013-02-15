

// create new canvas like this:
// var canvas = new Canvas('#canvas_id');

function Canvas(canvas_selector) {
  this.cx = $(canvas_selector)[0].getContext("2d");
  this.width = $(canvas_selector).width();
  this.height = $(canvas_selector).height();
  
  this.bFill = true;
  this.vFill = "#ffffff";
  this.cx.fillStyle = this.vFill;
  
  this.bStroke = true;
  this.vStroke = "#000000";
  this.cx.strokeStyle = this.vStroke;
}

Canvas.prototype.fill = function (hexcolorval) {
  this.bFill = true;
  this.vFill = hexcolorval;
  this.cx.fillStyle = this.vFill;  
}
Canvas.prototype.noFill = function () {
  this.bFill = false;
}

Canvas.prototype.stroke = function (hexcolorval) {
  this.bStroke = true;
  this.vStroke = hexcolorval;
  this.cx.strokeStyle = this.vStroke;  
}
Canvas.prototype.noStroke = function () {
  this.bStroke = false;
}

Canvas.prototype.line = function (x1, y1, x2, y2) {
  this.cx.beginPath();
  this.cx.moveTo(x1, y1);
  this.cx.lineTo(x2, y2);
  if (this.bFill) { this.cx.fill(); }
  if (this.bStroke) { this.cx.stroke(); }
  this.cx.closePath();
}

Canvas.prototype.rect = function (x, y, w, h) {
  this.cx.beginPath();
  this.cx.rect(x, y, w, h);
  if (this.bFill) { this.cx.fill(); }
  if (this.bStroke) { this.cx.stroke(); }
  this.cx.closePath();
}

Canvas.prototype.circle = function (x, y, r) {
  this.cx.beginPath();
  this.cx.arc(x, y, r, 0, Math.PI*2, true);
  if (this.bFill) { this.cx.fill(); }
  if (this.bStroke) { this.cx.stroke(); }
  this.cx.closePath();
};

Canvas.prototype.arc = function (x, y, r, startang, endang, ccw) {
  this.cx.beginPath();
  this.cx.arc(x, y, r, startang, endang, ccw);
  if (this.bFill) { this.cx.fill(); }
  if (this.bStroke) { this.cx.stroke(); }
  this.cx.closePath();
};
// there is also a cx.arcTo(x1, y1, x2, y2, radius)

Canvas.prototype.background = function (color) {
  this.noStroke();
  this.fill(color);
  this.rect(0, 0, this.width, this.height);
}

Canvas.prototype.clear = function () {
  this.cx.clearRect(0, 0, this.width, this.height);
}

Canvas.prototype.draw = function () {
  this.clear();
  this.circle(x, y, 10);

  x += 2;
  y += 4;
}


