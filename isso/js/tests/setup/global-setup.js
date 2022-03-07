/* Currently unused */

const { setup: setupDevServer } = require('jest-dev-server')

module.exports = async function globalSetup() {
  await setupDevServer({
    command: `.venv/bin/isso -c share/isso-dev.conf`,
    //launchTimeout: 50000,
    launchTimeout: 5000,
    port: 8080,
  })
  // Your global setup
}
