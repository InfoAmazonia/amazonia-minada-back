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

// Set UTF-8 encoding for all responses
app.use((req, res, next) => {
  res.setHeader('Content-Type', 'application/json; charset=utf-8')
  next()
})

app.use(
  cors({
    origin: (origin, callback) => {
      // Allow requests with no origin (like mobile apps, curl, etc.)
      if (!origin) return callback(null, true);
      // Allow all subdomains of infoamazonia.org
      const regex = /^https?:\/\/(.*\.)?infoamazonia\.org(:\d+)?$/i;
      if (regex.test(origin)) {
        return callback(null, true);
      }
      // Otherwise, block it
      callback(new Error('Not allowed by CORS'));
    },
    credentials: true,
  })
)
app.use(express.json({ limit: '50mb' }))
app.use(express.urlencoded({ extended: true, limit: '50mb' }))
app.use(InitRequestLogger());
app.use('/api', router)
app.use(errorHandler)

app.listen(5000, () => console.log('Server is running!'))
