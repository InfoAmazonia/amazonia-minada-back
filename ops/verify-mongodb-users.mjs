// Non-destructive audit. Supply URIs through a private environment file, never CLI arguments.
import assert from 'node:assert/strict';
import mongodb from 'mongodb';
const { MongoClient } = mongodb;
const checks = [];
async function deny(label, operation) {
    await assert.rejects(operation, error => error.code === 13, label);
    checks.push(label);
}
for (const [kind, variable, user] of [
    ['backend', 'MINADA_BACKEND_URI', 'minada_backend'],
    ['importer', 'MINADA_IMPORTER_URI', 'minada_importer']
]) {
    if (!process.env[variable]) throw new Error(`Missing private environment variable ${variable}`);
    const client = new MongoClient(process.env[variable]);
    await client.connect();
    try {
        const application = client.db('icfj');
        const identity = await application.command({ connectionStatus: 1, showPrivileges: true });
        assert.deepEqual(identity.authInfo.authenticatedUsers, [{ user, db: 'icfj' }]);
        assert.ok(identity.authInfo.authenticatedUserPrivileges.every(p => p.resource.db === 'icfj'));
        for (const collection of ['licenses', 'unities', 'reserves', 'invasions', 'reserveinvasions']) {
            await application.collection(collection).findOne({}, { projection: { _id: 1 } });
        }
        await deny(`${kind}: administrative data`, () => client.db('admin').collection('system.users').findOne());
        await deny(`${kind}: unrelated database`, () => client.db('unrelated').collection('probe').findOne());
        if (kind === 'backend') {
            // The predicate can never match; even a misconfigured account cannot change a document.
            await deny('backend: writes', () => application.collection('invasions').updateOne(
                { $expr: { $eq: [1, 0] } }, { $set: { permissionAudit: true } }, { upsert: false }
            ));
            await deny('backend: publication queues', () => application.collection('invasionpt_queueitems').findOne());
        }
    } finally {
        await client.close();
    }
}
console.log(JSON.stringify({ applicationReads: true, denied: checks }));
