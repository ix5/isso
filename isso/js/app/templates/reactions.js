var html = function (globals) {
  var count = globals.count;
  var i18n = globals.i18n;
  var svg = globals.svg;
  return "" +
"<div id='isso-reactions'>"
+ "<a id='isso-thanks' href='#' title='Click me!'>"
+ svg['heart'] + "</a>"
+ "<span id='isso-thanks-counter'>" + count + "</span>"
+ "<span> " + i18n('reactions-thanks') + "</span>"
+ "</div>"
};
module.exports = html;
