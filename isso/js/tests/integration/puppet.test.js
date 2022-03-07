/* Integration testing - WIP */

// Not currently needed:
//import 'expect-puppeteer';
//const pup = require("expect-puppeteer");

describe('Isso embed on /demo', () => {
  beforeAll(async () => {
    //await page.goto('https://google.com')
    await page.goto('http://localhost:8080/demo')
  })

  it('should display "Isso Demo" text on page', async () => {
    await expect(page).toMatch('Isso Demo');
  });
  it("should type into comment box", async () => {
    await page.type('.textarea', 'MyComment', { delay: 100 });
    await page.click('input[type=submit]');
    //await page.waitForNavigation(100);
    await expect(page).toMatch('Isso Demo');
  });
})
