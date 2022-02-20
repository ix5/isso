const comment_html = require('./comment_tmpl').html;
const comment_loader = require('./comment-loader_tmpl').html;
const postbox = require('./postbox_tmpl').html;

var i18n = function (text) { return text; };
var pluralize = function (trans, count=null) { return count ? 'plural: ' + trans : trans; };
var humanize = function (text) { return text; };
var datetime = function (text) { return text; };
var conf = { gravatar: true, avatar: false};
var comment = {
    created: 2018,
    id: 1,
    gravatar_image: 'https://image.svg',
    website: 'https://web.site',
    author: 'Author',
    email: 'email@email.com',
    mode: 2,
    text: 'Lorem ipsum, <code>html</code>, my comment.',
    hidden_replies: 2,
};

console.log(comment_html(i18n, comment, conf, datetime, humanize, pluralize));
console.log(comment_loader(comment, pluralize));
console.log(postbox(i18n, comment.author, comment.email, comment.website));
