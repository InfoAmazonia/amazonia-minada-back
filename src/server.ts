import 'reflect-metadata'
import cors from 'cors'
import express from 'express'
import 'express-async-errors'
import { InitLogger, InitRequestLogger } from './utils/logging'

InitLogger();

// -

import { errorHandler } from './errors'
import { router } from './routes'

import './database'
import './shared/container'

const app = express()

app.use(cors())
app.use(express.json())
app.use(express.urlencoded({ extended: true }))
app.use(InitRequestLogger());
app.use('/api', router)
app.use(errorHandler)

app.listen(5000, () => console.log('Server is running!'))
