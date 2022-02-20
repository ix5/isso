const pug = require('pug');

//var tmpl = pug.renderFile('isso/js/app/templates/postbox.pug', {
var tmpl = pug.renderFile('isso/js/app/templates/comment.pug', {
  i18n: (text) => 'i18n(' + text + ')',
  author: 'Author',
  email: 'email@email.com',
  website: 'https://web.site',
  pretty: true,
});
console.log(tmpl);
