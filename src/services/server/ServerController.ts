import { Request, Response } from 'express'
import { getLogger } from '../../utils/logging'
import { Invasion } from '../../database/models/Invasion';

export class ServerController {
    async Healthpoint(request: Request, response: Response) {
        try {
            const secretKey: string = request.query['secret'] as string;
            if (secretKey == (process.env.HEALTH_SECRET || '0')) {
                // - Test a Simple Query in the Database
                const invasionQuery = await Invasion.findOne({}).select({"_id": 0});
                    
                // -
                response.json({
                    "state": "Okay"
                });
                response.status(200);
            } else {
                response.status(403);
            }
        } catch (error) {
            getLogger().error("Fail in Healthpoint!");
            getLogger().error(error);
            response.status(500);
        }

        response.end();
    }
}