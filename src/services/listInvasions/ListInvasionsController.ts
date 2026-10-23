import { Request, Response } from 'express'
import json2csv from 'json2csv'
import { container } from 'tsyringe'
import * as yup from 'yup'

import { paginate } from '../../utils/pagination'
import { filterSchema } from '../../yup/schemas/filterSchema'
import { ListInvasionsService } from './ListInvasionsService'

// Keep the CSV schema stable, including when the selection has no rows.
const csvFields = [
  'key',
  'id',
  'company',
  'process',
  'area',
  'year',
  'state',
  'miningProcess',
  'territory',
  'type',
  'substance',
  'use',
  'lastEvent',
  'miningProcessType',
  'reservePhase',
  'reserveEthnicity',
]

class ListInvasionsController {
  async handle(request: Request, response: Response): Promise<Response> {
    const { filters, enableUnity, enableReserve } = request.body
    const { page, pageSize, output } = request.query

    const schema = yup.object().shape({
      filters: filterSchema,
      enableUnity: yup.boolean(),
      enableReserve: yup.boolean(),
    })

    await schema.validate(request.body, { abortEarly: false })

    const listInvasionsService = container.resolve(ListInvasionsService)

    const invasions = await listInvasionsService.execute(
      filters,
      enableUnity,
      enableReserve
    )

    if (output === 'csv') {
      const data = json2csv.parse(invasions, { fields: csvFields })
      return response.attachment('invasions.csv').status(200).send(data)
    }

    const pageNumber = Number(page) || 1
    const pageSizeNumber = Number(pageSize) || 10

    const paginatedInvasions = paginate(invasions, pageNumber, pageSizeNumber)

    return response.json(paginatedInvasions)
  }
}

export { ListInvasionsController }
