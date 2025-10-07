import { Router } from 'express'

import { GetInvasionsShapeController } from '../services/getInvasionsShape/GetInvasionsShapeController'
import { GetRequirementsPhaseController } from '../services/getRequirementsPhase/GetRequirementsPhaseController'
import { GetReservesPhaseController } from '../services/getReservesPhase/GetReservesPhaseController'
import { GetStatisticsController } from '../services/getStatistics/GetStatisticsController'
import { GetUsesController } from '../services/getUses/GetUsesController'
import { GetYearsController } from '../services/getYears/GetYearsController'
import { InvasionRankingController } from '../services/invasionRanking/InvasionRankingController'
import { ListInvasionsController } from '../services/listInvasions/ListInvasionsController'
import { SearchController } from '../services/search/SearchController'
import { ServerController } from '../services/server/ServerController'

const router = Router()

const searchController = new SearchController()
const listInvasionsController = new ListInvasionsController()
const invasionRankingController = new InvasionRankingController()
const getStatisticsController = new GetStatisticsController()
const getReservesPhaseController = new GetReservesPhaseController()
const getRequirementsPhaseController = new GetRequirementsPhaseController()
const getInvasionsShapeController = new GetInvasionsShapeController()
const getYearsController = new GetYearsController()
const getUsesController = new GetUsesController()
const serverController = new ServerController()

router.get('/search/:searchTerm', searchController.handle)
router.post('/invasions', listInvasionsController.handle)
router.post(
  '/invasions/ranking/:propertyType/:dataType',
  invasionRankingController.handle
)
router.get('/invasions/phase', getRequirementsPhaseController.handle)
router.get('/invasions/years', getYearsController.handle)
router.post('/invasions/shape', getInvasionsShapeController.handle)
router.get('/invasions/uses', getUsesController.handle)
router.post('/statistics', getStatisticsController.handle)
router.get('/reserves/phase', getReservesPhaseController.handle)
router.get('/server/healthz', serverController.Healthpoint);

export { router }
