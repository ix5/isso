// https://stackoverflow.com/questions/41098009/mocking-document-in-jest
var document_mock = {
    getElementsByTagName: () => {
        return [{
            className: 'welcome',
            attributes: [
                { name: "data-isso-css", value: true },
                { name: "data-isso-css-url", value: null },
                { name: "data-isso-lang", value: "" },
                { name: "data-isso-default-lang", value: "en" },
                { name: "data-isso-reply-to-self", value: false },
                { name: "data-isso-require-email", value: false },
                { name: "data-isso-require-author", value: false },
                { name: "data-isso-reply-notifications", value: false },
                { name: "data-isso-max-comments-top", value: "inf" },
                { name: "data-isso-max-comments-nested", value: 5 },
                { name: "data-isso-reveal-on-click", value: 5 },
                { name: "data-isso-gravatar", value: false },
                { name: "data-isso-avatar", value: true },
            ],
        }]
    },
};

global.document = document_mock;
global.navigator = { languages: null };

const config = require("app/config");


test("Client configuration", () => {
  let expected_langs = ["en", "en"];
  expect(config["langs"]).toStrictEqual(expected_langs);
});
