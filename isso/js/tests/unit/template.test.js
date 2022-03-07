/* TODO not working because jest and pug-loader somehow don't want to work
 * together */

/* XXX Disable for now
const template = require("app/template");

test("Template functions", () => {
  let _data = {
    "author": "foo",
    "email": "foo@foo.bar",
    "website": "https://foo.bar",
    "preview": "",
  };
  expect(template.render("postbox", _data)).toStrictEqual("");
});

*/
