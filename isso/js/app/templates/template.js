"use strict";

const tmpl_postbox = require("./postbox_tmpl").html;
const tmpl_comment = require("./comment_tmpl").html;
const tmpl_comment_loader = require("./comment-loader_tmpl").html;

var globals = {},
    templates = {};

var load_tmpl = function(name, tmpl) {
    templates[name] = tmpl;
};

load_tmpl("postbox", tmpl_postbox);
load_tmpl("comment", tmpl_comment);
load_tmpl("comment-loader", tmpl_comment_loader);

var set = function(name, value) {
    globals[name] = value;
};

set("bool", function(arg) { return arg ? true : false; });
set("humanize", function(date) {
    if (typeof date !== "object") {
        date = new Date(parseInt(date, 10) * 1000);
    }

    return date.toString();
});
set("datetime", function(date) {
    if (typeof date !== "object") {
        date = new Date(parseInt(date, 10) * 1000);
    }
    return [
        date.getUTCFullYear(),
        utils.pad(date.getUTCMonth(), 2),
        utils.pad(date.getUTCDay(), 2)
    ].join("-") + "T" + [
        utils.pad(date.getUTCHours(), 2),
        utils.pad(date.getUTCMinutes(), 2),
        utils.pad(date.getUTCSeconds(), 2)
    ].join(":") + "Z";
});
var i18n = function (text) { return 'i18n: ' + text; };
var pluralize = function (trans, count=null) { return count ? 'plural: ' + trans : 'sing: ' + trans; };
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
var svg = function () { return '<svg width="16" height="16" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" fill="gray"> <g> <path d="M 24.773,13.701c-0.651,0.669-7.512,7.205-7.512,7.205C 16.912,21.262, 16.456,21.44, 16,21.44c-0.458,0-0.914-0.178-1.261-0.534 c0,0-6.861-6.536-7.514-7.205c-0.651-0.669-0.696-1.87,0-2.586c 0.698-0.714, 1.669-0.77, 2.522,0L 16,17.112l 6.251-5.995 c 0.854-0.77, 1.827-0.714, 2.522,0C 25.47,11.83, 25.427,13.034, 24.773,13.701z"> </path> </g> </svg>'};

set("conf", conf);
set("i18n", i18n);
set("pluralize", pluralize);
set("svg", svg);


var render = function(name, locals) {
    var rv, t = templates[name];
    if (! t) {
        throw new Error("Template not found: '" + name + "'");
    }
    locals = locals || {};
    var keys = [];
    for (var key in locals) {
        if (locals.hasOwnProperty(key) && !globals.hasOwnProperty(key)) {
            keys.push(key);
            globals[key] = locals[key];
        }
    }
    //console.log("Globals: ", {...globals});
    //var html = function(i18n, ...rest) { return `${i18n('foo')}`};
    //console.log("i18n: ", `${globals['i18n']('foo')}`);
    //console.log("i18n: ", html({...globals}));
    rv = templates[name](globals);
    //for (var i = 0; i < keys.length; i++) {
    //    delete globals[keys[i]];
    //}
    return rv;
};

console.log(render('postbox', {'comment': {'name': 'foo'}}));
//render('postbox', {'comment': {'name': 'foo'}});
