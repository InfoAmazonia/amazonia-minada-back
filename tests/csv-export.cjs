// Run after npm run build: node tests/csv-export.cjs
require('reflect-metadata')
const assert = require('assert').strict
const { container } = require('tsyringe')
const { ListInvasionsController } = require('../dist/services/listInvasions/ListInvasionsController')

const header = ['key', 'id', 'company', 'process', 'area', 'year', 'state',
  'miningProcess', 'territory', 'type', 'substance', 'use', 'lastEvent',
  'miningProcessType', 'reservePhase', 'reserveEthnicity']
  .map(field => `"${field}"`).join(',')

async function exportSelection(values) {
  const resolve = container.resolve
  container.resolve = () => ({ execute: async () => values })
  const response = {
    attachment(name) { assert.equal(name, 'invasions.csv'); return this },
    status(code) { assert.equal(code, 200); return this },
    send(csv) { this.csv = csv; return this },
  }
  try {
    await new ListInvasionsController().handle(
      { body: { filters: {} }, query: { output: 'csv' } }, response
    )
    return response.csv
  } finally {
    container.resolve = resolve
  }
}

async function main() {
  assert.equal(await exportSelection([]), header)
  const csv = await exportSelection([
    { id: 'sample', company: 'Amazônia, "Pesquisa"\nSegunda linha', area: 12.5 },
  ])
  assert.ok(csv.startsWith(header + '\n'))
  assert.ok(csv.includes('"Amazônia, ""Pesquisa""\nSegunda linha"'))
  assert.ok(csv.includes(',12.5,'))
  console.log('CSV regression tests passed: empty selection and escaped values')
}

main().catch(error => { console.error(error); process.exitCode = 1 })
